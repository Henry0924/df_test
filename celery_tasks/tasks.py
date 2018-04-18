from celery import Celery
from django.conf import settings
from django.core.mail import send_mail
import os
import django

app = Celery('celery_tasks.tasks', broker='redis://127.0.0.1:6379/8')

# django设置初始化
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "df_test.settings")
django.setup()


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

