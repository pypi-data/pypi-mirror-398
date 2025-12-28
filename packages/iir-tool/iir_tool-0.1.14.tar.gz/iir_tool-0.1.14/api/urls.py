from django.urls import path

from . import health, views

urlpatterns = [
    path("api/v1/replace", views.ReplaceAPIView.as_view(), name="api-replace"),
    path("api/v1/categories", views.CategoriesAPIView.as_view(), name="api-categories"),
    path("health/startup/", health.startup_health, name="health-startup"),
    path("health/live/", health.live_health, name="health-live"),
    path("health/ready/", health.ready_health, name="health-ready"),
]
