from django.conf.urls import include, url
from apps.goods import views
from apps.goods.views import IndexView

urlpatterns = [
    url(r'^$', IndexView.as_view(), name='index'),
    url(r'^list$', views.goods_list, name='list'),
    url(r'^detail$', views.detail, name='detail'),
]
