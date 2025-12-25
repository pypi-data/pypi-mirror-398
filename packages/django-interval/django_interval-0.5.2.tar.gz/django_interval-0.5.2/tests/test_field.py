from django.test import TestCase
from tests.models import DjangoIntervalTestModel
from datetime import date as dt


class FuzzyDateParserFieldTest(TestCase):
    def test_complete_date(self):
        obj = DjangoIntervalTestModel.objects.create(fuzzy_parser_field="2024-11-01")
        obj.save()  # Save the object to trigger the field's save method
        retrieved = DjangoIntervalTestModel.objects.get(pk=obj.pk)
        assert retrieved.fuzzy_parser_field == "2024-11-01"
        assert retrieved.fuzzy_parser_field_date_sort == dt.fromisoformat("2024-11-01")
        assert retrieved.fuzzy_parser_field_date_from == dt.fromisoformat("2024-11-01")
        assert retrieved.fuzzy_parser_field_date_to == dt.fromisoformat("2024-11-01")

    def test_incomplete_date(self):
        obj = DjangoIntervalTestModel.objects.create(fuzzy_parser_field="2024-11")
        obj.save()
        retrieved = DjangoIntervalTestModel.objects.get(pk=obj.pk)
        assert retrieved.fuzzy_parser_field == "2024-11"
        assert retrieved.fuzzy_parser_field_date_sort == dt.fromisoformat("2024-11-15")
        assert retrieved.fuzzy_parser_field_date_from == dt.fromisoformat("2024-11-01")
        assert retrieved.fuzzy_parser_field_date_to == dt.fromisoformat("2024-11-30")
        obj = DjangoIntervalTestModel.objects.create(fuzzy_parser_field="2024")
        obj.save()
        retrieved = DjangoIntervalTestModel.objects.get(pk=obj.pk)
        assert retrieved.fuzzy_parser_field == "2024"
        assert retrieved.fuzzy_parser_field_date_sort == dt.fromisoformat("2024-07-01")
        assert retrieved.fuzzy_parser_field_date_from == dt.fromisoformat("2024-01-01")
        assert retrieved.fuzzy_parser_field_date_to == dt.fromisoformat("2024-12-31")

    def test_single_valid_ISO_date_in_angled_brackets(self):
        """Field contains random extra text outside angled brackets to demonstrate that's allowed."""
        obj = DjangoIntervalTestModel.objects.create(fuzzy_parser_field="<20241101> (TBD, check)")
        obj.save()
        retrieved = DjangoIntervalTestModel.objects.get(pk=obj.pk)
        assert retrieved.fuzzy_parser_field == "<20241101> (TBD, check)"
        assert retrieved.fuzzy_parser_field_date_sort == dt.fromisoformat("2024-11-01")
        assert retrieved.fuzzy_parser_field_date_from is None
        assert retrieved.fuzzy_parser_field_date_to is None

    def test_triple_valid_ISO_dates_in_angled_brackets(self):
        """Dates are surrounded by additional, superfluous whitespace to demonstrate that's allowed."""
        obj = DjangoIntervalTestModel.objects.create(fuzzy_parser_field="< 2024-11-15, 2024-11-01, 2024-12-01 >")
        obj.save()
        retrieved = DjangoIntervalTestModel.objects.get(pk=obj.pk)
        assert retrieved.fuzzy_parser_field == "< 2024-11-15, 2024-11-01, 2024-12-01 >"
        assert retrieved.fuzzy_parser_field_date_sort == dt.fromisoformat("2024-11-15")
        assert retrieved.fuzzy_parser_field_date_from == dt.fromisoformat("2024-11-01")
        assert retrieved.fuzzy_parser_field_date_to == dt.fromisoformat("2024-12-01")

class RegexDateParserFieldTest(TestCase):
    def test_regex_date(self):
        obj = DjangoIntervalTestModel.objects.create(
            fuzzy_regex_field="2023 <sort: 15.08.2023> <from: 01.01.2023> <to: 31.12.2023>"
        )
        obj.save()
        retrieved = DjangoIntervalTestModel.objects.get(pk=obj.pk)
        assert (
            retrieved.fuzzy_regex_field
            == "2023 <sort: 15.08.2023> <from: 01.01.2023> <to: 31.12.2023>"
        )
        assert retrieved.fuzzy_regex_field_date_sort == dt.fromisoformat("2023-08-15")
        assert retrieved.fuzzy_regex_field_date_from == dt.fromisoformat("2023-01-01")
        assert retrieved.fuzzy_regex_field_date_to == dt.fromisoformat("2023-12-31")
