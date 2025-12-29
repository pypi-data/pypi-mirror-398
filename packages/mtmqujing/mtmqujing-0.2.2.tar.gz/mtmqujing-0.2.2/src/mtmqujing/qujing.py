import re

import requests
try:
    import aiohttp
except ImportError:
    aiohttp = None

from .exceptions import QujingInvokeError

from dataclasses import dataclass, field


def post_invoke_data_process(text: str):
    if text.startswith("Base64#"):
        datatype = "base64"
        data = text[7:]
    elif text.startswith("raw#"):
        datatype = "raw"
        data = text[4:]
    else:
        datatype = "raw"
        data = text
    return {"data": data, "dtype": datatype}


@dataclass
class URLModel:
    protocol: str = field(default="http")
    domain: str = field(default="localhost")
    port: int = field(default=61000)
    path: str = field(default="")
    url: str = field(init=False)

    def __post_init__(self):
        self.url = f"{self.protocol}://{self.domain}:{self.port}{self.path}"


class QujingTemplateAPI:
    def __init__(self, url: URLModel | str, timeout: int = 5, **kwargs):
        self.url = self._get_url(url)
        self.timeout = timeout
        self.kwargs = kwargs
    
    def _get_url(self, url: URLModel | str):
        if isinstance(url, str):
            return url
        if isinstance(url, URLModel):
            return url.url
        raise ValueError(f"Invalid URL type: {type(url)}")

    def _get_kwargs(self, **kwargs):
        _kwargs = self.kwargs.copy()
        _kwargs.setdefault("timeout", self.timeout)
        _kwargs.update(kwargs)
        return _kwargs

class QujingConfigAPI(QujingTemplateAPI):  
    """配置API"""
    def get_pid(self, packages: list, **kwargs):
        url = self.url + "/manualguid"
        kwargs = self._get_kwargs(**kwargs)
        resp = requests.get(url, **kwargs)
        ports = {package: re.findall(f"<td>{package}</td>.*?<td>(.*?)</td>", resp.text, re.S) for package in packages}
        ports = {package: int(port[0]) for package, port in ports.items() if len(port)}
        return ports

    def set_app(self, packages: list, **kwargs):
        url = self.url + "/settargetapp"
        kwargs = self._get_kwargs(**kwargs)
        resp = requests.get(url, params=packages, **kwargs)
        return resp.status_code == 200
    

class QujingInvokeAPI(QujingTemplateAPI):
    """调用API"""
    def invoke(self, data: dict, **kwargs):
        url = self.url + "/invoke"
        kwargs = self._get_kwargs(**kwargs)
        try:
            resp = requests.post(url, data=data, **kwargs)
        except Exception as e:
            raise QujingInvokeError({"code": 500, "data": data, "error": str(e), "type": "error"})
        return post_invoke_data_process(resp.text.strip())

class AsyncQujingInvokeAPI(QujingTemplateAPI):
    """异步调用API"""
    async def invoke(self, data: dict, **kwargs):
        url = self.url + "/invoke"
        kwargs = self._get_kwargs(**kwargs)
        timeout = aiohttp.ClientTimeout(total=kwargs.pop("timeout", 5))
        
        try:
            async with aiohttp.ClientSession(timeout=timeout, **kwargs) as session:
                async with session.post(url, data=data) as resp:
                    text = await resp.text()
        except Exception as e:
            raise QujingInvokeError({"code": 500, "data": data, "error": str(e), "type": "error"})
        return post_invoke_data_process(text.strip())
