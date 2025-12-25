# Django Interval

django-interval is a [Django](https://www.djangoproject.com/) app. It provides
model fields to store date information with some extra data stored in
additional fields. The additional fields are composed of a `_date_sort`, a `_date_from`
and a `_date_to` field that store data that is generated from the string stored in
the main model field.

# Installation

Install `django-interval` and add `django_interval` to your
[INSTALLED_APPS](https://docs.djangoproject.com/en/stable/ref/settings/#std-setting-INSTALLED_APPS)
add the `django_interval.urls` to your `urlpatterns`:
```
urlpatterns += [path("", include("django_interval.urls"))]
```

Use either the `django_interval.fields.FuzzyDateParserField` or the
`django_interval.fields.FuzzyDateRegexField` in your models. Both
come with sensible defaults (a parser method in the `FuzzyDateParserField`
and a list of regexes in the `FuzzyDateRegexField`), but it is possible
to pass custom parser or regexes as arguments.
