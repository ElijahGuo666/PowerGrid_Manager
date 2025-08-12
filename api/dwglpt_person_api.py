import json
import asyncio
from .dwglpt_encrypt import encrypt_id
from .dwglpt_http import DwglptHttp
from pprint import pprint
import math
from fuzzywuzzy import process
import logging
import os

BATCH_QUERY_SLICE = 20  # 批量查询时每批最大数量
logger = logging.getLogger(__name__)

# 电网管理平台人员相关API封装
class DwglptPersonAPI:
    """
    电网管理平台人员和组织API封装类
    提供人员信息查询、组织信息查询、用户组织链查询等功能
    """
    def __init__(self,dwglpt_http:DwglptHttp):
        """
        初始化人员API实例
        Args:
            dwglpt_http: 电网管理平台HTTP会话对象
        """
        self._http = dwglpt_http

    # 批量获取人员或组织详情
    async def get_detail(self,pids,choosetype="user"):
        """
        批量获取人员或组织的详细信息
        Args:
            pids: 人员或组织ID列表
            choosetype: 查询类型，"user"表示人员，"org"表示组织
        Returns:
            list: 人员或组织详细信息列表，格式为[{...}, ...]
        """
        if len(pids) == 0:
            return []

        pids_encrypted = []

        # 对每个ID进行加密
        for pid in pids:
            pids_encrypted.append(encrypt_id(pid))

        sliced_result = []

        # 分批请求，防止单次请求过大
        for iter in range(math.ceil(len(pids_encrypted) / BATCH_QUERY_SLICE)):
            iter_pids = pids_encrypted[
                iter * BATCH_QUERY_SLICE : 
                (iter+1) * BATCH_QUERY_SLICE
            ]
            # print(iter,iter_pids)
        
            req_payload = {
                "chooseType":choosetype,
                "ids":iter_pids,
                "showLevel":1,
                "showOrder":"order"
            }

            sliced_result += await self._http.post(
                "http://10.10.21.28/api/jadp/personnel/choose/SelectedData",
                req_payload
            )
        
        return sliced_result
        
    # 获取某个组织/人员的下级节点
    async def get_children(self,pid):
        """
        获取指定节点下的子节点（人员或组织）
        Args:
            pid: 父节点ID
        Returns:
            list: 子节点列表，格式为[{...}, ...]
        """
        return await self._http.get(
            f"http://10.10.21.28/api/jadp/personnel/choose/{pid}/children?id={pid}&userType=1&orgTypes="
        )

    # 获取当前登录用户信息
    async def get_whoami(self):  
        """
        获取当前登录用户的详细信息
        Returns:
            dict: 当前用户详细信息
        """
        return await self._http.get("http://10.10.21.28/api/jadp/auth/currentUser")

    # 获取用户所属组织链
    async def get_user_org_chain(self,pid):
        """
        获取用户所属组织链（从根到当前组织）
        Args:
            pid: 用户ID
        Returns:
            list: 组织链信息
        """
        return await self._http.get(
            f"http://10.10.21.28/api/jadp/personnel/orgs/security/queryOrganizationChainByUserId?userId={pid}"
        )

# 读取组织代码映射表
curr_dir = os.path.abspath(os.path.dirname(__file__))
logger.debug(curr_dir)
with open(os.path.join(curr_dir,"orgcode_result.json"),"r",encoding="utf-8") as f:
    orgcodes = json.loads(f.read())
orgcode_dict = {}
for og in orgcodes:
    # 简化组织名称，去掉前缀
    simptitle = og["title"].replace("中国南方电网有限责任公司/广西电网有限责任公司/南宁供电局/","")
    orgcode_dict[simptitle] = og["orgCode"]

# 解析自然语言表达的orgname，转为ID。
def resolve_org_code(orgname:str):
    """
    通过自然语言组织名称模糊匹配获取组织代码
    Args:
        orgname: 组织名称
    Returns:
        list: 匹配结果列表，每个元素包含[组织名, 匹配度, 组织代码]
    """
    if process is None:
        logger.warning("fuzzywuzzy模块未安装，无法进行模糊匹配")
        return []
    
    matches = process.extract(orgname, orgcode_dict.keys(),limit=3)
    logger.debug("matched:%s",matches)
    result = []
    for match in matches:
        result.append([match[0],match[1],orgcode_dict[match[0]]])
    return result

# 测试主流程
async def main():
    """
    测试主函数，演示人员API的使用方法
    """
    # print(person_get_detail([
    #     "0A416CFC00D74421B206B89B8D93F766",
    #     "62DFDA59020A454A827087848C892BA5"
    # ]))

    http = DwglptHttp()
    await http.http_init()
    personapi = DwglptPersonAPI(http)

    # pids_to_query = []

    # # for child in person_get_children("-1"): #南网根目录
    # for child in await personapi.get_children("11739068305E522EE05336050A0A3A5C"): #南宁供电局
    #     if child["isFolder"] == "false":
    #         pids_to_query.append(child["key"])
    #     else:
    #         print("discovered",child["fullName"],child["key"])

    # print(pids_to_query)

    # a = await personapi.get_detail(pids_to_query)
    # print(a)
    # for p in a:
    #     # print(p["name"],p["mobilePhone"])
    #     pprint(p)

    # pprint(await personapi.get_whoami())

    print(await personapi.get_user_org_chain("0A416CFC00D74421B206B89B8D93F766"))

    await http.http_destory()

if __name__ == "__main__":
    # asyncio.run(main())
    print(resolve_org_code("变电三所/站用电源班"))
