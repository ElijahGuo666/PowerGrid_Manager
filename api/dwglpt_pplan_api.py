import json
import asyncio
from .dwglpt_encrypt import encrypt_id
from .dwglpt_http import DwglptHttp
from pprint import pprint
import math

BATCH_QUERY_SLICE = 20  # 批量查询时每批最大数量

# 电网管理平台生产计划相关API封装
class DwglptPPlanAPI:
    """
    电网管理平台生产计划API封装类
    提供维护检修计划查询等功能
    """
    def __init__(self,dwglpt_http:DwglptHttp):
        """
        初始化生产计划API实例
        Args:
            dwglpt_http: 电网管理平台HTTP会话对象
        """
        self._http = dwglpt_http

    # 获取计划列表
    async def get_plan_list(self,orgCode,planBeginTime,planEndTime,pageNo=1,pageSize=25):
        """
        获取指定组织的维护检修计划列表
        Args:
            orgCode: 组织代码
            planBeginTime: 计划开始时间（格式：YYYY-MM-DD）
            planEndTime: 计划结束时间（格式：YYYY-MM-DD）
            pageNo: 页码
            pageSize: 每页大小
        Returns:
            dict: 计划列表数据
        """
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
        
        # 发送POST请求获取计划列表
        return await self._http.post(
            "http://10.10.21.28/gmp/sp/operationmaintenaceservice/prodplan/ppPlanQuery/queryPlanList",
            req_payload
        )
        

# 测试主流程
async def main():
    """
    测试主函数，演示生产计划API的使用方法
    """
    # print(person_get_detail([
    #     "0A416CFC00D74421B206B89B8D93F766",
    #     "62DFDA59020A454A827087848C892BA5"
    # ]))

    http = DwglptHttp()
    await http.http_init()
    pplanapi = DwglptPPlanAPI(http)

    print(await pplanapi.get_plan_list("04016306","2025-06-25","2025-06-25"))

    await http.http_destory()

if __name__ == "__main__":
    asyncio.run(main())
