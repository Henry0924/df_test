from django.shortcuts import render
from django.views.generic import View
from apps.goods.models import GoodsType, IndexGoodsBanner, IndexTypeGoodsBanner, IndexPromotionBanner
from django_redis import get_redis_connection


# Create your views here.
class IndexView(View):
    def get(self, request):
        """显示首页"""
        # 1.获取所有商品种类
        types = GoodsType.objects.all()
        # 2.获取首页轮播图片
        goods_banner = IndexGoodsBanner.objects.all().order_by('index')
        # 3.获取首页广告图片
        promotion_banner = IndexPromotionBanner.objects.all().order_by('index')
        # 4.获取每个种类的商品图片和文字信息
        for type in types:
            # 获取每个种类的商品图片信息
            goods_imgs = IndexTypeGoodsBanner.objects.filter(type=type, display_type=1)
            # 获取每个种类的商品文字信息
            goods_names = IndexTypeGoodsBanner.objects.filter(type=type, display_type=0)

            type.goods_imgs = goods_imgs
            type.goods_names = goods_names
        # 5.获取购物车的数目
        cart_count = 0
        if request.user.is_authenticated():
            conn = get_redis_connection('default')
            cart_key = 'cart_%d' % request.user.id
            cart_count = conn.hlen(cart_key)

        # 准备上下文模板
        content = {'types': types,
                   'goods_banner': goods_banner,
                   'promotion_banner': promotion_banner,
                   'cart_count': cart_count}
        # 使用上下文模板
        return render(request, 'goods/index.html', content)


def index(request):
    return render(request, 'goods/index.html')


def goods_list(request):
    return render(request, 'goods/list.html')


def detail(request):
    return render(request, 'goods/detail.html')