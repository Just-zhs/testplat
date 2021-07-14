from django.urls import path, re_path

from web.views import account, home, project

urlpatterns = [
    path('register/', account.register, name='register'),
    re_path(r'^login/$', account.login, name='login'),
    path('login/sms/', account.login_sms, name='login_sms'),
    path('image/code/', account.image_code, name='image_code'),
    path('send/sms/', account.send_sms, name='send_sms'),
    path('index/', home.index, name='index'),
    path('logout/', account.logout, name='logout'),
    #   项目管理
    path('project/list', project.project_list, name='project_list'),

]
