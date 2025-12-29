import logging
import ssl
import asyncio
from functools import wraps
from urllib.parse import urlparse, parse_qs, urlencode

import httpx
import pyotp
from tenacity import retry, stop_after_attempt

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

logger.setLevel(logging.INFO)


def sync_and_async(async_func):
    """装饰器，使异步函数支持同步和异步调用。"""

    @wraps(async_func)
    def wrapper(*args, **kwargs):
        try:
            # 检查当前是否有运行的事件循环
            asyncio.get_running_loop()
            # 存在运行中的事件循环，返回协程对象，需用户await
            return async_func(*args, **kwargs)
        except RuntimeError:
            # 无事件循环，同步执行
            return asyncio.run(async_func(*args, **kwargs))

    return wrapper


class Yhlogin:
    retry_num = 1

    def __init__(self):
        self.UserAgent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0'

        # YHBI的SSL原因，需配置
        ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        ctx.options |= 0x4  # 启用 OP_LEGACY_SERVER_CONNECT
        self.transport = httpx.HTTPTransport(verify=ctx)
        self.async_transport = httpx.AsyncHTTPTransport(verify=ctx)

    @retry(stop=stop_after_attempt(retry_num))
    @sync_and_async
    async def login(self, username, password, otp_key, service, skip_ad=True):
        # 兼容之前某些已存在的代码做的转换
        if service.startswith('https://bigdata.yonghui.cn'):
            service = f'http://cas-prod.bigdata.yonghui.cn:7070/redirect?redirectUrl={service}'

        skip_ad_service = 'https://oa'
        target_url = service
        service = skip_ad_service if skip_ad else service
        headers = {'Content-Type': 'application/x-www-form-urlencoded', 'User-Agent': self.UserAgent}

        async with httpx.AsyncClient(transport=self.async_transport) as client:
            res = await client.get(url=target_url, headers=headers, follow_redirects=True)
            target_login_url = res.url.__str__()
            login_url = target_login_url.split('?')[0]
            # 使用跳过域网址
            if skip_ad:
                url = f'{login_url}?service={service}'
            else:
                url = target_login_url
            e1s1_data = {'flag': 1,
                         'username': username,
                         'password': password,
                         'phoneNum': None,
                         'captcha': None,
                         'sourceType': 1,
                         'execution': 'e2s1',
                         '_eventId': 'submit',
                         'geolocation': None}
            # 原因不明，就是要get，不然没办法登录
            await client.get(url=url, headers=headers)
            res = await client.post(url=url, headers=headers, data=e1s1_data, follow_redirects=True)
            res_text = res.text
            res_status_code = res.status_code
            # 如果是401则需要填otp
            if res_status_code == 200:
                pass
            elif res_status_code == 401:
                if res_text.find('id = "dynamicPassword"'):
                    dynamic_password = pyotp.TOTP(otp_key).now()
                    e1s2_data = {'flag': 1,
                                 'token': dynamic_password,
                                 'username': username,
                                 'password': None,
                                 'phoneNum': None,
                                 'captcha': None,
                                 'sourceType': 1,
                                 'execution': 'e2s2',
                                 '_eventId': 'submit',
                                 'geolocation': None}
                    res = await client.post(url=url, headers=headers, data=e1s2_data, follow_redirects=True)
                    res_status_code = res.status_code

            if res_status_code == 200:
                # 获取cookies
                cookies = client.cookies
                url = res.url
                if cookies:
                    self.cookies = cookies
                    self.url = url
                else:
                    raise ValueError('登录失败,未获取cookies')
            else:
                raise ValueError('登录失败')
