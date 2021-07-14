import datetime
import uuid

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect

from web import models
from web.forms.account import RegisterModelForm, SendSmsForm, LoginSMSForm, LoginForm


def register(request):
    if request.method == 'GET':
        form = RegisterModelForm()
        return render(request, 'register.html', {'form': form})

    form = RegisterModelForm(request.POST)
    if form.is_valid():
        # 验证通过，写入数据库(密码要是密文）
        # form.save()
        instance = form.save()
        # 创建交易
        policy_object = models.PricePolicy.objects.filter(category=1,title="个人免费版").first()
        models.Transaction.objects.create(
            status=2,
            order=str(uuid.uuid4()),
            user=instance,
            price_policy=policy_object,
            count=0,
            start_datetime=datetime.datetime.now()
        )

        return JsonResponse({'status': True, 'data': '/login/'})
    else:
        print(form.errors)

    return JsonResponse({'status': False, 'error': form.errors})


def send_sms(request):
    """发送短信"""
    # 'mobile_phone': ['123321'], 'tpl': ['register']}
    # mobile_phone = request.GET.get('mobile_phone')
    # tpl = request.GET.get('tpl')
    # sms_template_id = settings.TENCENT_SMS_TEMPLATE['tpl']
    print(request.GET)
    form = SendSmsForm(request, data=request.GET)
    # 只是检验手机号：非空,格式正确
    if form.is_valid():
        # 通过校验，发短信写redis
        return JsonResponse({'status': True})
    return JsonResponse({'status': False, 'error': form.errors})


def login_sms(request):
    """短信登录"""
    if request.method == 'GET':
        form = LoginSMSForm()
        return render(request, 'login_sms.html', {'form': form})
    else:
        form = LoginSMSForm(request.POST)
        if form.is_valid():
            # 用户输入正确，登录成功
            user_object = form.cleaned_data['mobile_phone']
            # todo：把user_object中的用户信息放入session
            print(user_object)
            return JsonResponse({"status": True, 'data': "/index/"})
        return JsonResponse({"status": False, 'error': form.errors})


def login(request):
    """用户名密码登录"""
    if request.method == "GET":
        form = LoginForm(request)
        return render(request, 'login.html', {'form': form})
    form = LoginForm(request, data=request.POST)
    if form.is_valid():
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        from django.db.models import Q
        user_object = models.UserInfo.objects.filter(Q(email=username) | Q(mobile_phone=username)).filter(
            password=password).first()
        if user_object:
            request.session['user_id'] = user_object.id
            request.session.set_expiry(60 * 60 * 24)
            return redirect('index')
        form.add_error('username', '用户名或密码错误')
    return render(request, 'login.html', {'form': form})

def logout(request):
    request.session.flush()
    return redirect('index')


def image_code(request):
    """生成验证码"""
    from utils.image_code import check_code
    image_object, code = check_code()
    # 写入session
    request.session['image_code'] = code
    # 修改session过期时间
    request.session.set_expiry(60)
    # 把图片的内容写入到内存stream
    from io import BytesIO
    stream = BytesIO()
    image_object.save(stream, 'png')

    return HttpResponse(stream.getvalue())
