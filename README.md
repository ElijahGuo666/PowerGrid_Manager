# PowerGrid_Manager

电网管理平台流程自动化工具：提供资产域 API 封装、数字身份自动登录、生产计划/工作票/操作票查询、操作票验证、短信推送等能力。

## 功能总览
- 资产域 API：人员/组织信息、维护检修计划、工作票、操作票查询
- 自动登录：对接数字身份（IAM）平台，自动完成登录与会话管理
- 会话持久化：自动保存与复用 cookie，减少重复登录
- 操作票验证：时间逻辑、计划绑定、内容正确性（可扩展）
- 短信推送：支持发送与撤销
- 同步/异步：提供同步接口，部分模块支持异步调用

## 目录结构
```
PowerGrid_Manager/
├── api/
│   ├── __init__.py                 # 导出 DwglptAssetAPI 等主要类与工具
│   ├── dwglpt_api.py               # 三大域 API 封装（资产域已实现主要能力）
│   ├── dwglpt_encrypt.py           # RSA 加密工具
│   ├── dwglpt_http.py              # 会话与请求封装
│   ├── dwglpt_person_api.py        # 人员/组织相关接口
│   ├── dwglpt_pplan_api.py         # 维护检修计划接口
│   ├── iam_api.py                  # 数字身份平台自动登录流程
│   ├── elink_push_real.py          # 短信推送/撤销与签名
│   └── orgcode_result.json         # 组织代码映射
├── oticket_validator/              # 操作票验证器
│   ├── __init__.py
│   ├── oticket_validator.py
│   ├── oticket_usage_example.py
│   └── README.md
├── ddddocr/                        # 验证码识别模型
├── pickle/                         # 已登录会话持久化
├── main.py                         # 资产域 API 综合示例
├── 代码说明手册.txt
├── 使用示例.txt
└── 操作票验证器整理说明.md
```

## 安装与环境
- Python 3.6+
- 建议在可访问相关内网服务的环境运行

安装依赖：
```bash
pip install aiohttp pycryptodome ddddocr fuzzywuzzy requests gmssl
```

## 快速开始

### 1) 初始化与用户信息
```python
from api import DwglptAssetAPI

# 创建资产域 API 实例（自动登录 + 会话持久化）
asset_api = DwglptAssetAPI()

# 当前登录用户
print(asset_api.common_currentUser())
```

### 2) 人员/组织
```python
# 获取某组织下子节点（人员/组织）
children = asset_api.asset_person_choose_children("11739068305E522EE05336050A0A3A5C")

# 批量查询详细信息（人员）
person_ids = [c["key"] for c in children if c["isFolder"] == "false"]
persons = asset_api.asset_person_choose_selectedData(person_ids)

# 批量查询详细信息（组织）
org_ids = [c["key"] for c in children if c["isFolder"] == "true"]
orgs = asset_api.asset_person_choose_selectedData(org_ids, choosetype="org")
```

### 3) 维护检修计划
```python
plans = asset_api.asset_pplan_queryPlanList(
    orgCode=orgs[0]["orgCode"],
    planBeginTime="2025-07-01",
    planEndTime="2025-07-30",
)
```

### 4) 工作票
```python
wtickets = asset_api.asset_wticket_query(
    orgCode=orgs[0]["orgCode"],
    planBeginTime="2025-07-01 00:00:00",
    planEndTime="2025-07-30 00:00:00",
)
```

### 5) 操作票
```python
otickets = asset_api.asset_oticket_query(
    createOname="变电管理三所",
    operationStartTime="2025-08-01 00:00:00",
    operationStartTimeEnd="2025-08-01 23:59:59",
    ticketStateList=["3", "4"],
)
```

### 6) 操作票验证（可选）
```python
from oticket_validator import OTicketValidator

validator = OTicketValidator()
result = validator.validate_all(otickets)
print("是否通过:", result["is_valid"])  # 汇总判断
```

### 7) 短信推送（可选）
```python
from api import elink_push, elink_revoke

ok, ret = elink_push("13800138000", "测试短信")
if ok:
    print("发送成功，消息ID:", ret)
    # elink_revoke(ret)
else:
    print("发送失败:", ret)
```

## 核心模块说明
- api/dwglpt_api.py
  - DwglptBaseAPI：自动登录、会话持久化、通用 GET/POST、`common_currentUser`
  - DwglptAssetAPI：
    - `asset_person_choose_children(pid)`
    - `asset_person_choose_selectedData(pids, choosetype="user"|"org")`
    - `asset_pplan_queryPlanList(orgCode, planBeginTime, planEndTime)`
    - `asset_wticket_query(orgCode, planBeginTime, planEndTime)`
    - `asset_oticket_query(createOname, operationStartTime, operationStartTimeEnd, ticketStateList)`
- api/iam_api.py：数字身份平台自动登录流程（验证码识别、证书签名、业务系统会话获取）
- api/dwglpt_http.py：请求封装与会话复用
- api/elink_push_real.py：短信推送 `elink_push`、撤销 `elink_revoke`、签名与请求构造
- oticket_validator/：操作票验证（时间逻辑/计划绑定/内容正确性，可扩展）

## 更多示例与文档
- `使用示例.txt`：从基础到高级的完整示例
- `api/README.md`：API 子模块详情
- `oticket_validator/README.md`：操作票验证器说明
- `代码说明手册.txt`：模块设计与调用链说明

## 注意事项
1. 需要可访问相关内网接口的网络环境。
2. 首次登录会将会话持久化至 `pickle/` 目录；失效后会自动重新登录。
3. 部分功能依赖可选库（如 `ddddocr`、`gmssl`），未安装将影响对应能力。
4. 时间参数格式：计划接口使用 `YYYY-MM-DD`；票据接口使用 `YYYY-MM-DD HH:mm:ss`。

## 许可证
请见 `LICENSE` 文件。
