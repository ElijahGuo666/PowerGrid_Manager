#!/usr/bin/env python3
# -*- coding: UTF-8 -*- 

####################################################
# 电网管理平台 三大域 API V0.1
# 功能：提供电网管理平台资产域、人资域、计财域的API封装
####################################################

import json
import string
from . import iam_api
import pickle
import os
import requests
import sys
import logging

logger = logging.getLogger(__name__)

# 导入RSA加密相关模块

from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5

import base64
import math

# RSA公钥字符串，用于加密ID参数
enckey = "MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCNfcV+KcSNFZDJat4c1IHkDZNmqJ9F9SVTq30S4X3RAiZgLLeULHvEo12zEZGUqN/7pt55E3jVipTS76V8VNKJUj7phakUH/WErJjfdKaU4jD/Vkkx+anwCG14+jDRashs4E91CG0M+Bmq0KZeqfi086dlr8C53ONBVQDV/PQuRwIDAQAB"
# 导入公钥对象
if RSA is not None:
    pubKey = RSA.import_key('-----BEGIN PUBLIC KEY-----\n' + enckey + '\n-----END PUBLIC KEY-----')
else:
    pubKey = None

def encrypt_id(msg):
    """
    使用RSA公钥加密ID字符串
    Args:
        msg: 需要加密的ID字符串
    Returns:
        base64编码的加密结果
    """
    if pubKey is None or PKCS1_v1_5 is None:
        raise ImportError("RSA加密模块未安装，无法进行加密")
    encryptor = PKCS1_v1_5.new(pubKey)
    encrypted = encryptor.encrypt(msg.encode())
    return base64.b64encode(encrypted).decode()

# 三大域基础API类
class DwglptBaseAPI():
    """
    电网管理平台三大域的基础API类
    提供通用的登录、会话管理、HTTP请求等功能
    """

    DOMAIN_NAME = "base"  # 域名称
    BASEURL = "http://10.10.21.28"  # 基础URL

    def login_function(self,iam_sess):
        """
        根据域名称调用对应的登录函数
        Args:
            iam_sess: IAM会话对象
        Returns:
            对应域的会话对象
        """
        if self.DOMAIN_NAME == "asset":
            return iam_api.iam_get_dwglpt_asset_domain_session(iam_sess)
        elif self.DOMAIN_NAME == "hr":
            return iam_api.iam_get_dwglpt_hr_domain_session(iam_sess)
        elif self.DOMAIN_NAME == "fms":
            return iam_api.iam_get_dwglpt_fms_domain_session(iam_sess)
        else:
            raise Exception("Unknown Domain")

    def check_http_ok(self,http):
        """
        检查HTTP会话是否有效（用户是否已登录）
        Args:
            http: HTTP会话对象
        Returns:
            bool: 会话是否有效
        """
        try:
            resp = http.request("GET",self.BASEURL + "/api/jadp/auth/currentUser",verify=False)
        except requests.exceptions.ConnectionError as e:
            logger.error("网络链接错误，请检查网络。")
            logger.error(str(e))
            sys.exit(1)

        respdata = resp.json()
        logger.debug(respdata)
        if resp.ok and respdata["state"] == 1:
            logger.debug("已使用如下身份登录:{}_{}".format(respdata["nameFullPath"],respdata["employeeName"]))
            return True
        return False

    def __init__(self):
        """
        初始化API实例，自动处理登录和会话管理
        """
        logger.debug("API:%s BASE:%s",self.DOMAIN_NAME,self.BASEURL)

        # 构建cookie文件路径
        self.pkl_path = os.path.join("pickle","dwglpt_" + self.DOMAIN_NAME + "_http.pkl")

        need_refresh_http = True
        # 检查本地是否有保存的会话
        if os.path.exists(self.pkl_path):
            with open(self.pkl_path,"rb") as f:
                http = pickle.load(f)
            logger.debug("正在检查凭据是否有效...")
            if self.check_http_ok(http):
                need_refresh_http = False

        # 如果会话无效，重新登录
        if need_refresh_http:
            logger.info("凭据失效。正在重新登录....")
            iam_sess = iam_api.iam_login()
            http = self.login_function(iam_sess)
            if not self.check_http_ok(http):
                raise Exception("电网管理平台登录失败！")

        # 保存会话到本地
        os.makedirs("pickle",exist_ok=True)
        with open(self.pkl_path,"wb") as f:
            pickle.dump(http,f)

        self.http = http

    def http_get(self,url):
        """
        发送GET请求
        Args:
            url: 请求URL（不包含基础URL）
        Returns:
            JSON响应数据
        """
        resp = self.http.request("GET",
            self.BASEURL + url,
            verify=False
        )
        
        return resp.json()

    def http_post(self,url,body):
        """
        发送POST请求
        Args:
            url: 请求URL（不包含基础URL）
            body: 请求体数据
        Returns:
            JSON响应数据
        """
        resp = self.http.request("POST",
            self.BASEURL + url,
            json=body,
            verify=False
        )
        return resp.json()

    # 开始 具体API：
    # common: 三大域通用API
    def common_currentUser(self):
        """
        获取当前登录用户信息
        Returns:
            当前用户详细信息
        """
        return self.http_get("/api/jadp/auth/currentUser")

# 批量查询时的切片大小
BATCH_QUERY_SLICE = 20

# 资产域API类
class DwglptAssetAPI(DwglptBaseAPI):
    """
    电网管理平台资产域API封装
    提供人员、组织、计划、工作票等查询功能
    """
    DOMAIN_NAME = "asset"
    BASEURL = "http://10.10.21.28"

    def asset_person_choose_children(self,pid):
        """
        获取指定节点下的子节点（人员或组织）
        Args:
            pid: 父节点ID
        Returns:
            子节点列表，格式为[{
                'fullName': '中国南方电网有限责任公司/广西电网有限责任公司/南宁供电局/安全监管部（应急指挥中心）',    
                'key': '1173906831A3522EE05336050A0A3A5C',
                'title': '安全监管部（应急指挥中心）',
                'isFolder': 'true'/'false'  # true表示组织，false表示人员
            },....]
        """
        return self.http_get(
            f"/api/jadp/personnel/choose/{pid}/children?id={pid}&userType=1&orgTypes="
        )
    
    def asset_person_choose_selectedData(self,pids,choosetype="user"):
        """
        批量获取人员或组织的详细信息
        Args:
            pids: 人员或组织ID列表
            choosetype: 查询类型，"user"表示人员，"org"表示组织
        Returns:
            人员或组织详细信息列表，格式为[{
                'employeeAccount': 'admin_sc_gx@csg.cn',
                'employeeId': 'CFB5C09B743E709BE05396D55C0A3F0D',
                'fullName': '中国南方电网有限责任公司/广西电网有限责任公司/南宁供电局/韦启杉',
                'id': 'E8595698845749DE9F4E54FB061C9B0D',
                'mobilePhone': '14795556908',
                'name': '韦启杉',
                'orgCode': '0401',
                'orgId': '11739068305E522EE05336050A0A3A5C',
                'orgLevel': 0,
                'orgName': '南宁供电局',
                'sex': 1,
                'showName': '韦启杉',
                'userState': 1,
                'userTitle': '21',
                ........
            },.....]
        """
        if len(pids) == 0:
            return []

        # 对ID进行加密
        pids_encrypted = []
        for pid in pids:
            pids_encrypted.append(encrypt_id(pid))

        sliced_result = []

        # 分批查询，避免单次请求过大
        for iter in range(math.ceil(len(pids_encrypted) / BATCH_QUERY_SLICE)):
            iter_pids = pids_encrypted[
                iter * BATCH_QUERY_SLICE : 
                (iter+1) * BATCH_QUERY_SLICE
            ]
        
            req_payload = {
                "chooseType":choosetype,
                "ids":iter_pids,
                "showLevel":1,
                "showOrder":"order"
            }

            sliced_result += self.http_post(
                "/api/jadp/personnel/choose/SelectedData",
                req_payload
            )
        
        return sliced_result

    def asset_pplan_queryPlanList(self, orgCode, planBeginTime, planEndTime):
        """
        查询组织维护检修计划，自动获取所有数据（分页拉取）
        Args:
            orgCode: 组织代码
            planBeginTime: 计划开始时间（格式：YYYY-MM-DD）
            planEndTime: 计划结束时间（格式：YYYY-MM-DD）
        Returns:
            所有维护检修计划数据列表
        """
        pageNo = 1
        pageSize = 100
        all_data = []

        while True:
            req_payload = {
                "pageNo": pageNo,
                "pageSize": pageSize,
                "sortType": "asc",
                "sortTypes": [
                    "asc"
                ],
                "planDateType": "month",
                "planBeginTime": planBeginTime,
                "planEndTime": planEndTime,
                "workTeamOcode": orgCode,
                "powerGridFlag": 1,
                "sortColumnType": "asc"
            }

            resp = self.http_post(
                "/gmp/sp/operationmaintenaceservice/prodplan/ppPlanQuery/queryPlanList",
                req_payload
            )
            data_list = resp.get("list", []) if isinstance(resp, dict) else []
            all_data.extend(data_list)

            total = resp.get("total", 0) if isinstance(resp, dict) else 0
            if pageNo * pageSize >= total or not data_list:
                break
            pageNo += 1

        return all_data

    def asset_wticket_query(self, orgCode, planBeginTime, planEndTime):
        """
        查询组织工作票，自动获取所有数据（分页拉取）
        Args:
            orgCode: 组织代码
            planBeginTime: 计划开始时间（格式：YYYY-MM-DD HH:mm:ss）
            planEndTime: 计划结束时间（格式：YYYY-MM-DD HH:mm:ss）
        Returns:
            所有工作票数据列表
        """
        pageNo = 1
        pageSize = 100
        all_data = []

        while True:
            req_payload = {
                "planStartTime": planBeginTime,
                "planEndTime": planEndTime,
                "provinceCode": orgCode[:2],  # 省份代码（前2位）
                "bureauCode": orgCode[:4],    # 局代码（前4位）
                "ticketTypes": [],
                "peopleTypePulldown": "0",
                "whetherOuterDept": None,
                "timeTypePulldown": "0",
                "workStates": [],
                "powerGridFlag": None,
                "isExitSwitch": None,
                "isAssociatePowerCut": "0",
                "delayTimeEndDateRangePicker": [],
                "isGraph": "0",
                "standardType": "0",
                "whetherSecondbill": "0",
                "isSupplyTicket": "0",
                "isGap": "0",
                "isKeyStation": "0",
                "riskLevals": [],
                "ticketSourceList": [],
                "isLancangMekong": "0",
                "departmentCode": orgCode,
                "workPermissionOid": "",
                "workPermissionOname": "",
                "workPermissionOcode": "",
                "vindicateOids": [],
                "vindicateOnames": "",
                "vindicateOcodes": [],
                "changeNewPrincipalUid": "",
                "changeNewPrincipalUname": "",
                "countyId": "",
                "countyName": "",
                "countyCode": "",
                "pageNo": pageNo,
                "pageSize": pageSize,
                "sortName": "createTime",
                "sortType": "desc",
                "sortFieldName": "createTime",
                "sortNames": [
                    "createTime"
                ],
                "sortTypes": [
                    "desc"
                ],
                "mobileOperationStates": []
            }

            resp = self.http_post(
                "/gmp/sp/operationmaintenaceservice/workticket/wticketQueryDTO/queryWticketList",
                req_payload
            )
            # 兼容返回结构
            data_list = []
            if isinstance(resp, dict):
                data_list = resp.get("list", [])
            elif isinstance(resp, list):
                data_list = resp

            all_data.extend(data_list)

            # 判断是否拉取完毕
            if not data_list or len(data_list) < pageSize:
                break
            pageNo += 1

        return all_data

    def asset_oticket_query(self, createOname, operationStartTime, operationStartTimeEnd, ticketStateList):
        """
        查询组织操作票，自动获取所有数据（分页拉取）
        Args:
            createOname: 创建组织名称
            operationStartTime: 操作开始时间（格式：YYYY-MM-DD HH:mm:ss）
            operationStartTimeEnd: 操作结束时间（格式：YYYY-MM-DD HH:mm:ss）
            ticketStateList: 操作票状态列表
        Returns:
            所有操作票数据列表
        """
        pageNo = 1
        pageSize = 100
        all_data = []

        while True:
            req_payload = {
                "createOid": "8adc55298c9271f8018cafdee68c11d9",
                "createOcode": "04016311",
                "createOname": createOname,
                "ticketStateList": ticketStateList,  # 操作票状态[未上报，未审核，已初审，已生成，已归档，未执行，已作废]
                "provinceCode": "04",
                "bureauCode": "0401",
                "operationStartTimeEndDateRangePicker": [],
                "operationEndTimeEndDateRangePicker": [],
                "operationStartTime": operationStartTime,
                "operationStartTimeEnd": operationStartTimeEnd,
                "oticketSourceList": [],
                "powerGridFlag": "0",
                "generateDateEndDateRangePicker": [],
                "reportTimeEndDateRangePicker": [],
                "archiveTimeEndDateRangePicker": [],
                "issueOrderDeptList": [],
                "isKeyStation": "0",
                "riskLevals": [],
                "createUid": "",
                "createUname": "",
                "entryUid": "",
                "entryUname": "",
                "operatorUidList": [],
                "operatorUnames": "",
                "guardianUidList": [],
                "guardianUnames": "",
                "watchUid": "",
                "watchUname": "",
                "pageNo": pageNo,
                "pageSize": pageSize,
                "sortName": "updateTime",
                "sortType": "desc",
                "sortFieldName": "updateTime",
                "sortNames": ["updateTime"],
                "sortTypes": ["desc"],
                "dataBelongUnitOcode": ""
            }

            resp = self.http_post(
                "/gmp/sp/operationmaintenaceservice/operationticket/oticketManageQuery/queryOTicketQueryList",
                req_payload
            )
            # 兼容返回结构
            data_list = []
            if isinstance(resp, dict):
                data_list = resp.get("list", [])
            elif isinstance(resp, list):
                data_list = resp

            all_data.extend(data_list)

            # 判断是否拉取完毕
            if not data_list or len(data_list) < pageSize:
                break
            pageNo += 1

        return all_data


        

# 人资域API类
class DwglptHrAPI(DwglptBaseAPI):
    """
    电网管理平台人资域API封装
    """
    DOMAIN_NAME = "hr"
    BASEURL = "http://10.10.21.23"

# 计财域API类
class DwglptFmsAPI(DwglptBaseAPI):
    """
    电网管理平台计财域API封装
    """
    DOMAIN_NAME = "fms"
    BASEURL = "https://fms.gmp.cloud.hq.iv.csg"

if __name__ == "__main__":
    # 测试代码
    # msg = "62DFDA59020A454A827087848C892BA5"
    # print(encrypt_id(msg))

    # api = DwglptAssetAPI()
    # print(api.common_currentUser())

    # api = DwglptHrAPI()
    # print(api.common_currentUser())

    api = DwglptFmsAPI()
    print(api.common_currentUser())


    

