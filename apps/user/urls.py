from django.conf.urls import url
from apps.user import views
from apps.user.views import RegisterView, ActiveView, LoginView, UserInfoView, UserOrderView, AddressView, LogOutView

urlpatterns = [
    url(r'^register$', RegisterView.as_view(), name='register'),
    url(r'^login$', LoginView.as_view(), name='login'),
    url(r'^active/(?P<token>.*)$', ActiveView.as_view(), name='active'),
    url(r'^logout$', LogOutView.as_view(), name='logout'),
    url(r'^$', UserInfoView.as_view(), name='user'),
    url(r'^order$', UserOrderView.as_view(), name='order'),
    url(r'^address$', AddressView.as_view(), name='address'),
]
