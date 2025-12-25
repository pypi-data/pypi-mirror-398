from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest
from dotenv import load_dotenv, find_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings


load_dotenv(find_dotenv(usecwd=True))


class SmsSettings(BaseSettings):
    """统一放在 .env 中管理"""
    ali_sms_access_key_id:     str = Field(..., env='ALI_SMS_ACCESS_KEY_ID')
    ali_sms_access_key_secret: str = Field(..., env='ALI_SMS_ACCESS_KEY_SECRET')
    ali_sms_sign_name:         str = Field('', env='ALI_SMS_SIGN_NAME')
    ali_sms_template_code:     str = Field('', env='ALI_SMS_TEMPLATE_CODE')
    ali_sms_region_id:     str = Field('cn-hangzhou', env='ALI_SMS_REGION_ID')


class AliSmsClient:

    _sms_settings = SmsSettings()

    """线程安全：每个请求新建 AcsClient 即可"""
    def __init__(self):
        self.client = AcsClient(
            self._sms_settings.ali_sms_access_key_id,
            self._sms_settings.ali_sms_access_key_secret,
            'cn-hangzhou'
        )

    def do_send_code(self, phone: str, code: str, ali_sms_sign_name: str = None, ali_sms_template_code: str = None) -> bool:
        req = CommonRequest(domain='dysmsapi.aliyuncs.com',
                            version='2017-05-25',
                            action_name='SendSms')
        req.set_method('POST')
        req.set_protocol_type('https')
        req.add_query_param('PhoneNumbers', phone)
        req.add_query_param('SignName', self._sms_settings.ali_sms_sign_name if ali_sms_sign_name is None else ali_sms_sign_name)
        req.add_query_param('TemplateCode', self._sms_settings.ali_sms_template_code if ali_sms_template_code is None else ali_sms_template_code)
        req.add_query_param('TemplateParam', f'{{"code":"{code}"}}')

        try:
            self.client.do_action_with_exception(req)
            return True
        except Exception as e:
            # 记录日志或告警
            print('SMS send error:', e)
            return False

    @classmethod
    def send_code(cls, phone: str, code: str, ali_sms_sign_name: str = None, ali_sms_template_code: str = None) -> bool:
        client = AliSmsClient()
        return client.do_send_code(phone=phone, code=code, ali_sms_sign_name=ali_sms_sign_name, ali_sms_template_code=ali_sms_template_code)
