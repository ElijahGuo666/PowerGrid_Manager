#!/usr/bin/env python3
# -*- coding: UTF-8 -*- 

####################################################
# 数字身份认证平台 API V0.1
# 功能：实现数字身份认证平台的自动化登录流程，包括验证码识别、密码加密、获取业务系统登录cookie等
####################################################

import requests
import logging
from urllib.parse import parse_qs
import re
import copy

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# 用于提取登录URL的正则表达式
#var locationValue = "https://10.10.21.133/im-gateway/szsfyfwglpt/im-business/business/loginAuth?code=6bd6aaa0b722f2b161cd382a9280202a&amp;state=1";
iam_loc_regex = r"var locationValue = \"(.*)\";"

def iam_login():
    """
    数字身份认证平台自动登录流程
    包含验证码识别、密码加密、获取登录token等步骤
    Returns:
        requests.Session: 已登录的会话对象
    """
    http = requests.Session()
    # 设置User-Agent，模拟浏览器请求
    http.headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.71 Safari/537.36 SE 2.X MetaSr 1.0"

    # 第一步：获取登录页面，获取lck参数
    resp = http.get(
        "https://10.10.21.133/idp/authCenter/authenticate?response_type=code&state=1&redirect_uri=https://10.10.21.133/im-gateway/szsfyfwglpt/im-business/business/loginAuth&client_id=im",
        allow_redirects=False,
        verify=False
    )

    # 解析重定向URL，提取lck参数
    parsed_target = resp.headers["Location"].replace("https://10.10.21.133/login/#/index?","")
    lck = parse_qs(parsed_target)["lck"][0]
    logger.debug("lck=%s",lck)

    # 第二步：获取挑战码（challenge）
    resp = http.get(
        "https://10.10.21.133/am-gateway/szsfyfwglpt/am-authn-service/authn/authJiDaRandom",
        verify=False
    )

    # 响应格式：{"original":"70o84e","code":"200","QRCodeAuth":"false","authnCerKey":"22001787-67ac-4b5a-8cf8-48c3f8f64036"}
    challange = resp.json()

    # 第三步：获取PKI服务地址
    resp = http.post(
        "https://127.0.0.1:10087/",
        data="QueryService",
        verify=False
    )

    pki_baseurl = resp.text

    # 第四步：初始化PKI服务
    resp = http.post(
        pki_baseurl,
        data='GetVersion:',
        verify=False
    )
    logger.debug("PKI Version=%s",resp.text)

    # 第五步：初始化PKI加密库
    resp = http.post(
        pki_baseurl,
        data="Initialize:{\"strAlgType\":\"\",\"strAuxParam\":\"<?xml version=\\\"1.0\\\" encoding=\\\"utf-8\\\"?><authinfo><liblist><lib type=\\\"CSP\\\" version=\\\"1.0\\\" dllname=\\\"\\\" ><algid val=\\\"SHA1\\\" sm2_hashalg=\\\"sm3\\\"/></lib><lib type=\\\"SKF\\\" version=\\\"1.1\\\" dllname=\\\"SERfR01DQUlTLmRsbA==\\\" ><algid val=\\\"SHA1\\\" sm2_hashalg=\\\"sm3\\\"/></lib><lib type=\\\"SKF\\\" version=\\\"1.1\\\" dllname=\\\"U2h1dHRsZUNzcDExXzMwMDBHTS5kbGw=\\\" ><algid val=\\\"SHA1\\\" sm2_hashalg=\\\"sm3\\\"/></lib><lib type=\\\"SKF\\\" version=\\\"1.1\\\" dllname=\\\"U0tGQVBJLmRsbA==\\\" ><algid val=\\\"SHA1\\\" sm2_hashalg=\\\"sm3\\\"/></lib><lib type=\\\"SKF\\\" version=\\\"1.1\\\" dllname=\\\"dGFzc19ncGdjX2VwYXNzM2tnbS5kbGw=\\\" ><algid val=\\\"SHA1\\\" sm2_hashalg=\\\"sm3\\\"/></lib><lib type=\\\"PM\\\" version=\\\"1.0\\\" dllname=\\\"Q3J5cHRPY3guZGxs\\\"><algid val=\\\"SHA1\\\" sm2_hashalg=\\\"SM3\\\" /></lib><lib type=\\\"CSP\\\" version=\\\"1.0\\\" dllname=\\\"RW50ZXJTYWZlIGVQYXNzMzAwMEdNIENTUCBGb3IgSklUIFYxLjA\\\"><algid val=\\\"SHA1\\\" sm2_hashalg=\\\"SHA1\\\" /></lib><lib type=\\\"CSP\\\" version=\\\"1.0\\\" dllname=\\\"TWljcm9zb2Z0IFN0cm9uZyBDcnlwdG9ncmFwaGljIFByb3ZpZGVy\\\"><algid val=\\\"SHA1\\\" sm2_hashalg=\\\"SHA1\\\" /></lib><lib type=\\\"CSP\\\" version=\\\"1.0\\\" dllname=\\\"RW50ZXJTYWZlIGVQYXNzMzAwMyBDU1AgdjEuMA==\\\"><algid val=\\\"SHA1\\\" sm2_hashalg=\\\"SHA1\\\" /></lib><lib type=\\\"CSP\\\" version=\\\"1.0\\\" dllname=\\\"SklUIFVTQiBLZXkgQ1NQIHYxLjA=\\\"><algid val=\\\"SHA1\\\" sm2_hashalg=\\\"SHA1\\\" /></lib><lib type=\\\"CSP\\\" version=\\\"1.0\\\" dllname=\\\"RW50ZXJTYWZlIGVQYXNzMjAwMSBDU1AgdjEuMA==\\\"><algid val=\\\"SHA1\\\" sm2_hashalg=\\\"SHA1\\\" /></lib><lib type=\\\"CSP\\\" version=\\\"1.0\\\" dllname=\\\"SklUIFVTQiBLZXkzMDAzIENTUCB2MS4w\\\"><algid val=\\\"SHA1\\\" sm2_hashalg=\\\"SHA1\\\" /></lib><lib type=\\\"CSP\\\" version=\\\"1.0\\\" dllname=\\\"TWljcm9zb2Z0IEJhc2UgQ3J5cHRvZ3JhcGhpYyBQcm92aWRlciB2MS4w\\\"><algid val=\\\"SHA1\\\" sm2_hashalg=\\\"SHA1\\\" /></lib><lib type=\\\"CSP\\\" version=\\\"1.0\\\" dllname=\\\"RkVJVElBTiBlUGFzc05HIFJTQSBDcnlwdG9ncmFwaGljIFNlcnZpY2UgUHJvdmlkZXI=\\\"><algid val=\\\"SHA1\\\" sm2_hashalg=\\\"SHA1\\\" /></lib><lib type=\\\"CSP\\\" version=\\\"1.0\\\" dllname=\\\"RkVJVElBTiBlUGFzc05HIENTUCBGb3IgSklUM0sgVjEuMA==\\\"><algid val=\\\"SHA1\\\" sm2_hashalg=\\\"SHA1\\\" /></lib><lib type=\\\"SKF\\\" version=\\\"1.1\\\" dllname=\\\"SklUR01LRVlfU0pLMTQyNC5kbGw=\\\"><algid val=\\\"SHA1\\\" sm2_hashalg=\\\"SM3\\\" /></lib><lib type=\\\"SKF\\\" version=\\\"1.0\\\" dllname=\\\"Sml0M2tHTVAxMVYyMTEuZGxs\\\"><algid val=\\\"SHA1\\\" sm2_hashalg=\\\"SM3\\\" /></lib><lib type=\\\"SKF\\\" version=\\\"1.1\\\" dllname=\\\"L3Vzci9saWIvbGliZXNfMzAwMGdtLnNvLjEuMC4w\\\" ><algid val=\\\"SHA1\\\" sm2_hashalg=\\\"sm3\\\"/></lib><lib type=\\\"SKF\\\" version=\\\"1.1\\\" dllname=\\\"L3Vzci9saWIvbGliZXNfMzAwMGdtLnNvLjEuMC4w\\\" ><algid val=\\\"SHA1\\\" sm2_hashalg=\\\"sm3\\\"/></lib></liblist></authinfo>\"}",
        verify=False,
        headers={"Content-Type":"text/plain;charset=UTF-8"}
    )
    logger.debug("PKI init:%s",resp.text)

    # 第六步：设置证书选择模式
    resp = http.post(
        pki_baseurl,
        data='SetChooseSingleCert:{"isChoose":1}',
        verify=False
    )
    logger.debug("PKI SetChooseSingleCert=%s",resp.text)

    # 提示用户输入USB-KEY密码
    logger.info("=========================================")
    logger.info("请在弹出的对话框中，输入您的USB-KEY密码（如果有）")
    logger.info("=========================================")

    # 第七步：使用证书对挑战码进行签名
    resp = http.post(
        pki_baseurl,
        data='P7SignString:{"strValue":"'+ challange["original"] +'","isDetach":true,"isIncludeCert":true}',
        verify=False
    )
    logger.debug("PKI P7SignString=%s" % resp.text)
    signed_val = resp.json()["value"]

    # 第八步：检查PKI操作是否成功
    resp = http.post(
        pki_baseurl,
        data='GetLastError:',
        verify=False
    )
    logger.debug("PKI GetLastError=%s" % resp.text)

    if int(resp.json()["value"]) != 0:
        resp = http.post(
            pki_baseurl,
            data='GetLastErrorMessage:',
            verify=False
        )
        logger.debug("PKI GetLastErrorMessage=%s" % resp.text)
        raise ValueError("PKI证书登录失败！原因：%s" % resp.json()["value"])

    # 第九步：结束PKI操作
    resp = http.post(
        pki_baseurl,
        data='Finalize:',
        verify=False
    )
    logger.debug("PKI Finalize=%s" % resp.text)

    # 第十步：提交认证请求
    resp = http.post(
        "https://10.10.21.133/am-gateway/szsfyfwglpt/am-authn-service/authn/authExecute?lang=zh_CN",
        json={
            "authModuleCode":"jiDaCer",
            "authChainCode":"23938cda55144219ad4c3ede53a0249c",
            "entityId":"im",
            "requestType":"chain_type",
            "lck":lck,
            "authPara":{
                "authMode":"cert",
                "original":challange["original"],
                "signed_data":signed_val,
                "authnCerKey":challange["authnCerKey"],
                "token": challange["original"],
                "loginName":None
            }
        },
        verify=False
    )
    logger.debug("IAM authExecute=%s" % resp.text)

    # 检查认证结果
    iam_login_result = resp.json()
    if iam_login_result["status"] != 200:
        raise ValueError("数字认证平台登录失败！！")
    logintoken = resp.json()["loginToken"]

    # 第十一步：获取业务系统登录URL
    resp = http.get(
        "https://10.10.21.133/idp/authCenter/authnEngine?loginToken=" + logintoken,
        verify=False
    )
    loginurl = re.findall(iam_loc_regex,resp.text)[0]
    logger.debug("IAM Login URL=%s",loginurl)

    # 第十二步：访问业务系统，完成登录
    http.get(
        loginurl,
        verify=False
    )

    return http

def iam_get_dwglpt_asset_domain_session(iam_session:requests.Session):
    """
    获取电网管理平台资产域的会话
    Args:
        iam_session: 已登录的IAM会话对象
    Returns:
        requests.Session: 资产域会话对象
    """
    session = copy.deepcopy(iam_session)
    # 获取资产域登录URL
    resp = session.get(
        "https://10.10.21.133/idp/authCenter/authenticate?response_type=code&state=1&redirect_uri=http://10.10.21.28/gmp/static/gmpweb/index.html&client_id=pgpas",
        verify=False
    )
    loginurl = re.findall(iam_loc_regex,resp.text)[0]
    logger.debug("GMP Login URL=%s",loginurl)

    # 解析登录URL，获取token
    parsed_target = loginurl.replace("http://10.10.21.28/gmp/static/gmpweb/index.html?","")
    dwglpt_token = parse_qs(parsed_target)["code"][0]
    logger.debug("dwglpt_token=%s",dwglpt_token)

    # 设置Authorization cookie
    resp = session.get("http://10.10.21.28/security/JavaScriptServlet")
    session.cookies.set("Authorization",dwglpt_token)
    resp = session.get("http://10.10.21.28/api/jadp/auth/currentUser")

    return session

def iam_get_dwglpt_hr_domain_session(iam_session:requests.Session):
    """
    获取电网管理平台人资域的会话
    Args:
        iam_session: 已登录的IAM会话对象
    Returns:
        requests.Session: 人资域会话对象
    """
    session = copy.deepcopy(iam_session)
    # 获取人资域登录URL
    resp = session.get(
        "https://10.10.21.133/idp/authCenter/authenticate?response_type=code&state=1&redirect_uri=http://10.10.21.23/gmp/static/gmpweb/index.html&client_id=pgphs",
        verify=False
    )
    loginurl = re.findall(iam_loc_regex,resp.text)[0]
    logger.debug("GMP Login URL=%s",loginurl)

    # 解析登录URL，获取token
    parsed_target = loginurl.replace("http://10.10.21.23/gmp/static/gmpweb/index.html?","")
    dwglpt_token = parse_qs(parsed_target)["code"][0]
    logger.debug("dwglpt_token=%s",dwglpt_token)

    # 设置Authorization cookie
    session.cookies.set("Authorization",dwglpt_token)
    resp = session.get("http://10.10.21.23/api/jadp/auth/currentUser")

    return session

def iam_get_dwglpt_fms_domain_session(iam_session:requests.Session):
    """
    获取电网管理平台计财域的会话
    Args:
        iam_session: 已登录的IAM会话对象
    Returns:
        requests.Session: 计财域会话对象
    """
    session = copy.deepcopy(iam_session)
    # 获取计财域登录URL
    resp = session.get(
        "https://10.10.21.133/idp/authCenter/authenticate?response_type=code&state=1&redirect_uri=https://fms.gmp.cloud.hq.iv.csg/gmp/index.html&client_id=pgpfs",
        verify=False
    )
    loginurl = re.findall(iam_loc_regex,resp.text)[0]
    logger.debug("GMP Login URL=%s",loginurl)

    # 解析登录URL，获取token
    parsed_target = loginurl.replace("https://fms.gmp.cloud.hq.iv.csg/gmp/index.html?","")
    dwglpt_token = parse_qs(parsed_target)["code"][0]
    logger.debug("dwglpt_token=%s",dwglpt_token)

    # 设置Authorization cookie
    session.cookies.set("Authorization",dwglpt_token)
    resp = session.get("https://fms.gmp.cloud.hq.iv.csg/api/jadp/auth/currentUser",verify=False)

    return session

if __name__ == "__main__":
    # 测试代码
    iam_session = iam_login()
    # dwglpt_asset_sess = iam_get_dwglpt_asset_domain_session(iam_session)
    dwglpt_hr_sess = iam_get_dwglpt_hr_domain_session(iam_session)

