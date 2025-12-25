# seeder/base.py

import json
import traceback

from django.apps import apps
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.db.utils import OperationalError, ProgrammingError

from .builders import (
    FixtureEntryBuilder,
    ManyToManyFixtureBuilder,
    get_extra_required_fields_for_model,
)
from .logging import get_logger
from .ordering import ModelOrderingStrategy
from .registry import registry

logger = get_logger(__name__)


def write_fixture_file(fixture_data, output_path="seed_data.json"):
    with open(output_path, "w") as f:
        json.dump(fixture_data, f, cls=DjangoJSONEncoder, indent=2)
    logger.info(f"✅ Fixture saved to {output_path}")


def generate_fixture_data(model_class, count=10, context=None):
    builder = FixtureEntryBuilder(model_class, context)
    return builder.build_fixtures(count)


def generate_many_to_many_fixtures(model_list, model_instances_map):
    builder = ManyToManyFixtureBuilder(model_list, model_instances_map)
    return builder.generate()


class FixtureSeeder:
    def __init__(
        self,
        app_labels=None,
        count_per_model=10,
        output_path="seed_data.json",
        ordering_strategy=None,
    ):
        registry.configure_from_settings()
        self.app_labels = (
            app_labels
            if app_labels is not None
            else [app.label for app in apps.get_app_configs()]
        )
        self.count_per_model = count_per_model
        self.output_path = output_path
        self.ordering_strategy = ordering_strategy or ModelOrderingStrategy()
        self.model_instances_map = {}
        self.all_fixtures = []

    def _collect_models(self):
        model_list = []
        for app_label in self.app_labels:
            app_models = list(apps.get_app_config(app_label).get_models())
            model_list.extend(app_models)
        return model_list

    def _should_skip_model(self, model_class):
        required_fields = get_extra_required_fields_for_model(model_class)
        for field in model_class._meta.fields:
            if (
                isinstance(field, (models.ForeignKey, models.OneToOneField))
                and not field.null
                and not field.blank
                and field.name in required_fields
            ):
                if field.related_model in self.model_instances_map:
                    continue
                try:
                    if field.related_model.objects.exists():
                        continue
                except (OperationalError, ProgrammingError):
                    logger.info(
                        f"⚠️ Unable to query {field.related_model.__name__}; "
                        "assuming no existing records."
                    )
                logger.warning(
                    f"⚠️ Skipping {model_class.__name__} because it depends on {field.related_model.__name__}, which is missing from the context."
                )
                return True
        return False

    def _seed_model(self, model_class):
        fixture = generate_fixture_data(
            model_class,
            count=self.count_per_model,
            context=self.model_instances_map,
        )
        self.model_instances_map[model_class] = fixture
        self.all_fixtures.extend(fixture)

    def _append_many_to_many_fixtures(self, model_list):
        m2m_fixtures = generate_many_to_many_fixtures(
            model_list, self.model_instances_map
        )
        self.all_fixtures.extend(m2m_fixtures)

    def _merge_inline_fixtures(self):
        """Ensure fixtures created inline for dependencies are persisted."""
        existing = {
            (entry.get("model"), entry.get("pk")) for entry in self.all_fixtures
        }
        for fixtures in self.model_instances_map.values():
            for entry in fixtures:
                key = (entry.get("model"), entry.get("pk"))
                if entry.get("pk") is None:
                    continue
                if key in existing:
                    continue
                self.all_fixtures.append(entry)
                existing.add(key)

    def run(self):
        model_list = self._collect_models()
        ordered_models = self.ordering_strategy.order(model_list)

        pending = list(ordered_models)
        while pending:
            progressed = False
            next_pending = []
            for model in pending:
                if self._should_skip_model(model):
                    logger.info(f"Skipping {model.__name__}.")
                    next_pending.append(model)
                    continue
                try:
                    self._seed_model(model)
                    logger.info(f"✅ {model.__name__} - generated")
                    progressed = True
                except Exception as exc:
                    logger.warning(f"⚠️ {model.__name__} failed: {exc}")
                    traceback.print_exc()
            if not progressed:
                break
            pending = next_pending

        # Final best-effort pass for any remaining models, even if dependencies
        # were not satisfied, to maximize generated data.
        if pending:
            logger.warning(
                "⚠️ Proceeding with best-effort generation for remaining models despite unresolved dependencies."
            )
            for model in pending:
                try:
                    self._seed_model(model)
                except Exception as exc:
                    logger.warning(
                        f"⚠️ Error generating fixture for {model.__name__} in best-effort pass: {exc}"
                    )
                    traceback.print_exc()

        # Capture inline fixtures generated on the fly (e.g., GFK targets)
        self._merge_inline_fixtures()
        self._append_many_to_many_fixtures(ordered_models)
        if self.output_path:
            write_fixture_file(self.all_fixtures, self.output_path)
        return self.all_fixtures


def seed_all(
    app_labels=None,
    count_per_model=10,
    output_path="seed_data.json",
):
    seeder = FixtureSeeder(
        app_labels=app_labels,
        count_per_model=count_per_model,
        output_path=output_path,
    )
    return seeder.run()


__all__ = [
    "FixtureSeeder",
    "generate_fixture_data",
    "generate_many_to_many_fixtures",
    "seed_all",
    "write_fixture_file",
]
