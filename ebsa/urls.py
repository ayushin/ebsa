"""ebsa URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Import the include() function: from django.conf.urls import url, include
    3. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from django.conf.urls import url
from django.contrib import admin
import ebsa.views

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^statement/(?P<account>[a-zA-Z0-9]+)/(?P<datefrom>\d{2,4}-\d{1,2}-\d{1,2})/(?P<dateto>\d{2,4}-\d{1,2}-\d{1,2})', ebsa.views.account_statement),
    url(r'^statement/(?P<account>[a-zA-Z0-9]+)/(?P<datefrom>\d{2,4}-\d{1,2}-\d{1,2})', ebsa.views.account_statement),
    url(r'^statement/(?P<account>[a-zA-Z0-9]+)', ebsa.views.account_statement),
    url(r'^statement/', ebsa.views.account_list),
    url(r'^ofx', ebsa.views.ofx_connect),
]
