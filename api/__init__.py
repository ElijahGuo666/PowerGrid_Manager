#!/usr/bin/env python3
# -*- coding: UTF-8 -*- 

"""
电网管理平台API包
提供电网管理平台三大域（资产域、人资域、计财域）的API封装
"""

# 导出主要的API类
from .dwglpt_api import DwglptBaseAPI, DwglptAssetAPI, DwglptHrAPI, DwglptFmsAPI
from .dwglpt_http import DwglptHttp
from .dwglpt_person_api import DwglptPersonAPI
from .dwglpt_pplan_api import DwglptPPlanAPI
from .dwglpt_encrypt import encrypt_id
from .iam_api import iam_login, iam_get_dwglpt_asset_domain_session, iam_get_dwglpt_hr_domain_session, iam_get_dwglpt_fms_domain_session
from .elink_push_real import elink_push, elink_revoke, ServiceClientV2

__all__ = [
    'DwglptBaseAPI',
    'DwglptAssetAPI', 
    'DwglptHrAPI',
    'DwglptFmsAPI',
    'DwglptHttp',
    'DwglptPersonAPI',
    'DwglptPPlanAPI',
    'encrypt_id',
    'iam_login',
    'iam_get_dwglpt_asset_domain_session',
    'iam_get_dwglpt_hr_domain_session', 
    'iam_get_dwglpt_fms_domain_session',
    'elink_push',
    'elink_revoke',
    'ServiceClientV2'
] 