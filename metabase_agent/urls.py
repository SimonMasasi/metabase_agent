"""
URL configuration for metabase_agent project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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
from django.urls import path
from urls.api_v1 import api_v1
from urls.api_v2 import api_v2
from ninja import NinjaAPI
from views.v1.license import license_router

admin.site.site_title = "Metabase Agent Admin"
admin.site.site_header = "Metabase Agent Admin"

# Create API for license/token status endpoints
api_license = NinjaAPI(version="2.0")
api_license.add_router("", license_router)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', api_v1.urls , name='api_v1'),
    path('api/v2/', api_v2.urls, name='api_v2'),
    path('api/', api_license.urls, name='api_license'),
]
