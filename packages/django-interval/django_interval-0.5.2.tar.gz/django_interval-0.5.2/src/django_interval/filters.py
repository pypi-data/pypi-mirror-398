from django.db.models import Q
from django import forms
from django_filters import Filter


class IntervalRangeMultiWidget(forms.MultiWidget):
    """
    A basic implementation of Django's MultiWidget class, that
    comes with its own multiwidget template and implements a
    simple decompress function.
    """
    template_name = "django_interval/widgets/multiwidget.html"
    use_fieldset = False

    def __init__(self):
        widgets = (forms.TextInput(), forms.TextInput())
        super().__init__(widgets=widgets)

    def decompress(self, value):
        if value is None:
            return [None, None]
        return value


class IntervalRangeMultiField(forms.MultiValueField):
    """
    A basic implementation of Django's MultiValueField class
    that passes the `type`, the `start` and the `end` arguments
    on to the widget via the widget_attrs method.
    """
    widget = IntervalRangeMultiWidget

    def __init__(self, *args, **kwargs):
        self.start = kwargs.pop("start", None)
        self.end = kwargs.pop("end", None)
        self.type = kwargs.pop("type", "date")
        super().__init__(*args, **kwargs)

    def widget_attrs(self, widget):
        attrs = super().widget_attrs(widget)
        if self.start:
            attrs["min"] = self.start
        if self.end:
            attrs["max"] = self.end
        attrs["type"] = self.type
        return attrs

    def compress(self, value):
        return value


class DateIntervalRangeFilter(Filter):
    """
    Filter a django-interval value by using a max and min date
    interval and use the `from` and `to` values to filter
    Use this by setting filter_overrides in your filterset:
    ```
    filter_overrides = {
            FuzzyDateParserField: {
                'filter_class': DateIntervalRangeFilter
            }
    }
    ```
    Instead of using filter_overrides you can also manually
    use the filterclass. If you pass the `start` and `end`
    arguments to the filterclass, they will be set on the
    widget as their `min` and `max` values.
    """
    field_class = IntervalRangeMultiField

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.extra["type"] = "date"
        self.extra["fields"] = (forms.DateField(), forms.DateField())

    def filter(self, qs, value):
        q = Q()
        if value:
            _min, _max = value
            if _min:
                q &= Q(**{f"{self.field_name}_date_from__gte": _min})
            if _max:
                q &= Q(**{f"{self.field_name}_date_to__lte": _max})
        return qs.filter(q)


class YearIntervalRangeFilter(Filter):
    """
    Filter a django-interval value by using a max and min year
    interval and use the `from` and `to` values to filter
    Use this by setting filter_overrides in your filterset:
    ```
    filter_overrides = {
            FuzzyDateParserField: {
                'filter_class': YearIntervalRangeFilter
            }
    }
    ```
    Instead of using filter_overrides you can also manually
    use the filterclass. If you pass the `start` and `end`
    arguments to the filterclass, they will be set on the
    widget as their `min` and `max` values.
    """
    field_class = IntervalRangeMultiField

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.extra["type"] = "number"
        self.extra["fields"] = (forms.IntegerField(), forms.IntegerField())

    def filter(self, qs, value):
        q = Q()
        if value:
            _min, _max = value
            if _min:
                q &= Q(**{f"{self.field_name}_date_from__year__gte": _min})
            if _max:
                q &= Q(**{f"{self.field_name}_date_to__year__lte": _max})
        return qs.filter(q)
