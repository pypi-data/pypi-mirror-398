from django.urls import path

from django_interval.views import IntervalView

urlpatterns = [
    path(
        "interval/<str:natural_key>/<str:field>",
        IntervalView.as_view(),
        name="intervalview",
    )
]
