from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.views.generic import View
from django_redis import get_redis_connection
from django.http import JsonResponse
from utils.mixin import LoginRequiredMixin
from apps.goods.models import GoodsSKU
from apps.user.models import Address
from apps.order.models import OrderGoods, OrderInfo
from datetime import datetime


# Create your views here.
class OrderPlaceView(LoginRequiredMixin, View):
    def post(self, request):
        """显示订单页"""
        user = request.user
        # 获取数据
        sku_ids = request.POST.getlist('sku_id')

        # 校验数据
        if not sku_ids:
            return redirect(reverse('apps.cart:cart'))
        # 获取订单中的商品信息
        conn = get_redis_connection('default')
        cart_key = 'cart_%d' % user.id
        skus = []
        # 总价和总件数
        total_count = 0
        total_price = 0
        for sku_id in sku_ids:
            try:
                sku = GoodsSKU.objects.get(id=sku_id)
            except:
                return redirect(reverse('apps.cart:cart'))
            # 商品数量
            count = conn.hget(cart_key, sku_id)
            count = int(count)
            sku.count = count
            # 商品小计
            amount = sku.price * count
            sku.amount = amount
            # 追加
            skus.append(sku)
            # 累加计算总价和总件数
            total_count += count
            total_price += amount

        # 获取收货地址
        addrs = Address.objects.filter(user=user)
        # 运费
        transit_price = 10
        # 实付款
        total_pay = total_price + transit_price

        # 将sku_ids变为字符串
        sku_ids = ','.join(sku_ids)
        # 准备上下文
        context = {'skus': skus, 'total_count': total_count, 'total_price': total_price,
                   'transit_price': transit_price, 'addrs': addrs, 'total_pay': total_pay, 'sku_ids': sku_ids}

        # 使用模板
        return render(request, 'order/place_order.html', context)


class OrderCommitView(View):
    def post(self, request):
        """提交订单"""
        user = request.user
        if not user.is_authenticated():
            return JsonResponse({'res': 0, 'errmsg': '请先登录'})
        # 获取数据
        sku_ids = request.POST.get('sku_ids')
        addr_id = request.POST.get('addr_id')
        pay_method = request.POST.get('pay_method')

        # 校验数据
        if not all([sku_ids, addr_id, pay_method]):
            return JsonResponse({'res': 1, 'errmsg': '数据不完整'})
        try:
            addr = Address.objects.get(id=addr_id)
        except Address.DoesNotExist:
            return JsonResponse({'res': 2, 'errmsg': '地址不存在'})
        if pay_method not in OrderInfo.PAY_METHOD.keys():
            return JsonResponse({'res': 3, 'errmsg': '支付方式不合法'})

        # 向df_order_info表中插入一条数据
        """
        order_id = models.CharField(max_length=128, primary_key=True, verbose_name='订单id')
        user = models.ForeignKey('user.User', verbose_name='用户')
        addr = models.ForeignKey('user.Address', verbose_name='地址')
        pay_method = models.SmallIntegerField(choices=PAY_METHOD_CHOICES, default=3, verbose_name='支付方式')
        total_count = models.IntegerField(default=1, verbose_name='商品数量')
        total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='商品总价')
        transit_price = models.DecimalField(max_digits=10, decimal_places=2,verbose_name='订单运费')
        order_status = models.SmallIntegerField(choices=ORDER_STATUS_CHOICES, default=1, verbose_name='订单状态')
        trade_no = models.CharField(max_length=128, default='', verbose_name='支付编号')

        """
        order_id = datetime.now().strftime('%Y%m%d%H%M%S') + str(user.id)
        total_count = 0
        total_price = 0
        transit_price = 10

        order = OrderInfo.objects.create(order_id=order_id,
                                         user=user,
                                         addr=addr,
                                         pay_method=pay_method,
                                         total_count=total_count,
                                         total_price=total_price,
                                         transit_price=transit_price)

        # 订单中有几种商品，向df_order_goods表中插入几条数据
        sku_ids = sku_ids.split(',')
        conn = get_redis_connection('default')
        cart_key = 'cart_%d' % user.id
        for sku_id in sku_ids:
            try:
                sku = GoodsSKU.objects.get(id=sku_id)
            except:
                return JsonResponse({'res': 4, 'errmsg': '商品不存在'})

            count = conn.hget(cart_key, sku_id)
            count = int(count)

            OrderGoods.objects.create(order=order,
                                      sku=sku,
                                      count=count,
                                      price=sku.price)
            # 累加计算总价和总件数
            total_count += count
            total_price += sku.price * count

            # 修改库存和销量
            sku.stock -= count
            sku.sales += count
            sku.save()

        # 更新df_order_info
        order.total_count = total_count
        order.total_price = total_price
        order.save()

        # 删除购物车中的对应记录
        conn.hdel(cart_key, *sku_ids)

        # 返回应答
        return JsonResponse({'res': 5, 'msg': '下单成功'})




