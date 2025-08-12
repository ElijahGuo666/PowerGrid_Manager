import json
# from fourA_api import fourA_login,fourA_get_dwglpt_asset_domain_session
from .iam_api import iam_login,iam_get_dwglpt_asset_domain_session
import pickle
import os
import aiohttp
import sys
import logging
import asyncio

logger = logging.getLogger(__name__)

# 检查cookie是否有效（即当前用户是否已登录资产域）
async def check_cookie_ok(cookies):
    """
    异步检查cookie是否有效
    Args:
        cookies: cookie字典
    Returns:
        bool: cookie是否有效
    """
    cj_new = aiohttp.CookieJar(unsafe=True)
    cj_new.update_cookies(cookies)
    async with aiohttp.ClientSession(cookie_jar=cj_new) as http:
        try:
            resp = await http.get("http://10.10.21.28/api/jadp/auth/currentUser")
        except aiohttp.ClientConnectorError as e:
            logger.error("网络链接错误，请检查网络。")
            logger.error(str(e))
            sys.exit(1)

        respdata = await resp.json(content_type=None)
        if resp.ok and respdata["state"] == 1:
            logger.info("已使用如下身份登录资产域:{}_{}".format(respdata["nameFullPath"],respdata["employeeName"]))
            return True
        return False
    
# 电网管理平台HTTP会话管理类
class DwglptHttp:
    """
    电网管理平台异步HTTP会话管理类
    提供自动登录、cookie持久化、会话管理等功能
    """
    def __init__(self):
        self._sess = None

    # 销毁HTTP会话
    async def http_destory(self):
        """
        销毁HTTP会话，释放资源
        """
        if self._sess != None:
            await self._sess.close()

    # 初始化HTTP会话，自动处理cookie获取与持久化
    async def http_init(self, username=None, password=None):
        """
        初始化HTTP会话
        自动处理登录、cookie获取、持久化等流程
        Args:
            username: 用户名（可选）
            password: 密码（可选）
        """
        need_refresh_http = True
        # 检查本地是否有已保存的cookie
        if os.path.exists(os.path.join("pickle","dwglpt_asset_cookie.pkl")):
            with open(os.path.join("pickle","dwglpt_asset_cookie.pkl"),"rb") as f:
                dwglpt_cookies = pickle.load(f)
            logger.info("正在检查资产域凭据是否有效...")
            if await check_cookie_ok(dwglpt_cookies):
                need_refresh_http = False

        # 如果cookie无效则重新登录
        if need_refresh_http:
            logger.warning("资产域凭据失效。正在重新登录....")
            # iam_sess = fourA_login()
            # http = fourA_get_dwglpt_asset_domain_session(csgst)
            iam_cookies = await iam_login(username, password)
            dwglpt_cookies = await iam_get_dwglpt_asset_domain_session(iam_cookies)
            if not await check_cookie_ok(dwglpt_cookies):
                raise Exception("电网管理平台登录失败！")

        # 保存cookie到本地
        os.makedirs("pickle",exist_ok=True)
        with open(os.path.join("pickle","dwglpt_asset_cookie.pkl"),"wb") as f:
            pickle.dump(dwglpt_cookies,f)

        # 初始化aiohttp会话，带上cookie
        cj_new = aiohttp.CookieJar(unsafe=True)
        cj_new.update_cookies(dwglpt_cookies)
        self._sess = aiohttp.ClientSession(cookie_jar=cj_new)

    # GET请求
    async def get(self,url):
        """
        发送异步GET请求
        Args:
            url: 请求URL
        Returns:
            JSON响应数据
        """
        resp = await self._sess.get(
            url,
        )
        
        return await resp.json()

    # POST请求
    async def post(self,url,body):
        """
        发送异步POST请求
        Args:
            url: 请求URL
            body: 请求体数据
        Returns:
            JSON响应数据
        """
        resp = await self._sess.post(
            url,
            json=body,
        )
        return await resp.json()

# 测试主流程
async def main():
    """
    测试主函数，演示如何使用DwglptHttp类
    """
    dwglpt_http = DwglptHttp()
    # 使用自定义用户名和密码登录
    # await dwglpt_http.http_init("your_username@nng.gx.csg.cn", "your_password")
    # 或者使用默认用户名和密码
    await dwglpt_http.http_init()
    print(await dwglpt_http.get("http://10.10.21.28/api/jadp/auth/currentUser"))
    await dwglpt_http.http_destory()

if __name__ == "__main__":
    asyncio.run(main())
