from django.conf.urls import url
from apps.goods.views import IndexView, GoodsListView, DetailView

urlpatterns = [
    url(r'^index$', IndexView.as_view(), name='index'),
    url(r'^list/(?P<type_id>\d+)/(?P<page>\d+)$', GoodsListView.as_view(), name='list'),
    url(r'^detail/(?P<goods_id>\d+)$', DetailView.as_view(), name='detail'),
]
