from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.views.generic import View
from apps.user.models import User
from django.conf import settings
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired
from django.http import HttpResponse
from django.core.mail import send_mail
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
        if not all([username, password, email]):
            return render(request, 'user/register.html', {'errmsg': '数据不完整'})
        if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'user/register.html', {'errmsg': '邮箱格式不正确'})
        if allow != 'on':
            return render(request, 'user/register.html', {'errmsg': '请同意协议'})

        # 检验用户名是否重复
        try:
            user_exist = User.objects.get(username=username)
        except User.DoesNotExist:
            # 用户名不存在
            user_exist = None
        else:
            return render(request, 'user/register.html', {'errmsg': '用户名已存在'})

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
        subject = '天天生鲜欢迎信息'
        message = ''
        sender = settings.EMAIL_FROM
        receiver = [email]
        html_message = '<h1>%s,欢迎您成为天天生鲜注册会员</h1>' \
                       '请点击下面链接激活您的账户<br/>' \
                       '<a href="http://127.0.0.1:8000/user/active/%s">http://127.0.0.1:8000/user/active/%s</a>'\
                       %(username, token, token)
        send_mail(subject, message, sender, receiver, html_message=html_message)

        return redirect(reverse('apps.goods:index'))


class ActiveView(View):
    """用户激活"""
    def get(self, request, token):
        """进行用户激活"""
        # 进行解密， 获取要激活的用户信息
        serializer = Serializer(settings.SECRET_KEY, 3600)
        try:
            info = serializer.loads(token)
            # 获取待激活用户的id
            user_id = info['confirm']
            # 根据id获取用户信息
            user = User.objects.get(id=user_id)
            user.is_active = 1
            user.save()
            # 跳转到登陆页面
            return redirect(reverse('apps.user:login'))
        except SignatureExpired as e:
            # 激活链接已过期
            return HttpResponse('激活链接已过期')


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
