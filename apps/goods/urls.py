from django.conf.urls import include, url
from apps.goods import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^list$', views.goods_list, name='list'),
    url(r'^detail$', views.detail, name='detail'),
]
