# seeder/generators.py
import random

from django.contrib.auth.hashers import make_password
from django.core import validators
from django.db import models
from django.utils import timezone
from faker import Faker

from .registry import registry

faker = Faker()

DEFAULT_EMAIL_DOMAIN = "example.com"
DEFAULT_PASSWORD = "0000"


def _generate_by_field_name(field, faker_obj):
    name = (getattr(field, "name", "") or "").lower()
    flattened = name.replace("_", "")

    if "password" in name:
        default_password = registry.get_default_password() or DEFAULT_PASSWORD
        return make_password(default_password)
    if "email" in name:
        domain = registry.get_email_domain() or DEFAULT_EMAIL_DOMAIN
        return faker_obj.email(domain=domain)
    if "username" in flattened or flattened.endswith("user"):
        return faker_obj.user_name()
    if "phone" in name or "mobile" in name or "cell" in name:
        return faker_obj.phone_number()
    if "city" in name:
        return faker_obj.city()
    if "state" in name or "province" in name or "region" in name:
        return faker_obj.state()
    if "country" in name:
        return faker_obj.country()
    if "zip" in name or "postal" in name:
        return faker_obj.postcode()
    if "street" in name:
        return faker_obj.street_address()
    if "address" in name:
        return faker_obj.address()
    if "image" in name or "avatar" in name or "photo" in name:
        return faker_obj.image_url()
    if "file" in name or "path" in name:
        return faker_obj.file_path(depth=2)
    if "website" in name or "url" in name:
        return faker_obj.url()
    if "firstname" in flattened:
        return faker_obj.first_name()
    if "lastname" in flattened or "surname" in flattened:
        return faker_obj.last_name()
    if "fullname" in flattened or flattened == "name":
        return faker_obj.name()
    if "name" in flattened:
        return faker_obj.word()
    if "bio" in name or "about" in name or "description" in name:
        return faker_obj.paragraph()
    if "title" in name or "headline" in name:
        return faker_obj.sentence(nb_words=6)
    if "summary" in name or "subtitle" in name:
        return faker_obj.sentence(nb_words=4)
    if (
        "comment" in name
        or "content" in name
        or "message" in name
        or "text" in name
        or "body" in name
    ):
        return faker_obj.text(max_nb_chars=200)
    if "slug" in name:
        return faker_obj.slug()
    if "company" in name or "org" in name:
        return faker_obj.company()
    if "job" in name or "role" in name or "position" in name:
        return faker_obj.job()
    if "timezone" in name:
        return faker_obj.timezone()
    if "language" in name:
        return faker_obj.language_code()
    if "currency" in name:
        return faker_obj.currency_code()
    if "color" in name or "colour" in name:
        return faker_obj.color_name()
    if "lat" in name:
        return float(faker_obj.latitude())
    if "lng" in name or "lon" in name:
        return float(faker_obj.longitude())
    if "ip" in name:
        return faker_obj.ipv4_public()
    if "token" in name or "secret" in name or "api_key" in name:
        return faker_obj.sha256()
    if "code" in name or "otp" in name or "pin" in name:
        return faker_obj.random_number(digits=6)
    if "uuid" in name or "guid" in name or name == "id":
        return faker_obj.uuid4()
    return faker_obj.sentence()


def _get_numeric_bounds(field, default_min, default_max):
    min_value, max_value = default_min, default_max
    for validator in getattr(field, "validators", []):
        if isinstance(validator, validators.MinValueValidator):
            try:
                min_value = max(min_value, validator.limit_value)  # type: ignore[arg-type]
            except TypeError:
                continue
        elif isinstance(validator, validators.MaxValueValidator):
            try:
                max_value = min(max_value, validator.limit_value)  # type: ignore[arg-type]
            except TypeError:
                continue
    return min_value, max_value


def _generate_decimal(field, faker_obj):
    max_digits = getattr(field, "max_digits", 6) or 6
    decimal_places = getattr(field, "decimal_places", 2) or 0
    left_digits = max(max_digits - decimal_places, 1)
    positive = any(
        isinstance(v, validators.MinValueValidator)
        and getattr(v, "limit_value", 0) >= 0
        for v in getattr(field, "validators", [])
    )
    return faker_obj.pydecimal(
        left_digits=left_digits,
        right_digits=decimal_places,
        positive=positive,
    )


def _generate_custom_value(field, faker_obj):
    generator = registry.get_field_generator(field)
    if generator is None:
        return None
    try:
        return generator(faker_obj, field)
    except Exception as exc:
        raise ValueError(
            f"Custom generator failed for field '{getattr(field, 'name', '?')}'"
        ) from exc


def _generate_candidate(field, faker_obj):
    custom = _generate_custom_value(field, faker_obj)
    if custom is not None:
        return custom

    value = _generate_by_field_type(field, faker_obj)
    if value is not None:
        return value
    return faker_obj.word()


def _generate_by_field_type(field, faker_obj):
    if isinstance(field, models.EmailField):
        domain = registry.get_email_domain() or DEFAULT_EMAIL_DOMAIN
        return faker_obj.email(domain=domain)
    if isinstance(field, models.UUIDField):
        return faker_obj.uuid4()
    if isinstance(field, models.URLField):
        return faker_obj.url()
    if isinstance(field, models.DateField):
        return faker_obj.date()
    if isinstance(field, models.TimeField):
        return faker_obj.time_object()
    if isinstance(field, models.DecimalField):
        return _generate_decimal(field, faker_obj)
    if isinstance(field, models.DateTimeField):
        return faker_obj.date_time().astimezone(tz=timezone.utc)
    if isinstance(field, models.DurationField):
        return faker_obj.time_delta()
    if isinstance(field, models.BooleanField):
        return random.choice([True, False])
    if isinstance(field, models.PositiveSmallIntegerField):
        min_value, max_value = _get_numeric_bounds(field, 0, 32767)
        return random.randint(int(min_value), int(max_value))
    if isinstance(field, models.SmallIntegerField):
        min_value, max_value = _get_numeric_bounds(field, -32768, 32767)
        return random.randint(int(min_value), int(max_value))
    if isinstance(field, models.PositiveIntegerField):
        min_value, max_value = _get_numeric_bounds(field, 1, 9999)
        return random.randint(int(min_value), int(max_value))
    if isinstance(field, models.BigIntegerField):
        min_value, max_value = _get_numeric_bounds(
            field, 1, 2**31 - 1
        )
        return random.randint(int(min_value), int(max_value))
    if isinstance(field, models.IntegerField):
        min_value, max_value = _get_numeric_bounds(field, 1, 9999)
        return random.randint(int(min_value), int(max_value))
    if isinstance(field, models.FloatField):
        min_value, max_value = _get_numeric_bounds(field, 1.0, 9999.0)
        return round(random.uniform(float(min_value), float(max_value)), 2)
    if isinstance(field, models.GenericIPAddressField):
        return faker_obj.ipv4()
    if isinstance(field, models.BinaryField):
        return faker_obj.binary(length=12).hex()
    if isinstance(field, models.SlugField):
        return faker_obj.slug()
    if isinstance(field, models.JSONField):
        return faker_obj.pydict(
            nb_elements=3, value_types=[str, int, float, bool]
        )
    try:
        from django.contrib.postgres.fields import ArrayField
    except Exception:  # pragma: no cover - optional postgres dependency
        ArrayField = None
    if ArrayField and isinstance(field, ArrayField):
        if isinstance(field.base_field, ArrayField):
            base_value = faker_obj.word()
        else:
            base_value = _generate_by_field_type(field.base_field, faker_obj)
        if base_value is None and getattr(field.base_field, "name", None):
            base_value = _generate_by_field_name(field.base_field, faker_obj)
        base_value = base_value or faker_obj.word()
        return [base_value for _ in range(random.randint(1, 3))]
    if isinstance(field, models.FilePathField):
        return faker_obj.file_path(depth=3)
    if isinstance(field, models.FileField):
        return faker_obj.file_path(depth=3)
    if isinstance(field, models.ImageField):
        return faker_obj.image_url()
    if isinstance(field, models.CharField) and field.choices:
        valid_choices = [choice[0] for choice in field.choices]
        return random.choice(valid_choices)
    if isinstance(field, models.TextField):
        return _generate_by_field_name(field, faker_obj)
    if isinstance(field, models.CharField):
        return _generate_by_field_name(field, faker_obj)
    return None


def generate_value(field, used_unique_values=None):
    registry.configure_from_settings()

    def _trim_value(value):
        if (
            isinstance(field, (models.CharField, models.TextField))
            and hasattr(field, "max_length")
            and field.max_length
            and isinstance(value, str)
        ):
            return value[: field.max_length]
        return value

    is_unique = field.unique and used_unique_values is not None
    if is_unique:
        faker_obj = (
            faker.unique
            if isinstance(field, (models.EmailField, models.URLField))
            else faker
        )
        used_values = used_unique_values.get(field.name, set())
        for _ in range(100):
            if isinstance(field, models.CharField) and field.choices:
                remaining = [
                    v for v, _ in field.choices if v not in used_values
                ]
                if not remaining:
                    break
                value = random.choice(remaining)
            else:
                value = _trim_value(_generate_candidate(field, faker_obj))
            if value not in used_values:
                return value
        raise ValueError(
            f"Unable to generate unique value for field: {field.name}"
        )
    else:
        faker_obj = faker
        value = _generate_candidate(field, faker_obj)
        return _trim_value(value)
