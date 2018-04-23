from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.views.generic import View
from apps.goods.models import GoodsType, IndexGoodsBanner, IndexTypeGoodsBanner, IndexPromotionBanner, GoodsSKU
from apps.order.models import OrderGoods
from django.core.cache import cache
from django.core.paginator import Paginator
from django_redis import get_redis_connection


# Create your views here.
class IndexView(View):
    def get(self, request):
        """显示首页"""
        context = cache.get('index_page_data')
        if context is None:
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
            # # 5.获取购物车的数目
            # cart_count = 0
            # if request.user.is_authenticated():
            #     conn = get_redis_connection('default')
            #     cart_key = 'cart_%d' % request.user.id
            #     cart_count = conn.hlen(cart_key)

            # 准备上下文模板
            context = {'types': types,
                       'goods_banner': goods_banner,
                       'promotion_banner': promotion_banner,
                       }
            cache.set('index_page_data', context, 3600)
        # 使用上下文模板
        return render(request, 'goods/index.html', context)


# list/type_id/page?sort=
class GoodsListView(View):
    def get(self, request, type_id, page):
        """显示商品列表页"""
        try:
            type = GoodsType.objects.get(id=type_id)
        except Exception as e:
            return redirect(reverse('apps.goods:index'))
        # 获取排序信息sort
        sort = request.GET.get('sort')
        sort_dict = {'default': '-id', 'price': 'price', 'hot': '-sales'}
        if sort in sort_dict:
            skus = GoodsSKU.objects.filter(type=type).order_by(sort_dict.get(sort))
        else:
            sort = 'default'
            skus = GoodsSKU.objects.filter(type=type).order_by('-id')
        # 分页
        paginator = Paginator(skus, 1)
        try:
            page = int(page)
        except Exception as e:
            page = 1
        if page > paginator.num_pages:
            page = 1
        page_skus = paginator.page(page)
        # 获取新品信息
        new_skus = GoodsSKU.objects.filter(type=type).order_by('-create_time')[:2]
        # 全部分类
        types = GoodsType.objects.all()

        # 准备上下文
        context = {'type': type, 'types': types, 'page_skus': page_skus, 'new_skus': new_skus, 'sort': sort}

        return render(request, 'goods/list.html', context)


class DetailView(View):
    def get(self, request, goods_id):
        """显示商品详情页"""
        # 获取商品对象
        try:
            sku = GoodsSKU.objects.get(id=goods_id)
        except Exception as e:
            # 商品不存在
            return redirect(reverse('apps.goods:index'))
        # 获取新品信息
        new_skus = GoodsSKU.objects.filter(type=sku.type).order_by('-create_time')[:2]
        # 获取评论信息
        sku_comments = OrderGoods.objects.filter(sku=sku).exclude(comment='')
        # 获取同类商品不同规格的信息
        same_spu_skus = GoodsSKU.objects.filter(goods=sku.goods).exclude(id=sku.id)
        # 全部商品种类
        types = GoodsType.objects.all()

        # 准备上下文
        context = {'sku': sku, 'new_skus': new_skus, 'types': types,
                   'sku_comments': sku_comments, 'same_spu_skus': same_spu_skus}
        # 记录用户浏览记录
        if request.user.is_authenticated():
            conn = get_redis_connection('default')
            history_key = 'history_%d' % request.user.id
            conn.lrem(history_key, 0, goods_id)
            conn.lpush(history_key, goods_id)
            conn.ltrim(history_key, 0, 4)

        return render(request, 'goods/detail.html', context)

