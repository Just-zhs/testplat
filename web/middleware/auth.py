import datetime

from django.shortcuts import redirect
from django.utils.deprecation import MiddlewareMixin

from web import models

class Tracer():
    def __init__(self):
        self.user = None
        self.price_policy = None

class AuthMiddleware(MiddlewareMixin):
    def process_request(self, request):
        """
        如果用户已登录，则reques中复制
        :param request:
        :return:
        """
        request.tracer = Tracer()
        user_id = request.session.get('user_id', 0)
        user_object = models.UserInfo.objects.filter(id=user_id).first()
        # tracer是自定义的写什么都行
        request.tracer.user = user_object

        # 白名单界面
        from django.conf import settings
        """
        1、获取当前URL
        2、检查URL是否在白名单中
        """
        # 中间件里return为空表示继续
        if request.path_info in settings.WHITE_REGEX_URL_LIST:
            return

        # 检查用户是否已登录，已登录则继续，未登录返回登录界面
        if not request.tracer.user:
            return redirect('login')

        # 登录成功之后，访问后台管理时获取当前额度
        # 方式一 免费额度在交易记录中存储
        _object = models.Transaction.objects.filter(user=user_object, status=2).order_by('-id').first()
        current_datetime = datetime.datetime.now()
        if _object.end_datetime and _object.end_datetime < current_datetime:
            _object = models.Transaction.objects.filter(user=user_object, status=2,price_policy__category=1).first()

        # 过期
        request.tracer.price_policy = _object.price_policy
        # 方式二 免费额度在配置文件中存储
