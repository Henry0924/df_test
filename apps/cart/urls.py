from django.conf.urls import url
from apps.cart.views import CartAddView, CartInfoView

urlpatterns = [
    url(r'^show_cart', CartInfoView.as_view(), name='cart'),
    url(r'^add$', CartAddView.as_view(), name='add'),

]
