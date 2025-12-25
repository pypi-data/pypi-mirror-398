# seeder/ordering.py

from django.db import models

from .builders import get_extra_required_fields_for_model
from .registry import registry


class ModelOrderingStrategy:
    """
    Orders models based on configured priorities and inferred dependencies from
    required relations. Lower priority numbers are processed first.
    """

    def __init__(self, priorities=None):
        registry.configure_from_settings()
        self.priorities = dict(priorities or registry.get_model_priorities())

    def _priority_for_model(self, model_class):
        label = model_class._meta.label_lower
        model_name = model_class._meta.model_name
        app_label = model_class._meta.app_label
        return self.priorities.get(
            label,
            self.priorities.get(
                model_name, self.priorities.get(app_label, 1000)
            ),
        )

    def _dependencies(self, model_class, candidates):
        required_fields = get_extra_required_fields_for_model(model_class)
        dependencies = set()
        for field in model_class._meta.fields:
            if (
                isinstance(field, (models.ForeignKey, models.OneToOneField))
                and not field.null
                and not field.blank
                and field.related_model in candidates
            ):
                dependencies.add(field.related_model)

        for field_name in required_fields:
            try:
                field_obj = model_class._meta.get_field(field_name)
            except Exception:
                continue
            if isinstance(
                field_obj, (models.ForeignKey, models.OneToOneField)
            ):
                related_model = field_obj.related_model
                if related_model in candidates:
                    dependencies.add(related_model)

        return dependencies

    def order(self, models):
        if not models:
            return []

        candidates = set(models)
        dependency_map = {
            model: self._dependencies(model, candidates) for model in models
        }
        dependents = {model: set() for model in models}
        for model, deps in dependency_map.items():
            for dependency in deps:
                dependents.setdefault(dependency, set()).add(model)

        indegree = {model: len(deps) for model, deps in dependency_map.items()}
        ordered = []
        ready = [model for model in models if indegree[model] == 0]

        while ready:
            ready.sort(
                key=lambda m: (
                    self._priority_for_model(m),
                    m._meta.label_lower,
                )
            )
            current = ready.pop(0)
            ordered.append(current)
            for dependent in dependents.get(current, set()):
                indegree[dependent] -= 1
                if indegree[dependent] == 0:
                    ready.append(dependent)

        if len(ordered) < len(models):
            remaining = [model for model in models if model not in ordered]
            remaining.sort(
                key=lambda m: (
                    self._priority_for_model(m),
                    m._meta.label_lower,
                )
            )
            print(
                "⚠️ Unresolved model dependencies detected; applying priority-based order for remaining models."
            )
            ordered.extend(remaining)

        return ordered


__all__ = ["ModelOrderingStrategy"]
