from django.conf import settings
from django.core.validators import RegexValidator
from django.http import HttpResponse
from django.shortcuts import render

# Create your views here.
import random
from utils.tencent.sms import send_sms_single


def send_sms(request):
    "发送短信"
    tpl = request.GET.get('tpl')
    tpl_id = settings.TENCENT_SMS_TEMPLATE.get(tpl)
    if not tpl_id:
        return HttpResponse('模板不存在')
    else:
        code = random.randrange(1000, 9999)
        res = send_sms_single('15141166689', 1022791, [code, ])
        print(res)
        if res['result'] == 0:
            return HttpResponse('成功')
        else:
            return HttpResponse(f"失败{res['errmsg']}")


from django import forms
from app01 import models


# 注册表单
class RegisterModelForm(forms.ModelForm):
    # form里重写字段
    mobile_phone = forms.EmailField(label='手机号', validators=[RegexValidator(r'^1([358])\d{9}$', '手机号格式错误'), ])
    password = forms.CharField(label='密码',
                               widget=forms.PasswordInput(attrs={'placeholder': '请输入密码'}))
    confirm_password = forms.CharField(label='重复密码', widget=forms.PasswordInput(
        attrs={'placeholder': '请重复输入密码'}))
    code = forms.CharField(label='验证码',
                           widget=forms.TextInput())

    class Meta:
        model = models.UserInfo
        fields = ['username', 'email', 'password', 'confirm_password', 'mobile_phone', 'code']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['placeholder'] = f'请输入{field.label}'


def register(request):
    form = RegisterModelForm()
    return render(request, 'register.html', {'form': form})

import redis