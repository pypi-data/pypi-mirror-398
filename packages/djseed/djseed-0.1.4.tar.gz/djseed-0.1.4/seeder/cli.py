# seeder/cli.py

from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
from pathlib import Path
from typing import Iterable, List, Optional

import django
from django.core.exceptions import ImproperlyConfigured

from .registry import registry


def _extend_pythonpath(paths: Iterable[str]) -> None:
    for entry in paths:
        path = Path(entry).expanduser().resolve()
        if not path.exists():
            print(f"⚠️ Skipping missing path: {path}")
            continue
        if str(path) not in sys.path:
            sys.path.insert(0, str(path))


def _import_config_modules(modules: Iterable[str]) -> None:
    for module_path in modules:
        try:
            importlib.import_module(module_path)
            print(f"✅ Loaded config module: {module_path}")
        except ModuleNotFoundError as exc:
            print(f"⚠️ Failed to import {module_path}: {exc}")


def _normalize_app_labels(raw: Optional[List[str]]) -> Optional[List[str]]:
    if not raw:
        return None
    labels: List[str] = []
    for item in raw:
        parts = [value.strip() for value in item.split(",") if value.strip()]
        labels.extend(parts)
    return labels or None


def _parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="djseed",
        description=(
            "Generate JSON fixtures from the models registered in a configured"
            "Django project."
        ),
    )
    parser.add_argument(
        "--settings",
        help=(
            "Django settings module (e.g. myproject.settings). "
            "If omitted, DJANGO_SETTINGS_MODULE will be used."
        ),
    )
    parser.add_argument(
        "--pythonpath",
        action="append",
        default=[],
        help=(
            "Additional directories to prepend to PYTHONPATH before Django "
            "is configured. May be used multiple times."
        ),
    )
    parser.add_argument(
        "--config",
        action="append",
        default=[],
        help=(
            "Python modules to import after django.setup(). "
            "Useful for registering custom rules with djseed.registry."
        ),
    )
    parser.add_argument(
        "--apps",
        nargs="+",
        help=(
            "List of app labels to include. Supports multiple arguments or "
            "comma-separated values. If omitted, all installed apps are used."
        ),
    )
    parser.add_argument(
        "--count",
        type=int,
        default=10,
        help="Number of objects to generate per model (default: 10).",
    )
    parser.add_argument(
        "--output",
        default="seed_data.json",
        help="Destination JSON filename (default: seed_data.json).",
    )
    parser.add_argument(
        "--no-output",
        action="store_true",
        help="Disable writing to disk; only return the in-memory result.",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Print the generated JSON to stdout.",
    )
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = _parse_args(argv)

    if args.pythonpath:
        _extend_pythonpath(args.pythonpath)

    if args.settings:
        os.environ["DJANGO_SETTINGS_MODULE"] = args.settings

    settings_module = os.environ.get("DJANGO_SETTINGS_MODULE")
    if not settings_module:
        print(
            "❌ Provide a Django settings module via --settings or DJANGO_SETTINGS_MODULE."
        )
        return 1

    try:
        django.setup()
    except ImproperlyConfigured as exc:
        print(f"❌ Failed to configure Django: {exc}")
        return 1

    if args.config:
        _import_config_modules(args.config)

    app_labels = _normalize_app_labels(args.apps)
    output_path = None if args.no_output else args.output

    from .base import (
        seed_all,
    )  # Late import keeps django.setup() optional for --help

    fixtures = seed_all(
        app_labels=app_labels,
        count_per_model=args.count,
        output_path=output_path,
    )

    if args.stdout:
        print(json.dumps(fixtures, ensure_ascii=False, indent=2))

    # Allow subsequent runs to reload dynamic settings overrides
    registry.reset_settings_cache()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
