from django.forms.widgets import Input
from django.templatetags.static import static
from django.utils.html import html_safe


@html_safe
class JSPath:
    def __str__(self):
        path = static("js/intervalwidget.js")
        return '<script src="' + path + '" defer></script>'


class IntervalWidget(Input):
    class Media:
        js = [JSPath()]
        css = {"all": ["css/intervalwidget.css"]}
