# -*- coding: UTF-8 -*- 

####################################################
# 数认-业务系统登陆API示例 V0.1
# 功能：演示电网管理平台资产域API的使用方法
####################################################

import os
import logging


# 导入urllib3并禁用SSL警告，避免HTTPS请求时的警告信息
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 配置根日志记录器
rootlogger = logging.getLogger()
rootlogger.setLevel(logging.DEBUG)

# 设置日志格式：包含时间戳、模块名、线程名、日志级别、文件名行号等信息
logFormatter = logging.Formatter('%(asctime)s [%(name)s] [%(threadName)s] [%(levelname)s] [%(filename)s:%(lineno)d] %(message)s')
consoleHeader = logging.StreamHandler()
consoleHeader.setFormatter(logFormatter)

rootlogger.addHandler(consoleHeader)

# 获取当前模块的日志记录器
logger = logging.getLogger(__name__)

# 导入电网管理平台API模块
from api import dwglpt_api

# 导入elink的API模块
from api import elink_push, elink_revoke, ServiceClientV2

if __name__ == "__main__":
    print("=====资产域======")
    # 创建资产域API实例，会自动处理登录和会话管理
    asset_api = dwglpt_api.DwglptAssetAPI()
    
    # 存储查询到的人员ID和组织ID
    pids_person_to_query = []
    pids_orgs_to_query = []
    
    # 查询南宁供电局下的所有子节点（人员和组织）
    # 参数"11739068305E522EE05336050A0A3A5C"是南宁供电局的组织ID
    for child in asset_api.asset_person_choose_children("11739068305E522EE05336050A0A3A5C"): #南宁供电局
        if child["isFolder"] == "false":
            # 如果不是文件夹，说明是人员，添加到人员查询列表
            pids_person_to_query.append(child["key"])
        else:
            # 如果是文件夹，说明是组织，添加到组织查询列表
            pids_orgs_to_query.append(child["key"])
            #print("discovered",child["fullName"],child["key"])

    print("=======查到的人=======")
    print(pids_person_to_query)
    # 批量查询人员详细信息
    persons = asset_api.asset_person_choose_selectedData(pids_person_to_query)
    #print(persons[:3])  # 只显示前3个人员信息
    
    print("=======查到的组织=======")
    print(pids_orgs_to_query)
    # 批量查询组织详细信息，choosetype="org"表示查询组织而非人员
    orgs = asset_api.asset_person_choose_selectedData(pids_orgs_to_query,choosetype="org")
    print(orgs[:3])  # 只显示前3个组织信息
    

    # 通过组织ID查询维护检修计划
    print("=======查到的计划=======")
    planBeginTime = "2025-07-01"
    planEndTime = "2025-07-30"
    print("通过组织ID 查询 维护检修计划",orgs[2]["fullName"],orgs[2]["orgCode"])
    plan_list = asset_api.asset_pplan_queryPlanList(orgs[2]["orgCode"],planBeginTime,planEndTime)[:1]  #查询该组织的检修维护计划
    print(plan_list)  
    jobContent = plan_list[0]["jobContent"]  #计划的工作内容
    print("工作内容:",jobContent)
    
    # 通过组织ID查询工作票
    print("=======查到的工作票=======")
    print("通过组织ID 查询 工作票",orgs[2]["fullName"],orgs[2]["orgCode"])
    print(asset_api.asset_wticket_query(orgs[2]["orgCode"],"2025-07-01 00:00:00","2025-07-30 00:00:00")[:1])

    # 通过组织ID查询操作票
    print("=======查到的操作票=======")
    otickets = asset_api.asset_oticket_query("变电管理三所","2025-08-01 00:00:00","2025-08-01 23:59:59",["3", "4"])
    print(otickets)
    
    # # 使用操作票验证器验证数据
    # print("=======操作票验证=======")
    # try:
    #     from oticket_validator import OTicketValidator
        
    #     # 创建验证器实例
    #     validator = OTicketValidator()
        
    #     # 执行验证
    #     result = validator.validate_all(otickets)
        
    #     # 输出验证结果
    #     print(f"验证结果: {'通过' if result['is_valid'] else '不通过'}")
    #     print(f"总票数: {result['summary']['total_tickets']}")
    #     print(f"时间错误数: {result['summary']['time_errors']}")
    #     print(f"计划绑定错误数: {result['summary']['plan_errors']}")
    #     print(f"内容错误数: {result['summary']['content_errors']}")
        
    #     # 详细错误信息
    #     if not result['time_validation']['is_valid']:
    #         print("\n时间验证错误:")
    #         for error in result['time_validation']['single_ticket_errors']:
    #             print(f"  - {error}")
    #         for error in result['time_validation']['multi_ticket_errors']:
    #             print(f"  - {error}")
        
    #     if not result['plan_validation']['is_valid']:
    #         print("\n计划绑定错误:")
    #         for ticket in result['plan_validation']['unbound_tickets']:
    #             print(f"  - {ticket} 未绑定计划")
                
    # except ImportError as e:
    #     print(f"导入操作票验证器失败: {e}")
    #     print("请确保oticket_validator文件夹存在且包含必要的文件")
    # except Exception as e:
    #     print(f"操作票验证失败: {e}")


    # print("没有封装API的时候怎么调用")
    # # 演示如何直接调用HTTP接口（从浏览器开发者工具复制的请求参数）
    # payload = { # 从devtools里面复制出request payload
    #     "queryCondition": {
    #         "bureauCode": "0401",  # 局代码
    #         "eqtAPIVersion": "V1",
    #         "flName": "",
    #         "runningState": "",
    #         "baseVoltageId": "",
    #         "dominionMode": "",
    #         "subType": "",
    #         "centerSubstationId": "",
    #         "vindicateOid": "",
    #         "plantTransferDateStrS": "",
    #         "plantTransferDateStrE": "",
    #         "isNewPower": "",
    #         "investSourceType": ""
    #     },
    #     "pageIndex": 1,
    #     "pageSize": 25,
    #     "sortFieldName": "id",
    #     "eqtAPIVersion": "V1",
    #     "isAsc": True,
    #     "bureauCode": "0401"
    # }
    # print(
    #     asset_api.http_post( # 如果方式是POST，就用http_post，如果是GET，就用http_get
    #         "/gmp/sp/cmquerymanageservice/cimquery/substationInfo/substationList", # 找到的URL，不包含前面的网址部分
    #         payload
    #     )
    # )
 