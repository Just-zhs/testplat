from django.utils.deprecation import MiddlewareMixin

from web import models


class AuthMiddleware(MiddlewareMixin):
    def process_request(self, request):
        """
        如果用户已登录，则reques中复制
        :param request:
        :return:
        """
        user_id = request.session.get('user_id', 0)
        user_object = models.UserInfo.objects.filter(id=user_id).first()
        # tracer是自定义的写什么都行
        request.tracer = user_object
