from django.shortcuts import render, redirect
from django.views.generic import View
from django.http import JsonResponse
from django_redis import get_redis_connection
from apps.goods.models import GoodsSKU
from utils.mixin import LoginRequiredMixin


# Create your views here.
class CartAddView(View):
    def post(self, request):
        """添加购物车记录"""
        # 获取登录的用户
        user = request.user
        # 获取数据
        sku_id = request.POST.get('sku_id')
        count = request.POST.get('count')
        # 校验数据
        if not user.is_authenticated():
            return JsonResponse({'res': 0, 'errmsg': '请先登录'})

        if not all([sku_id, count]):
            return JsonResponse({'res': 1, 'errmsg': '数据不完整'})

        try:
            count = int(count)
        except Exception as e:
            return JsonResponse({'res': 2, 'errmsg': '商品数量不正确'})

        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            return JsonResponse({'res': 3, 'errmsg': '该商品不存在'})

        # 添加购物车数据
        conn = get_redis_connection('default')
        cart_key = 'cart_%d' % user.id
        cart_count = conn.hget(cart_key, sku_id)
        if cart_count:
            count += int(cart_count)
        if count > sku.stock:
            return JsonResponse({'res': 4, 'errmsg': '商品库存不足'})

        conn.hset(cart_key, sku_id, count)
        # 获取购物车总条目
        total_count = conn.hlen(cart_key)

        # 返回应答
        return JsonResponse({'res': 5, 'total_count': total_count, 'msg': '添加成功'})


class CartInfoView(LoginRequiredMixin, View):
    def get(self, request):
        """显示购物车页面"""
        user = request.user
        # 从redis里获取购物车数据
        conn = get_redis_connection('default')
        cart_key = 'cart_%d' % user.id
        skus_dict = conn.hgetall(cart_key)
        # 获取sku_id 和 count
        total_count = 0
        total_price = 0
        skus = []
        for sku_id, count in skus_dict.items():
            sku = GoodsSKU.objects.get(id=sku_id)
            # 小计
            amount = sku.price * int(count)
            # 总商品数
            total_count += int(count)
            # 总价格
            total_price += amount
            sku.amount = amount
            sku.count = int(count)
            skus.append(sku)

        # 准备上下文
        context = {'skus': skus, 'total_count': total_count, 'total_price': total_price}

        return render(request, 'cart/cart.html', context)


class CartUpdateView(View):
    def post(self, request):
        """更新购物车数据"""
        user = request.user
        if not user.is_authenticated():
            return JsonResponse({'res': 0, 'errmsg': '请先登录'})
        # 获取数据
        sku_id = request.POST.get('sku_id')
        count = request.POST.get('count')

        # 校验数据
        if not all([sku_id, count]):
            return JsonResponse({'res': 1, 'errmsg': '数据不完整'})
        try:
            count = int(count)
        except Exception as e:
            return JsonResponse({'res': 2, 'errmsg': '商品数量不正确'})

        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            return JsonResponse({'res': 3, 'errmsg': '该商品不存在'})

        # 更新购物车数据
        conn = get_redis_connection('default')
        cart_key = 'cart_%d' % user.id
        if count > sku.stock:
            return JsonResponse({'res': 4, 'errmsg': '商品库存不足'})
        conn.hset(cart_key, sku_id, count)

        # 获取商品总件数
        total = 0
        vals = conn.hvals(cart_key)
        for val in vals:
            total += int(val)

        # 返回应答
        return JsonResponse({'res': 5, 'total': total, 'msg': '更新成功'})


class CartDeleteView(View):
    def post(self, request):
        """删除购物车记录"""
        user = request.user
        if not user.is_authenticated():
            return JsonResponse({'res': 0, 'errmsg': '请先登录'})
        # 获取数据
        sku_id = request.POST.get('sku_id')

        # 校验数据
        if not sku_id:
            return JsonResponse({'res': 1, 'errmsg': '数据不完整'})

        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            return JsonResponse({'res': 2, 'errmsg': '商品不存在'})

        # 删除购物车数据
        conn = get_redis_connection('default')
        cart_key = 'cart_%d' % user.id
        conn.hdel(cart_key, sku_id)

        # 获取商品总件数
        total = 0
        vals = conn.hvals(cart_key)
        for val in vals:
            total += int(val)

        # 返回应答
        return JsonResponse({'res': 3, 'total': total, 'msg': '删除成功'})

