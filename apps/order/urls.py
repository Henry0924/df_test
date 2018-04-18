from django.conf.urls import include, url
from apps.order import views

urlpatterns = [
    url(r'^order$', views.order, name='order'),

]
