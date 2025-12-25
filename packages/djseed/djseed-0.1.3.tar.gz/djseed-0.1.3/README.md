# djseed

Generate reproducible JSON fixtures from existing Django models. The fixtures work out of the box with `manage.py loaddata`, making reseeding development and review databases painless.

## Installation

From PyPI (recommended):

```bash
python -m pip install djseed
```

Or add to a Poetry project:

```bash
poetry add djseed
```

For local development, clone the repo and run `poetry install`; build with `poetry build`.

## Requirements

- Python 3.10+
- Django (uses your project’s models and settings)
- Access to the same environment your project uses (virtualenv, Poetry env, etc.)

## Quickstart (CLI)

```bash
djseed \
  --pythonpath "/path/to/project/root" \
  --settings config.settings.local \
  --apps core feeds \
  --count 300 \
  --output seed_data.json
```

Then load the generated fixtures:

```bash
python manage.py flush  # avoid FK integrity errors
python manage.py loaddata seed_data.json
```

Key options:

- `--settings`: Django settings module (falls back to `DJANGO_SETTINGS_MODULE`).
- `--pythonpath`: prepend directories to `PYTHONPATH` before configuring Django.
- `--apps`: list of app labels to process (`--apps core billing`).
- `--count`: objects per model (default: 10).
- `--output`: destination JSON file (default: `seed_data.json`).
- `--no-output`: skip disk writes (useful if you only need the return value or `--stdout`).
- `--stdout`: send JSON to stdout for piping.
- `--config`: import custom modules after `django.setup()` so you can register overrides.

## Django-side configuration

Expose a `DJSEED` dictionary inside your settings module to tweak required or ignored fields:

```python
# settings.py
DJSEED = {
    "extra_required_fields": {
        "*": {"created_at", "updated_at"},
        "users.user": {"first_name", "last_name"},
    },
    "ignored_field_names": {
        "*": {"created_by"},
    },
    "generic_foreign_keys": {
        "feeds.notification": {
            "content_object": {"feeds.like", "feeds.comment"},
        },
    },
  "model_priorities": {
    "core.user": 0,
    "feeds.comment": 1,
    "feeds.notification": 2,
  },
  "email_domain": "example.com",      # default domain for generated emails
  "default_password": "0000",    # default password for hashable fields
}
```

Need to do it in code instead? Use the registry helpers:

```python
from seeder import registry

registry.register_extra_required_fields("users.user", {"first_name"})
registry.register_ignored_field_names("*", {"created_by"})
registry.register_generic_foreign_key_models(
  "feeds.notification", {"content_object": {"feeds.like", "feeds.comment"}}
)
registry.register_field_generator("users.user.cpf", my_cpf_generator)  # model-specific
registry.register_field_type_generator(models.JSONField, my_json_generator)
```

For GenericForeignKey fields, list the fully-qualified model labels each field may point
to. djseed uses those hints to set the underlying `content_type` and `object_id`
fields with existing fixtures (when available) or with random database records.
Custom generators receive a `faker` instance and the Django `field`; return the value you want stored.
Custom generator registration is intentionally code-only (e.g., in the module passed via `--config`) to keep `DJSEED` settings minimal.

> Tip: djseed works best against a migrated database. If tables are missing, it will fall back to generating everything in-memory and skip DB lookups.

- Conditional UniqueConstraints are ignored during generation to maximize combinations. Mirrored unique constraints (e.g. `user1,user2` and `user2,user1`) are deduplicated to reduce false collisions during fixture generation. The database will still enforce the actual constraints at load time.

## Programmatic usage

```python
from seeder import seed_all

fixtures = seed_all(
    app_labels=["core", "feeds"],
    count_per_model=15,
    output_path="fixtures.json",
)
```

When `output_path` is provided (default `seed_data.json`), the file is written automatically. The function always returns the generated fixtures list so you can post-process or store it yourself.

## Troubleshooting

- Make sure the command runs inside the same virtual environment as Django so apps and settings resolve correctly.
- If you see missing module errors, double-check `--pythonpath` and `--settings`.
- Use `--stdout` plus `jq`/`rg` for quick inspection: `djseed --stdout | jq '. | length'`.
