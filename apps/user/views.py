from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.views.generic import View
from apps.user.models import User
from django.conf import settings
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired
from django.http import HttpResponse
from django.core.mail import send_mail
from celery_tasks.tasks import send_register_active_mail
import re


# Create your views here.
class RegisterView(View):
    """注册"""

    def get(self, request):
        """显示注册页面"""
        return render(request, 'user/register.html')

    def post(self, request):
        """进行注册处理"""
        # 获取注册信息
        username = request.POST.get('user_name')
        password = request.POST.get('pwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')

        # 进行数据校验
        # 1.校验注册信息是否完整
        if not all([username, password, email, allow]):
            return render(request, 'user/register.html', {'errmsg': '请将注册信息填写完整'})

        # 2.校验邮箱格式是否合法
        if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'user/register.html', {'errmsg': '邮箱格式不正确'})

        # 3.校验是否同意协议
        if allow != 'on':
            return render(request, 'user/register.html', {'errmsg': '请同意注册协议'})

        # 检验用户名是否重复
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = None
        else:
            return HttpResponse('此用户名已经注册过')

        # 进行业务处理：进行用户注册
        user = User.objects.create_user(username, email, password)
        user.is_active = 0
        user.save()

        # 加密用户的身份信息，生成激活token
        serializer = Serializer(settings.SECRET_KEY, 3600)
        info = {'confirm': user.id}
        token = serializer.dumps(info)
        token = token.decode()

        # 发送邮件
        send_register_active_mail.delay(email, username, token)
        # 返回响应
        return redirect(reverse('apps.goods:index'))


class ActiveView(View):
    """用户激活"""
    def get(self, request, token):
        # 解密激活链接token，获取用户id
        serializer = Serializer(settings.SECRET_KEY, 3600)
        try:
            info = serializer.loads(token)
            user_id = info['confirm']
            # 根据用户id获取用户信息
            user = User.objects.get(id=user_id)
            user.is_active = 1
            user.save()
            # 激活成功返回登录页面
            return redirect(reverse('apps.user:login'))
        except SignatureExpired as e:
            return HttpResponse('激活链接已经过期，请重新发送')


class LoginView(View):
    """登录"""
    def get(self, request):
        """显示登录页面"""
        return render(request, 'user/login.html')


def user_center_info(request):
    return render(request, 'user/user_center_info.html')


def user_center_order(request):
    return render(request, 'user/user_center_order.html')


def user_center_site(request):
    return render(request, 'user/user_center_site.html')
