from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.views.generic import View
from apps.user.models import User, Address, DefaultAddress
from django.conf import settings
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from celery_tasks.tasks import send_register_active_mail
from utils.mixin import LoginRequiredMixin
from django_redis import get_redis_connection
from apps.goods.models import GoodsSKU
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
        # 判断用户是否已经登录
        if request.user.is_authenticated():
            return redirect(reverse('apps.goods:index'))
        else:
            if 'username' in request.COOKIES:
                username = request.COOKIES['username']
                checked = 'checked'
            else:
                username = ''
                checked = ''
        return render(request, 'user/login.html', {'username': username, 'checked': checked})

    def post(self, request):
        """用户登录"""
        # 获取用户名和密码
        username = request.POST.get('username')
        password = request.POST.get('pwd')
        remember = request.POST.get('remember')

        # 数据校验
        if not all([username, password]):
            return render(request, 'user/login.html', {'errmsg': '请填写用户名和密码'})

        # 登录校验
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                # 记住用户的登录状态
                login(request, user)
                next_url = request.GET.get('next', reverse('apps.goods:index'))
                response = redirect(next_url)
                if remember == 'on':
                    response.set_cookie('username', username, 7*24*3600)
                else:
                    response.delete_cookie('username')
                return response
            else:
                return render(request, 'user/login.html', {'errmsg': '请先激活你的账号'})
        else:
            return render(request, 'user/login.html', {'errmsg': '用户名或密码错误'})


class LogOutView(View):
    """退出登录"""
    def get(self, request):
        logout(request)
        return redirect(reverse('apps.goods:index'))


class UserInfoView(LoginRequiredMixin, View):
    """用户中心"""
    def get(self, request):
        """显示用户中心页面"""
        # 有默认地址，则显示默认地址
        # user = request.user  # 获取当前登录的用户对象
        # try:
        #     address = Address.objects.get(user=user, is_default=True)
        # except Address.DoesNotExist:
        #     address = None
        address = Address.objects.get_default_address(request)
        # 获取用户历史浏览记录
        conn = get_redis_connection('default')
        history_key = 'history_%d' % request.user.id
        sku_ids = conn.lrange(history_key, 0, 4)
        goods_list = []
        for id in sku_ids:
            goods = GoodsSKU.objects.get(id=id)
            goods_list.append(goods)

        return render(request, 'user/user_center_info.html', {'page': 'user', 'address': address,
                                                              'goods_list': goods_list})


class UserOrderView(LoginRequiredMixin, View):
    """用户中心"""
    def get(self, request):
        """显示全部订单页面"""
        return render(request, 'user/user_center_order.html', {'page': 'order'})


class AddressView(LoginRequiredMixin, View):
    """用户中心"""
    def get(self, request):
        """显示收货地址页面"""
        # 有默认地址，则显示默认地址
        # user = request.user  # 获取当前登录的用户对象
        # try:
        #     address = Address.objects.get(user=user, is_default=True)
        # except Address.DoesNotExist:
        #     address = None
        address = Address.objects.get_default_address(request)
        return render(request, 'user/user_center_site.html', {'page': 'address', 'address': address})

    def post(self, request):
        """添加收货地址"""
        # 获取收货地址信息
        receiver = request.POST.get('receiver')
        addr = request.POST.get('addr')
        zip_code = request.POST.get('zip_code')
        phone = request.POST.get('phone')

        # 校验地址信息
        if not all([receiver, addr, phone]):
            return render(request, 'user/user_center_site.html', {'errmsg': '收货地址信息不完整'})
        if not re.match(r'^1[3|4|5|7|8][0-9]{9}$', phone):
            return render(request, 'user/user_center_site.html', {'errmsg': '电话号码格式不正确'})

        # 添加收货地址
        # 判断是否有默认地址
        user = request.user  # 获取当前登录的用户对象
        try:
            address = Address.objects.get(user=user, is_default=True)
        except Address.DoesNotExist:
            address = None

        if address:
            is_delete = False
        else:
            is_delete = True

        Address.objects.create(user=user,
                               receiver=receiver,
                               addr=addr,
                               zip_code=zip_code,
                               phone=phone,
                               is_default=is_delete)
        # 返回应答
        return redirect(reverse('apps.user:address'))

