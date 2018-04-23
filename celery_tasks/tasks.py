from celery import Celery
from django.conf import settings
from django.core.mail import send_mail
from django.template import loader
import os
import django

# django设置初始化
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "df_test.settings")
django.setup()

from apps.goods.models import GoodsType, IndexTypeGoodsBanner, IndexGoodsBanner, IndexPromotionBanner

app = Celery('celery_tasks.tasks', broker='redis://127.0.0.1:6379/8')


@app.task
def send_register_active_mail(to_email, username, token):
    """发送激活邮件"""
    # 准备邮件内容
    # 1.邮件标题
    subject = '天天生鲜'
    # 2.邮件内容
    message = ''
    # 3.发件人
    sender = settings.EMAIL_FROM
    # 4.收件人列表
    receiver = [to_email]
    # 5.html邮件内容
    html_message = '<h1>%s, 欢迎您注册天天生鲜会员</h1><br/>' \
                   '请点击下面的激活链接激活您的账户' \
                   '<a href="http://127.0.0.1:8002/user/active/%s">http://127.0.0.1:8002/user/active/%s</a>'\
                   % (username, token, token)
    # 发送邮件
    send_mail(subject, message, sender, receiver, html_message=html_message)


@app.task
def generate_static_index_html():
    """生成首页的静态文件"""

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

    # 准备上下文模板
    context = {'types': types,
               'goods_banner': goods_banner,
               'promotion_banner': promotion_banner,
               }
    # 加载模板
    temp = loader.get_template('goods/static_index.html')
    # 渲染模板文件
    static_index_html = temp.render(context)

    # 准备静态文件路径
    save_path = os.path.join(settings.BASE_DIR, 'static/index.html')

    # 写入静态文件
    with open(save_path, 'w') as f:
        f.write(static_index_html)

