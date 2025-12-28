"""
URL configuration for svr project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

admin.site.site_header = _("Management Console")
admin.site.site_title = _("Management Console")
admin.site.index_title = _("Management Console")

urlpatterns = [
    path(
        '',
        TemplateView.as_view(template_name='dictionary/home.html'),
        name='home'
    ),
    path('admin/', admin.site.urls),
    path('replace/', include('dictionary.urls')),
    path('', include('api.urls')),
    path('', include('mcp.urls')),
]
