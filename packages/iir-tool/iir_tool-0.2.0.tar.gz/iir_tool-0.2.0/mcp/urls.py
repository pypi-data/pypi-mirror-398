from django.urls import path

from mcp import views

urlpatterns = [
    path("mcp/replace", views.ReplaceAPIView.as_view(), name="mcp-replace"),
]
