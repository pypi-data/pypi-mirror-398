# seeder/registry.py

from __future__ import annotations

import logging
import re
from collections import defaultdict
from importlib import import_module
from typing import Any, Callable, Iterable, Mapping, MutableMapping, Set

from django.db import models

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


class SeederRegistry:
    """
    Central registry that keeps track of additional configuration for the
    seeding process. Users can populate it programmatically or via
    Django settings (DJSEED).
    """

    def __init__(self) -> None:
        self._extra_required_fields: MutableMapping[str, Set[str]] = (
            defaultdict(set)
        )
        self._ignored_field_names: MutableMapping[str, Set[str]] = defaultdict(
            set
        )
        self._generic_foreign_key_models: MutableMapping[
            str, MutableMapping[str, Set[str]]
        ] = defaultdict(lambda: defaultdict(set))
        self._model_priorities: MutableMapping[str, int] = {}
        self._email_domain: str | None = None
        self._default_password: str | None = None
        self._custom_field_generators: list[
            tuple[Callable[[models.Field], bool], Callable[..., Any]]
        ] = []
        self._custom_type_generators: list[
            tuple[type[models.Field], Callable[..., Any]]
        ] = []
        self._settings_loaded = False
        self._logger = logging.getLogger(__name__)

    # ------------------------------------------------------------------ #
    # Registration helpers
    # ------------------------------------------------------------------ #
    def register_extra_required_fields(
        self, model_label: str, fields: Iterable[str]
    ) -> None:
        self._extra_required_fields[model_label].update(fields)

    def register_ignored_field_names(
        self, model_label: str, fields: Iterable[str]
    ) -> None:
        self._ignored_field_names[model_label].update(fields)

    def register_generic_foreign_key_models(
        self, model_label: str, mapping: Mapping[str, Iterable[str]]
    ) -> None:
        target_map = self._generic_foreign_key_models[model_label]
        for field_name, model_labels in mapping.items():
            target_map[field_name].update(model_labels)

    def register_model_priorities(self, priorities: Mapping[str, int]) -> None:
        """
        Register ordering priorities for models. Lower numbers are processed
        first. Keys can be exact labels (app_label.ModelName), app labels,
        or plain model names.
        """
        self._model_priorities.update(priorities)

    def register_email_domain(self, domain: str) -> None:
        self._email_domain = domain

    def register_default_password(self, password: str) -> None:
        self._default_password = password

    def register_field_generator(
        self,
        match: str | re.Pattern[str] | Callable[[models.Field], bool],
        generator: str | Mapping[str, Any] | Callable[..., Any],
    ) -> None:
        """
        Register a generator that is selected by field name. The `match`
        argument can be:
        - a substring (case-insensitive) matched against the field name
        - a compiled regex matched against the field name
        - a callable that receives the field and returns True/False

        Generators can be callables or references to Faker providers
        (e.g., "user_name") or callables via dotted-path strings.
        """
        matcher = self._normalize_matcher(match)
        generator_fn = self._normalize_generator(generator)
        self._custom_field_generators.append((matcher, generator_fn))

    def register_field_type_generator(
        self,
        field_type: type[models.Field],
        generator: str | Mapping[str, Any] | Callable[..., Any],
    ) -> None:
        generator_fn = self._normalize_generator(generator)
        self._custom_type_generators.append((field_type, generator_fn))

    def get_field_generator(
        self, field: models.Field
    ) -> Callable[..., Any] | None:
        for matcher, generator in self._custom_field_generators:
            try:
                if matcher(field):
                    return generator
            except Exception:
                continue

        for field_type, generator in self._custom_type_generators:
            if isinstance(field, field_type):
                return generator

        return None

    # ------------------------------------------------------------------ #
    # Access helpers
    # ------------------------------------------------------------------ #
    def get_extra_required_fields(self, model_label: str) -> Set[str]:
        all_fields = set(self._extra_required_fields.get("*", set()))
        all_fields.update(self._extra_required_fields.get(model_label, set()))
        return all_fields

    def get_ignored_field_names(self, model_label: str | None) -> Set[str]:
        if model_label is None:
            return set(self._ignored_field_names.get("*", set()))
        ignored = set(self._ignored_field_names.get("*", set()))
        ignored.update(self._ignored_field_names.get(model_label, set()))
        return ignored

    def get_generic_foreign_key_models(
        self, model_label: str
    ) -> Mapping[str, Set[str]]:
        resolved: MutableMapping[str, Set[str]] = defaultdict(set)
        for label in ("*", model_label):
            field_map = self._generic_foreign_key_models.get(label, {})
            for field_name, targets in field_map.items():
                resolved[field_name].update(targets)
        return {field: set(models) for field, models in resolved.items()}

    def get_model_priorities(self) -> Mapping[str, int]:
        return dict(self._model_priorities)

    def get_email_domain(self) -> str | None:
        return self._email_domain

    def get_default_password(self) -> str | None:
        return self._default_password

    # ------------------------------------------------------------------ #
    # Settings-based configuration
    # ------------------------------------------------------------------ #
    def configure_from_settings(self) -> None:
        if self._settings_loaded:
            return
        try:
            if not settings.configured:  # type: ignore[attr-defined]
                return
        except ImproperlyConfigured:
            return

        config: Mapping[str, Mapping[str, Iterable[str]]] | None = getattr(
            settings, "DJSEED", None
        )
        if config:
            extra_required = config.get("extra_required_fields", {})
            for label, fields in extra_required.items():
                self.register_extra_required_fields(label, fields)

            ignored_fields = config.get("ignored_field_names", {})
            for label, fields in ignored_fields.items():
                self.register_ignored_field_names(label, fields)

            gfk_mappings = config.get("generic_foreign_keys", {})
            for label, mapping in gfk_mappings.items():
                self.register_generic_foreign_key_models(label, mapping)

            model_priorities = config.get("model_priorities", {})
            if model_priorities:
                self.register_model_priorities(model_priorities)

            email_domain = config.get("email_domain")
            if email_domain:
                self.register_email_domain(str(email_domain))

            default_password = config.get("default_password")
            if default_password:
                self.register_default_password(str(default_password))

        self._settings_loaded = True

    def reset_settings_cache(self) -> None:
        self._settings_loaded = False

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    def _normalize_matcher(
        self, match: str | re.Pattern[str] | Callable[[models.Field], bool]
    ) -> Callable[[models.Field], bool]:
        if callable(match):
            return match
        if isinstance(match, re.Pattern):
            return lambda field: bool(match.search(field.name))
        lowered = match.lower()

        # Support "app_label.model.field" exact matching for precision
        if "." in lowered:
            *model_parts, field_name = lowered.split(".")
            model_label = ".".join(model_parts)

            def _matches(field: models.Field) -> bool:
                model = getattr(field, "model", None)
                label = (
                    getattr(getattr(model, "_meta", None), "label_lower", "")
                    if model
                    else ""
                )
                return (
                    field.name.lower() == field_name
                    and label == model_label
                )

            return _matches

        return lambda field: lowered in field.name.lower()

    def _import_field_type(
        self, path: str
    ) -> type[models.Field] | None:  # pragma: no cover - best effort
        try:
            module_path, class_name = path.rsplit(".", 1)
            module = import_module(module_path)
            field_type = getattr(module, class_name)
            if not issubclass(field_type, models.Field):
                raise TypeError(
                    f"{path!r} is not a Django Field subclass."
                )
            return field_type
        except Exception as exc:
            self._logger.warning(
                f"⚠️ Could not import field type {path!r}: {exc}"
            )
            return None

    def _normalize_generator(
        self, generator: str | Mapping[str, Any] | Callable[..., Any]
    ) -> Callable[..., Any]:
        if callable(generator):
            return generator

        if isinstance(generator, Mapping):
            provider = generator.get("faker") or generator.get("provider")
            args = generator.get("args", []) or []
            kwargs = generator.get("kwargs", {}) or {}
            callable_path = generator.get("callable")
            if callable_path:
                func = (
                    callable_path
                    if callable(callable_path)
                    else self._import_callable(str(callable_path))
                )
                return self._wrap_callable(func, args, kwargs)
            if provider:
                return self._wrap_faker_provider(
                    str(provider), list(args), dict(kwargs)
                )

        if isinstance(generator, str):
            if "." in generator:
                func = self._import_callable(generator)
                return self._wrap_callable(func, [], {})
            return self._wrap_faker_provider(generator, [], {})

        raise TypeError("Invalid generator definition provided.")

    def _import_callable(
        self, path: str
    ) -> Callable[..., Any]:  # pragma: no cover - defensive
        module_path, func_name = path.rsplit(".", 1)
        module = import_module(module_path)
        return getattr(module, func_name)

    def _wrap_callable(
        self,
        func: Callable[..., Any],
        args: Iterable[Any],
        kwargs: Mapping[str, Any],
    ) -> Callable[..., Any]:
        def _wrapped(faker, field=None):
            return func(faker=faker, field=field, *args, **kwargs)

        return _wrapped

    def _wrap_faker_provider(
        self, provider: str, args: Iterable[Any], kwargs: Mapping[str, Any]
    ) -> Callable[..., Any]:
        def _wrapped(faker, field=None):
            attr = getattr(faker, provider)
            return attr(*args, **kwargs) if callable(attr) else attr

        return _wrapped


registry = SeederRegistry()


__all__ = ["registry", "SeederRegistry"]
