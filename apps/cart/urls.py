from django.conf.urls import url
from apps.cart.views import CartAddView, CartInfoView, CartUpdateView, CartDeleteView

urlpatterns = [
    url(r'^show_cart', CartInfoView.as_view(), name='cart'),
    url(r'^add$', CartAddView.as_view(), name='add'),
    url(r'update$', CartUpdateView.as_view(), name='update'),
    url(r'delete$', CartDeleteView.as_view(), name='delete'),

]
