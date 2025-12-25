# -*- coding: utf-8 -*-
"""
# ---------------------------------------------------------------------------------------------------------
# ProjectName:  http-helper
# FileName:     async_proxy.py
# Description:  客户端异步代理
# Author:       ASUS
# CreateDate:   2025/11/24
# Copyright ©2011-2025. Hunan xxxxxxx Company limited. All rights reserved.
# ---------------------------------------------------------------------------------------------------------
"""
import json
import aiohttp
import asyncio
from yarl import URL
from ..utils.log import logger
from typing import Any, Dict, Optional
from ..utils.http_execption import HttpClientError
from ..utils.reponse_handle_utils import get_html_title


class HttpClientFactory:
    __retry: int = 0

    def __init__(
            self,
            protocol: str = "https",
            domain: str = "api.weixin.qq.com",
            timeout: int = 10,
            retry: int = 0,
            enable_log: bool = False,
            cookie_jar: Optional[aiohttp.CookieJar] = None,
            playwright_state: Dict[str, Any] = None
    ):
        self.base_url = "://".join([protocol, domain])
        self.protocol = protocol
        self.domain = domain
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.__retry = retry
        self.enable_log = enable_log
        self.cookie_jar = cookie_jar
        self.playwright_state = playwright_state
        self.session = aiohttp.ClientSession(timeout=self.timeout, cookie_jar=cookie_jar)
        if playwright_state:
            self._load_playwright_cookies_to_aiohttp(playwright_state)
        self.valid_methods = {"get", "post", "put", "delete"}

    def _load_playwright_cookies_to_aiohttp(self, playwright_state: Dict[str, Any]):
        for ck in playwright_state.get("cookies", []):
            name = ck["name"]
            value = ck["value"]
            domain = ck["domain"]
            path = ck.get("path", "/")

            # aiohttp 要求 domain 不能以 . 开头
            if domain.startswith("."):
                domain = domain[1:]

            # 设置 cookie
            self.session.cookie_jar.update_cookies(
                {name: value},
                response_url=URL(f"{self.protocol}://{domain}{path}")
            )

    async def request(
            self,
            method: str,
            url: str,
            *,
            params: Dict[str, Any] = None,
            json_data: Any = None,
            data: Any = None,
            headers: Dict[str, str] = None,
            is_end: bool = True
    ) -> Any:

        method = method.lower().strip()
        if method not in self.valid_methods:
            raise HttpClientError(f"Invalid Request method: {method}")

        full_url = f"{self.base_url}{url}"

        # 重试机制
        attempts = self.__retry + 1
        for attempt in range(1, attempts + 1):
            try:
                if self.enable_log:
                    logger.debug(f"{method.upper()} Request {full_url} attempt {attempt}")

                async with self.session.request(
                        method=method,
                        url=full_url,
                        params=params or None,
                        json=json_data,
                        data=data,
                        headers=headers,
                ) as resp:

                    # 非 2xx 抛异常
                    if resp.status >= 400:
                        raise HttpClientError(f"Response status {resp.status} Error: {await resp.text()}")

                    # 检查响应的 Content-Type
                    content_type = resp.headers.get("Content-Type", "")

                    # 尝试 JSON 解码
                    try:
                        # 如果 Content-Type 是 text/json，手动解析 JSON
                        if "text/json" in content_type:
                            json_data = await resp.text()  # 获取响应文本
                            # 手动解析 JSON
                            json_data = json.loads(json_data)
                        elif "application/json" in content_type:
                            json_data = await resp.json()
                        elif "text/html" in content_type:
                            # 纯文本类型
                            json_data = dict(code=resp.status, message=get_html_title(html=await resp.text()),
                                             data=await resp.text())
                        else:
                            # 其他类型，默认视为二进制内容
                            content = await resp.content.readany()
                            content = content.decode('utf-8')
                            json_data = dict(code=resp.status, message=get_html_title(html=content), data=content)
                        if is_end is True:
                            await self.session.close()
                        return json_data
                    except aiohttp.ContentTypeError as e:
                        raise HttpClientError(f"Response parse error: {e}")

            except Exception as e:
                if attempt == attempts:
                    raise HttpClientError(f"Request failed after {attempts} attempts: {e}")
                await asyncio.sleep(1 * attempt)  # 递增式重试间隔
        if is_end is True and self.session:
            await self.session.close()

    async def close(self):
        if self.session:
            await self.session.close()
