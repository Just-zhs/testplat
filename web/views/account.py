from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render

from web.forms.account import RegisterModelForm, SendSmsForm, LoginSMSForm


def register(request):
    if request.method == 'GET':
        form = RegisterModelForm()
        return render(request, 'register.html', {'form': form})

    form = RegisterModelForm(request.POST)
    if form.is_valid():
        # 验证通过，写入数据库(密码要是密文）
        form.save()
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
        return render(request,'login_sms.html',{'form':form})
    else:
        form = LoginSMSForm(request.POST)
        if form.is_valid():
            # 用户输入正确，登录成功
            user_object = form.cleaned_data['mobile_phone']
            # todo：把user_object中的用户信息放入session
            print(user_object)
            return JsonResponse({"status":True,'data':"/index/"})
        return JsonResponse({"status":False,'error': form.errors})