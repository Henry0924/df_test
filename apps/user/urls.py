from django.conf.urls import url
from apps.user import views
from apps.user.views import RegisterView, ActiveView, LoginView

urlpatterns = [
    url(r'^register$', RegisterView.as_view(), name='register'),
    url(r'^login$', LoginView.as_view(), name='login'),
    url(r'^active/(?P<token>.*)$', ActiveView.as_view(), name='active'),
    url(r'^user_center_info$', views.user_center_info, name='user_center_info'),
    url(r'^user_center_order$', views.user_center_order, name='user_center_order'),
    url(r'^user_center_site$', views.user_center_site, name='user_center_site'),
]
