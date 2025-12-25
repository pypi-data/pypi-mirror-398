# seeder/builders.py

import random
import uuid
from collections import deque
from types import SimpleNamespace

from django.apps import apps
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.utils import OperationalError, ProgrammingError

from .generators import generate_value
from .logging import get_logger
from .registry import registry

logger = get_logger(__name__)


def has_generic_foreign_key(model_class):
    for field in model_class._meta.private_fields:
        if isinstance(field, GenericForeignKey):
            return True
    return False


def _get_generic_foreign_key_fields(model_class):
    return [
        field
        for field in model_class._meta.private_fields
        if isinstance(field, GenericForeignKey)
    ]


def _get_generic_foreign_key_component_names(model_class):
    names = set()
    for field in _get_generic_foreign_key_fields(model_class):
        names.add(field.ct_field)
        names.add(field.fk_field)
    return names


def _resolve_generic_target_models(model_class, targets_by_field):
    resolved = {}
    for field_name, model_labels in targets_by_field.items():
        resolved_models = []
        for label in model_labels:
            try:
                resolved_models.append(apps.get_model(label))
            except LookupError:
                logger.warning(
                    f"⚠️ Unknown model '{label}' configured for {model_class.__name__}.{field_name}"
                )
        if resolved_models:
            resolved[field_name] = resolved_models
    return resolved


def get_generic_foreign_key_targets(model_class):
    registry.configure_from_settings()
    label = model_class._meta.label_lower
    targets_by_field = registry.get_generic_foreign_key_models(label)
    return _resolve_generic_target_models(model_class, targets_by_field)


def get_ignored_field_names(model_class=None):
    registry.configure_from_settings()
    label = None if model_class is None else model_class._meta.label_lower
    return registry.get_ignored_field_names(label)


def get_extra_required_fields_for_model(model_class):
    registry.configure_from_settings()
    label = model_class._meta.label_lower
    required = set(registry.get_extra_required_fields(label))

    for field in model_class._meta.fields:
        if (
            isinstance(field, (models.ForeignKey, models.OneToOneField))
            and not field.null
            and not field.blank
            and field.name not in get_ignored_field_names(model_class)
        ):
            required.add(field.name)

    return required


def _should_skip_field(field, model_class=None):
    if field.name == "id":
        return False
    if model_class and field.name in _get_generic_foreign_key_component_names(
        model_class
    ):
        return True
    if field.name in get_ignored_field_names(model_class):
        return True
    return False


def _handle_field_assignment(field, value, fields_data):
    if isinstance(field, (models.ForeignKey, models.OneToOneField)):
        fields_data[field.name] = value.pk
    else:
        fields_data[field.name] = value


def _safe_random_instance(model):
    try:
        return model.objects.order_by("?").first()
    except (OperationalError, ProgrammingError):
        return None


def _fill_auto_now_fields(model_class, fields_data):
    for field in model_class._meta.fields:
        if (
            isinstance(field, models.DateTimeField)
            and (
                getattr(field, "auto_now_add", False)
                or getattr(field, "auto_now", False)
            )
            and field.name not in fields_data
        ):
            value = generate_value(field)
            _handle_field_assignment(field, value, fields_data)


def _select_generic_related_object(allowed_models, context):
    candidates = list(allowed_models)
    random.shuffle(candidates)
    for target_model in candidates:
        fixtures = (context or {}).get(target_model, [])
        valid_fixtures = [entry for entry in fixtures if entry.get("pk")]
        logger.info(
            f"Selecting GFK target for {target_model.__name__}: {len(valid_fixtures)} valid fixtures found"
        )
        if valid_fixtures:
            selected = random.choice(valid_fixtures)
            logger.info(
                f"Selected GFK target: {target_model.__name__} (pk={selected['pk']})"
            )
            return target_model, selected["pk"]
        instance = _safe_random_instance(target_model)
        if instance:
            return target_model, instance.pk
    return None, None


def _assign_pk_if_needed(model_class, pk_value):
    if not pk_value:
        for field in model_class._meta.fields:
            if getattr(field, "primary_key", False) and isinstance(
                field, models.UUIDField
            ):
                pk_value = uuid.uuid4()
                break
    return pk_value


def _normalize_unique_value(value):
    """Normalize values so uniqueness checks treat UUIDs consistently."""
    if isinstance(value, models.Model):
        value = value.pk
    if isinstance(value, uuid.UUID):
        return str(value)
    return value


def _condition_applies(condition, fields_data):
    """
    Best-effort evaluation of a UniqueConstraint condition (Q object) against
    the already-generated field values. Returns True when the condition is
    satisfied, False when definitively not satisfied, and None when it cannot
    be evaluated (e.g., missing values or unsupported lookups).
    """

    if condition is None:
        return True

    def eval_q(node):
        results = []
        for child in node.children:
            if isinstance(child, models.Q):
                results.append(eval_q(child))
                continue

            lookup, expected = child
            if "__" in lookup:
                field_name, lookup_type = lookup.split("__", 1)
            else:
                field_name, lookup_type = lookup, "exact"

            if field_name not in fields_data:
                results.append(None)
                continue

            actual = fields_data.get(field_name)
            if lookup_type == "exact":
                results.append(actual == expected)
            elif lookup_type == "isnull":
                results.append((actual is None) == bool(expected))
            else:
                results.append(None)

        if not results:
            return None

        known = [res for res in results if res is not None]
        if node.connector == models.Q.OR:
            if True in known:
                verdict = True
            elif len(known) == len(results):
                verdict = False
            else:
                verdict = None
        else:  # AND
            if False in known:
                verdict = False
            elif len(known) == len(results):
                verdict = True
            else:
                verdict = None

        if node.negated and verdict is not None:
            verdict = not verdict
        return verdict

    return eval_q(condition)


def _build_unique_together_registry(model_class):
    unique_together_registry = []
    for unique in model_class._meta.unique_together:
        unique_together_registry.append(
            {"fields": unique, "used": set(), "condition": None}
        )
    for constraint in model_class._meta.constraints:
        if isinstance(constraint, models.UniqueConstraint):
            field_tuple = tuple(constraint.fields)
            normalized = tuple(sorted(field_tuple))
            # Avoid duplicating mirrored constraints (e.g., user1/user2 vs user2/user1)
            if any(
                sorted(entry["fields"]) == list(normalized)
                for entry in unique_together_registry
            ):
                continue
            unique_together_registry.append(
                {
                    "fields": field_tuple,
                    "used": set(),
                    "condition": getattr(constraint, "condition", None),
                }
            )
    return unique_together_registry


def _build_unique_field_registry(model_class):
    unique_field_registry = {}
    for field in model_class._meta.fields:
        if field.unique:
            unique_field_registry[field.name] = set()
    return unique_field_registry


def _should_skip_instance(
    fields_data, unique_field_registry, unique_together_registry
):
    for field_name, used_values in unique_field_registry.items():
        field_value = _normalize_unique_value(fields_data.get(field_name))
        if field_value in used_values:
            return True
    for combo in unique_together_registry:
        field_names = combo["fields"]
        condition = combo.get("condition")
        applies = _condition_applies(condition, fields_data)
        if applies is False:
            continue
        key = tuple(
            _normalize_unique_value(fields_data.get(fname))
            for fname in field_names
        )
        if None in key:
            continue
        if applies and key in combo["used"]:
            return True
    return False


def _register_unique_values(
    fields_data, unique_field_registry, unique_together_registry
):
    for field_name in unique_field_registry:
        value = _normalize_unique_value(fields_data.get(field_name))
        if value is not None:
            unique_field_registry[field_name].add(value)
    for combo in unique_together_registry:
        condition = combo.get("condition")
        applies = _condition_applies(condition, fields_data)
        if applies is False:
            continue
        key = tuple(
            _normalize_unique_value(fields_data.get(fname))
            for fname in combo["fields"]
        )
        if None not in key:
            combo["used"].add(key)


def _max_instance_count_from_uniques(model_class):
    min_counts = []
    for field in model_class._meta.fields:
        if field.unique and field.choices:
            min_counts.append(len(field.choices))

    for constraint in model_class._meta.constraints:
        if isinstance(constraint, models.UniqueConstraint):
            fields = [
                model_class._meta.get_field(f) for f in constraint.fields
            ]
            if all(f.choices for f in fields):
                combos = 1
                for f in fields:
                    combos *= len(f.choices)
                min_counts.append(combos)

    return min(min_counts) if min_counts else 1000


def _has_unique_constraint_on_gfk(model_class, gfk_field):
    target_fields = {gfk_field.ct_field, gfk_field.fk_field}
    for constraint in model_class._meta.constraints:
        if isinstance(constraint, models.UniqueConstraint):
            if getattr(constraint, "condition", None):
                continue
            if set(constraint.fields) == target_fields:
                return True
    return False


class UniqueTracker:
    """Encapsulates tracking of unique and unique-together values for a model."""

    def __init__(self, model_class):
        self.model_class = model_class
        self.field_registry = _build_unique_field_registry(model_class)
        self.together_registry = _build_unique_together_registry(model_class)

    def should_skip(self, fields_data):
        return _should_skip_instance(
            fields_data, self.field_registry, self.together_registry
        )

    def register(self, fields_data):
        _register_unique_values(
            fields_data, self.field_registry, self.together_registry
        )


class FieldValueResolver:
    """Resolves and fills field values for a model instance fixture."""

    def __init__(self, model_class, context=None):
        self.model_class = model_class
        self.context = context
        self._inline_builder_cache = {}
        self._logged_messages = set()
        self._gfk_round_robin = {}

    def _log_once(self, message):
        if message in self._logged_messages:
            return
        self._logged_messages.add(message)
        logger.warning(message)

    def extract_base_fields(self):
        fields_data = {}
        pk_value = None
        for field in self.model_class._meta.fields:
            if _should_skip_field(field, model_class=self.model_class):
                continue
            value = self._extract_field_value(field)
            if value is not None:
                if getattr(field, "primary_key", False):
                    pk_value = value
                else:
                    _handle_field_assignment(field, value, fields_data)
        return fields_data, pk_value

    def _extract_field_value(self, field):
        if not field.blank and not field.null:
            return self._get_field_value(field)
        return None

    def _get_field_value(self, field):
        try:
            if field.name in get_ignored_field_names(self.model_class):
                return None

            if not isinstance(field, models.Field):
                return None

            if isinstance(field, (models.ForeignKey, models.OneToOneField)):
                related_model = field.related_model
                if self.context and related_model in self.context:
                    related_fixtures = self.context[related_model]
                    if related_fixtures:
                        selected = random.choice(related_fixtures)
                        return SimpleNamespace(pk=selected["pk"])
                # Best-effort: auto-generate a related fixture and reuse it
                inline = self._autocreate_related_instance(related_model)
                if inline is not None:
                    return inline
                related_instance = _safe_random_instance(related_model)
                if related_instance:
                    self._log_once(
                        f"⚠️ Using existing {related_model.__name__} for field '{field.name}'; "
                        "it will not be serialized into the generated fixtures."
                    )
                    return related_instance
                logger.warning(
                    f"⚠️ No instances of {related_model.__name__} available for field '{field.name}'. Skipping."
                )
                return None

            if field.choices:
                valid_choices = [choice[0] for choice in field.choices]
                return random.choice(valid_choices)

            return generate_value(field)

        except Exception as exc:  # pragma: no cover - guard rail
            logger.warning(
                f"⚠️ Skipping field '{field.name}' on {self.model_class.__name__}: {exc}"
            )
            return None

    def fill_required_fields(self, fields_data, unique_tracker):
        self._fill_extra_required_fields(fields_data)
        _fill_auto_now_fields(self.model_class, fields_data)
        self._fill_unique_fields(fields_data, unique_tracker)
        missing_gfk = self._fill_generic_foreign_keys(fields_data)
        if missing_gfk:
            return None
        return fields_data

    def _autocreate_related_instance(self, related_model, force_new=False):
        """
        Attempt to generate a single fixture entry for a missing related model
        and store it in the shared context so it can be reused by siblings.
        """
        if self.context is None:
            return None
        if (
            not force_new
            and related_model in self.context
            and self.context[related_model]
        ):
            selected = random.choice(self.context[related_model])
            return SimpleNamespace(pk=selected.get("pk"))

        builder = self._inline_builder_cache.get(related_model)
        if builder is None:
            builder = FixtureEntryBuilder(related_model, self.context)
            self._inline_builder_cache[related_model] = builder

        entries = builder.build_fixtures(1)
        if not entries:
            return None
        self.context.setdefault(related_model, []).extend(entries)
        selected = entries[0]
        return SimpleNamespace(pk=selected.get("pk"))

    def _build_gfk_pool(
        self, field, target_models, force_new=False, min_size=3
    ):
        key = (self.model_class, field.name)
        pool = []
        grouped = []
        for target_model in target_models:
            fixtures = (self.context or {}).get(target_model, [])
            pks = [
                entry.get("pk")
                for entry in fixtures
                if entry.get("pk") is not None
            ]
            if not pks and not force_new:
                # Ensure at least one candidate per target when possible
                inline = self._autocreate_related_instance(target_model)
                if inline:
                    pks.append(inline.pk)
            if not pks and not force_new:
                instance = _safe_random_instance(target_model)
                if instance:
                    self._log_once(
                        f"⚠️ Using existing {target_model.__name__} as GenericForeignKey target; "
                        "it will not be included in generated fixtures."
                    )
                    pks.append(instance.pk)
            grouped.append((target_model, pks))

        if force_new:
            # Build a small pool to diversify GFK targets when uniqueness demands it
            target_count = len(target_models) or 1
            idx = 0
            while sum(len(pks) for _, pks in grouped) < max(
                min_size, target_count
            ):
                target_model, pks = grouped[idx % target_count]
                inline = self._autocreate_related_instance(
                    target_model, force_new=True
                )
                if inline:
                    pks.append(inline.pk)
                idx += 1

        # Interleave targets to avoid bias toward the first available model
        max_len = max((len(pks) for _, pks in grouped), default=0)
        for i in range(max_len):
            for target_model, pks in grouped:
                if i < len(pks):
                    pool.append((target_model, pks[i]))

        dq = deque(pool)
        self._gfk_round_robin[key] = dq
        return dq

    def _next_gfk_target(self, field, target_models, force_new=False):
        key = (self.model_class, field.name)
        pool = self._gfk_round_robin.get(key)
        if pool is None or not pool:
            pool = self._build_gfk_pool(
                field, target_models, force_new=force_new
            )
        if not pool:
            return None, None
        target_model, target_pk = pool[0]
        pool.rotate(-1)
        return target_model, target_pk

    def _fill_extra_required_fields(self, fields_data):
        extra_required_fields = get_extra_required_fields_for_model(
            self.model_class
        )
        gfk_components = _get_generic_foreign_key_component_names(
            self.model_class
        )
        for field_name in extra_required_fields:
            if field_name in gfk_components:
                # GFK components are handled separately to avoid random content_type/object_id
                continue
            if field_name not in fields_data:
                try:
                    field_obj = self.model_class._meta.get_field(field_name)
                    value = self._get_field_value(field_obj)
                    if value is not None:
                        _handle_field_assignment(field_obj, value, fields_data)
                    else:
                        self._log_once(
                            f"⚠️ Unable to generate value for required field '{field_name}' in {self.model_class.__name__}"
                        )
                except Exception as exc:
                    self._log_once(
                        f"⚠️  Error filling required field '{field_name}' in {self.model_class.__name__}: {exc}"
                    )

    def _fill_unique_fields(self, fields_data, unique_tracker):
        registry_for_field = unique_tracker.field_registry
        for field in self.model_class._meta.fields:
            if field.unique and field.name not in fields_data:
                if isinstance(
                    field, (models.ForeignKey, models.OneToOneField)
                ):
                    value = self._get_field_value(field)
                    if value is not None:
                        _handle_field_assignment(field, value, fields_data)
                    continue
                try:
                    value = generate_value(
                        field, used_unique_values=registry_for_field
                    )
                    if value is not None:
                        _handle_field_assignment(field, value, fields_data)
                except Exception as exc:
                    logger.warning(
                        f"⚠️ Error generating unique value for field '{field.name}' in {self.model_class.__name__}: {exc}"
                    )

    def _fill_generic_foreign_keys(self, fields_data):
        gfk_fields = _get_generic_foreign_key_fields(self.model_class)
        if not gfk_fields:
            return False
        configured_targets = get_generic_foreign_key_targets(self.model_class)
        missing_required = False
        for field in gfk_fields:
            if field.ct_field in fields_data and field.fk_field in fields_data:
                continue

            target_models = configured_targets.get(field.name)
            if not target_models:
                # Fallback: use any model already present in the context
                target_models = [
                    model
                    for model, fixtures in (self.context or {}).items()
                    if fixtures
                ]
            force_new_target = _has_unique_constraint_on_gfk(
                self.model_class, field
            )

            fk_field_obj = self.model_class._meta.get_field(field.fk_field)
            ct_field_obj = self.model_class._meta.get_field(field.ct_field)
            is_optional = (
                getattr(fk_field_obj, "blank", False)
                or getattr(fk_field_obj, "null", False)
                or getattr(ct_field_obj, "blank", False)
                or getattr(ct_field_obj, "null", False)
            )

            if not target_models:
                if not is_optional:
                    logger.warning(
                        f"⚠️ GenericForeignKey '{field.name}' on {self.model_class.__name__} is missing DJSEED configuration. Skipping."
                    )
                missing_required = True
                continue

            target_model, target_pk = (None, None)
            if force_new_target:
                target_model, target_pk = self._next_gfk_target(
                    field, target_models, force_new=True
                )
            else:
                target_model, target_pk = self._next_gfk_target(
                    field, target_models, force_new=False
                )

            if target_model is None or target_pk is None:
                if not is_optional:
                    logger.warning(
                        f"⚠️ Unable to resolve target for GenericForeignKey '{field.name}' on {self.model_class.__name__}."
                    )
                missing_required = True
                continue

            try:
                content_type = ContentType.objects.get_for_model(target_model)
                fields_data[field.ct_field] = content_type.pk
                fields_data[field.fk_field] = fk_field_obj.to_python(target_pk)
            except (OperationalError, ProgrammingError):
                if not is_optional:
                    logger.warning(
                        f"⚠️ Cannot fetch ContentType for {target_model.__name__}; skipping required GFK '{field.name}'."
                    )
                missing_required = True
        return missing_required

    def assign_pk(self, pk_value):
        return _assign_pk_if_needed(self.model_class, pk_value)

    def ensure_primary_key_field(self, fields_data, pk_value):
        if not pk_value:
            return
        for field in self.model_class._meta.fields:
            if field.name == "id" and getattr(field, "primary_key", False):
                fields_data["id"] = str(pk_value)

    def build_entry(self, unique_tracker):
        fields_data, pk_value = self.extract_base_fields()
        fields_data = self.fill_required_fields(fields_data, unique_tracker)
        if fields_data is None:
            return None
        pk_value = self.assign_pk(pk_value)
        self.ensure_primary_key_field(fields_data, pk_value)

        if unique_tracker.should_skip(fields_data):
            return None

        unique_tracker.register(fields_data)
        return {
            "model": (
                f"{self.model_class._meta.app_label}."
                f"{self.model_class._meta.model_name}"
            ),
            "pk": str(pk_value) if pk_value else None,
            "fields": fields_data,
        }


class FixtureEntryBuilder:
    """High-level builder responsible for producing fixtures for a model."""

    def __init__(self, model_class, context=None):
        self.model_class = model_class
        self.context = context
        self.unique_tracker = UniqueTracker(model_class)
        self.resolver = FieldValueResolver(model_class, context)

    def build_fixtures(self, count):
        fixtures = []
        max_count = min(
            count, _max_instance_count_from_uniques(self.model_class)
        )
        for _ in range(max_count):
            entry = self.resolver.build_entry(self.unique_tracker)
            if entry is not None:
                fixtures.append(entry)
        return fixtures


class ManyToManyFixtureBuilder:
    """Build fixtures for implicit through models of ManyToMany relations."""

    def __init__(self, model_list, model_instances_map):
        self.model_list = model_list
        self.model_instances_map = model_instances_map

    def _create_m2m_entry(self, through_model, m2m_field, obj, related):
        model_path = (
            f"{through_model._meta.app_label}.{through_model._meta.model_name}"
        )
        return {
            "model": model_path,
            "pk": None,
            "fields": {
                m2m_field.m2m_field_name(): obj["pk"],
                m2m_field.m2m_reverse_field_name(): related["pk"],
            },
        }

    def _process_m2m_field(self, model, m2m_field):
        fixtures = []
        through_model = m2m_field.remote_field.through

        if not (
            through_model._meta.auto_created
            and through_model._meta.auto_created is not False
        ):
            return fixtures

        model_fixtures = self.model_instances_map.get(model, [])
        related_model = m2m_field.related_model
        related_fixtures = self.model_instances_map.get(related_model, [])

        if not model_fixtures or not related_fixtures:
            return fixtures

        for obj in model_fixtures:
            num_rel = random.randint(1, min(3, len(related_fixtures)))
            selected = random.sample(related_fixtures, num_rel)
            for related in selected:
                entry = self._create_m2m_entry(
                    through_model, m2m_field, obj, related
                )
                fixtures.append(entry)

        return fixtures

    def generate(self):
        fixtures = []
        for model in self.model_list:
            for m2m_field in model._meta.many_to_many:
                fixtures.extend(self._process_m2m_field(model, m2m_field))
        return fixtures


__all__ = [
    "FixtureEntryBuilder",
    "FieldValueResolver",
    "ManyToManyFixtureBuilder",
    "UniqueTracker",
    "get_extra_required_fields_for_model",
    "get_ignored_field_names",
    "get_generic_foreign_key_targets",
    "has_generic_foreign_key",
]
