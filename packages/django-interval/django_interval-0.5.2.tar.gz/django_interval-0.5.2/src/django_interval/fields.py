import re
from datetime import date
from typing import Callable, Tuple

from django.db.models import CharField, DateField
from django.contrib.contenttypes.models import ContentType
from django.forms import ValidationError
from django.urls import reverse, NoReverseMatch

from django_interval.utils import defaultdateparser
from django_interval.widgets import IntervalWidget


class GenericDateIntervalField(CharField):
    """Add additional fields to the model containing this field
    The check using `hasattr` and `setattr` to check the existence
    of the field is taken from https://github.com/django-money/django-money/blob/main/djmoney/models/fields.py#L255
    Without that the migrations did fail again and again ...
    Apparently this is *also* error prone, so we check with
    if the module is `__fake__` to know if we are running a migration.
    """

    def add_generated_date_field(self, cls, name):
        date_field = DateField(editable=False, blank=True, null=True, auto_created=True)
        cls.add_to_class(name, date_field)
        setattr(self, f"_{name}", date_field)

    def contribute_to_class(self, cls, name):
        for field_name in [f"{name}_date_sort", f"{name}_date_from", f"{name}_date_to"]:
            if not hasattr(self, f"_{field_name}") and not cls.__module__ == "__fake__":
                self.add_generated_date_field(cls, field_name)
        super().contribute_to_class(cls, name)
        setattr(cls, name, self)

    def formfield(self, *args, **kwargs):
        content_type = ContentType.objects.get_for_model(self.model)
        natural_key = f"{content_type.app_label}.{content_type.model}"
        try:
            interval_view = reverse("intervalview", args=[natural_key, self.name])
            attrs = {"data-intervaluri": interval_view}
        except NoReverseMatch:
            attrs = {}
        kwargs["widget"] = IntervalWidget(attrs=attrs)
        return super().formfield(*args, **kwargs)

    def calculate(self, date_string) -> Tuple[date, date, date]:
        raise NotImplementedError

    def _populate_fields(self, model_instance):
        name = self.attname
        value = getattr(model_instance, name)
        skip_date_interval_populate = getattr(
            model_instance, "skip_date_interval_populate", False
        )
        # this is a workaround until we find out another way to exclude
        # historical models (from `django-simple-history`)
        is_history_model = hasattr(model_instance, "history_id")
        if not skip_date_interval_populate and not is_history_model:
            if not value:
                setattr(model_instance, f"{name}_date_sort", None)
                setattr(model_instance, f"{name}_date_from", None)
                setattr(model_instance, f"{name}_date_to", None)
            else:
                try:
                    date_sort, date_from, date_to = self.calculate(value)
                    setattr(model_instance, f"{name}_date_sort", date_sort)
                    setattr(model_instance, f"{name}_date_from", date_from)
                    setattr(model_instance, f"{name}_date_to", date_to)
                except Exception as e:
                    raise ValidationError(f"Error parsing date string: {e}")

    def pre_save(self, model_instance, add):
        self._populate_fields(model_instance)
        return super().pre_save(model_instance, add)

    def save_form_data(self, instance, data):
        super().save_form_data(instance, data)
        self._populate_fields(instance)


class FuzzyDateParserField(GenericDateIntervalField):
    def __init__(
        self,
        parser: Callable[[str], Tuple[date, date, date]] = defaultdateparser,
        *args,
        **kwargs,
    ):
        self.parser = parser
        super().__init__(*args, **kwargs)

    def calculate(self, date_string):
        return self.parser(date_string)


FROM_PATTERN = r"<from: (?P<day>\d{1,2})\.(?P<month>\d{1,2})\.(?P<year>\d{1,4})>"
TO_PATTERN = r"<to: (?P<day>\d{1,2})\.(?P<month>\d{1,2})\.(?P<year>\d{1,4})>"
SORT_PATTERN = r"<sort: (?P<day>\d{1,2})\.(?P<month>\d{1,2})\.(?P<year>\d{1,4})>"


class FuzzyDateRegexField(GenericDateIntervalField):
    r"""
    Use regular expressions to differentiate between "from", "to" and "sort"
    dates.

    This field allows you to define how input dates need to be formatted to
    be successfully identified as/parsed out as the three available dates
    and to get stored in the relevant `_date_from`, `_date_to` and
    `_date_sort` fields.

    Each of the three attributes `from_pattern`, `to_pattern` and `sort_pattern`
    can be assigned its own RegEx pattern, which allows you to use a custom
    prefix or identifier for each date. The only required elements all
    patterns have (to have) in common are named RegEx groups for the
    <year>, <month> and <day> portions of each date.
    If you don't provide your own patterns, three pre-defined patterns,
    `FROM_PATTERN`, `TO_PATTERN`, `SORT_PATTERN`, are used as fallbacks.
    They expect dates to be enclosed in angled brackets, to follow German
    date formatting rules and to be identified via prefixes "from: ", "to: "
    and "sort: ". Example for from date: <from: 24.12.2024>

    A custom pattern could e.g. require dates to follow the ISO 8601 standard,
    i.e. be formatted YYYY-MM-DD, but use different characters to identify
    or separate individual dates.
    Example:
        "2024 (sort=2024-06-01)" may be a choice to have `_date_sort` set
        to datetime.date(2024, 6, 1). To achieve this, the following
        regular expression could be used with `sort_pattern`:
        r"\(sort=(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})\)"
    """

    def __init__(
        self,
        from_pattern=FROM_PATTERN,
        to_pattern=TO_PATTERN,
        sort_pattern=SORT_PATTERN,
        *args,
        **kwargs,
    ):
        self.from_pattern = from_pattern
        self.to_pattern = to_pattern
        self.sort_pattern = sort_pattern
        super().__init__(*args, **kwargs)

    def _match_to_date(self, regex_match: re.Match) -> date:
        match_dict = regex_match.groupdict()
        if match_dict.keys() >= {"day", "month", "year"}:
            month = int(match_dict.get("month", "01"))
            day = int(match_dict.get("day", "01"))
            year = int(match_dict["year"])
            return date(year, month, day)
        raise ValueError(
            f"Regex pattern does not contain all needed named groups (year, month, day): {match_dict}"
        )

    def calculate(self, date_string) -> Tuple[date, date, date]:
        sort_date, from_date, to_date = None, None, None
        if match := re.search(self.sort_pattern, date_string):
            sort_date = self._match_to_date(match)
        if match := re.search(self.from_pattern, date_string):
            from_date = self._match_to_date(match)
        if match := re.search(self.to_pattern, date_string):
            to_date = self._match_to_date(match)
        return sort_date, from_date, to_date
