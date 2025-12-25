from django import template

register = template.Library()


@register.inclusion_tag("django_interval/inline_interval.html")
def date_interval(to_date=None, from_date=None, sort_date=None):
    return {"to_date": to_date, "from_date": from_date, "sort_date": sort_date}
