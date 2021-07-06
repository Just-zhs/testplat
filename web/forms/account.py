# 注册表单
import random

from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django_redis import get_redis_connection

from utils.tencent.sms import send_sms_single
from web import models


class RegisterModelForm(forms.ModelForm):
    # form里重写字段
    mobile_phone = forms.CharField(label='手机号', validators=[RegexValidator(r'^1([358])\d{9}$', '手机号格式错误'), ])
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


class SendSmsForm(forms.Form):
    mobile_phone = forms.CharField(label='手机号', validators=[RegexValidator(r'^(1[3|4|5|6|7|8|9])\d{9}$', '手机号格式错误'), ])

    def __init__(self, request, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request

    def clean_mobile_phone(self):
        """手机号验证的钩子函数"""
        mobile_phone = self.cleaned_data['mobile_phone']

        # 判断短信模板是否有问题
        tpl = self.request.GET.get('tpl')
        sms_template_id = settings.TENCENT_SMS_TEMPLATE.get(tpl)
        if not sms_template_id:
            raise ValidationError('短信模板错误')

        # 检验数据库中是否有手机号
        exists = models.UserInfo.objects.filter(mobile_phone=mobile_phone).exists()
        if exists:
            raise ValidationError('手机号已存在')

        # 发短信&写redis
        code = random.randrange(1000, 9999)
        sms = send_sms_single(mobile_phone, sms_template_id, [code, ])
        if sms['result'] != 0:
            raise ValidationError(f'短信发送失败,{sms["errmsg"]}')

        conn = get_redis_connection()
        conn.set(mobile_phone, code, ex=60)

        return mobile_phone
