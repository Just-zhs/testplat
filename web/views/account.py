from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from web.forms.account import RegisterModelForm, SendSmsForm

def register(request):
    if request.method == 'GET':
        form = RegisterModelForm()
        return render(request, 'register.html', {'form': form})

    print(request.POST)
    return JsonResponse({})


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
