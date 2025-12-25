from django.db import models
from django_interval.fields import FuzzyDateParserField, FuzzyDateRegexField


class DjangoIntervalTestModel(models.Model):
    fuzzy_parser_field = FuzzyDateParserField()
    fuzzy_regex_field = FuzzyDateRegexField()
