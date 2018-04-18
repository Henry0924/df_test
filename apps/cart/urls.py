from django.conf.urls import include, url
from apps.cart import views

urlpatterns = [
    url(r'^cart$', views.cart, name='cart'),

]
