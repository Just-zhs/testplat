# 注册表单
import random

from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django_redis import get_redis_connection

from utils.tencent.sms import send_sms_single
from web import models

from utils import encrypt

from web.forms.bootstrap import BootStrapForm


class RegisterModelForm(BootStrapForm, forms.ModelForm):
    # form里重写字段
    mobile_phone = forms.CharField(label='手机号',
                                   validators=[RegexValidator(r'^1([358])\d{9}$', '手机号格式错误'), ])

    password = forms.CharField(label='密码',
                               min_length=8,
                               max_length=64,
                               error_messages={'min_length': "密码长度不能小于8个字符",
                                               'max_length': '密码长度不能大于64个字符',
                                               },
                               widget=forms.PasswordInput(attrs={'placeholder': '请输入密码'}))

    confirm_password = forms.CharField(label='重复密码',
                                       min_length=8,
                                       max_length=64,
                                       error_messages={
                                           'min_length': "重复密码长度不能小于8个字符",
                                           'max_length': '重复密码长度不能大于64个字符',
                                       },
                                       widget=forms.PasswordInput(attrs={'placeholder': '请重复输入密码'}))

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

    # 钩子函数，验证ajax传过来的值
    def clean_username(self):
        username = self.cleaned_data['username']

        exists = models.UserInfo.objects.filter(username=username).exists()
        if exists:
            return ValidationError('用户名已存在')
        return username

    def clean_email(self):
        email = self.cleaned_data['email']

        exists = models.UserInfo.objects.filter(email=email).exists()
        if exists:
            return ValidationError('邮箱已存在')
        return email

    def clean_password(self):
        pwd = self.cleaned_data['password']
        # 加密返回
        return encrypt.md5(pwd)

    def clean_confirm_password(self):
        pwd = self.cleaned_data.get('password')
        confirm_pwd = encrypt.md5(self.cleaned_data['confirm_password'])
        if pwd != confirm_pwd:
            raise ValidationError('两次密码不一致')
        return confirm_pwd

    def clean_mobile_phone(self):
        mobile_phone = self.cleaned_data['mobile_phone']
        exists = models.UserInfo.objects.filter(mobile_phone=mobile_phone).exists()
        if exists:
            raise ValidationError('手机号已注册')
        return mobile_phone

    def clean_code(self):
        code = self.cleaned_data['code']
        # mobile_phone = self.cleaned_data['mobile_phone']
        # 手机号不存在没必要验证验证码
        mobile_phone = self.cleaned_data.get('mobile_phone')
        if not mobile_phone:
            return code

        conn = get_redis_connection()
        redis_code = conn.get(mobile_phone)
        if not redis_code:
            raise ValidationError('验证码失效或未发送，请重新发送')

        redis_str_code = redis_code.decode('utf-8')
        print(redis_code)
        if code.strip() != redis_str_code:
            raise ValidationError('验证码错误，请重新输入')
        return code


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

        # 校验手机号
        exists = models.UserInfo.objects.filter(mobile_phone=mobile_phone).exists()
        if tpl == 'login':
            if not exists:
                raise ValidationError('该手机号不存在，请重新注册')

        else:
        # 检验数据库中是否有手机号
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


class LoginSMSForm(BootStrapForm,forms.Form):
    mobile_phone = forms.CharField(label='手机号',
                                   validators=[RegexValidator(r'^1([358])\d{9}$', '手机号格式错误'), ])

    code = forms.CharField(label='验证码',
                           widget=forms.TextInput())

    def clean_mobile_phone(self):
        mobile_phone = self.cleaned_data['mobile_phone']
        # exists = models.UserInfo.objects.filter(mobile_phone=mobile_phone).exists()
        # 用first()直接获取到用户对象
        user_object = models.UserInfo.objects.filter(mobile_phone=mobile_phone).first()
        if not user_object:
            raise ValidationError('手机号不存在')

        return user_object

    def clean_code(self):
        code = self.cleaned_data['code']
        # mobile_phone = self.cleaned_data['mobile_phone']

        user_object = self.cleaned_data.get('mobile_phone')
        # 手机号不存在没必要验证验证码
        if not user_object:
            return code

        conn = get_redis_connection()
        redis_code = conn.get(user_object.mobile_phone)
        if not redis_code:
            raise ValidationError('验证码失效或未发送，请重新发送')

        redis_str_code = redis_code.decode('utf-8')
        print(redis_code)
        if code.strip() != redis_str_code:
            raise ValidationError('验证码错误，请重新输入')
        return code

class LoginForm(BootStrapForm,forms.Form):
    username = forms.CharField(label='邮箱或手机号',)
    password = forms.CharField(label='密码', widget=forms.PasswordInput(render_value=True))
    code = forms.CharField(label='图片验证码')

    def __init__(self, request, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request

    def clean_password(self):
        pwd = self.cleaned_data['password']
        # 加密返回
        return encrypt.md5(pwd)

    def clean_code(self):
        code = self.cleaned_data['code']
        session_code = self.request.session.get('image_code')
        if not session_code:
            raise ValidationError('验证码已过期，请重新获取')

        if code.upper() != session_code.upper():
            raise ValidationError('验证码输入错误')

        return code