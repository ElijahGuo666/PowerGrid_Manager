# 电网管理平台API包

本包提供了电网管理平台三大域（资产域、人资域、计财域）的API封装。

## 文件结构

```
api/
├── __init__.py                    # 包初始化文件，导出主要API类
├── dwglpt_api.py                 # 电网管理平台三大域基础API类
├── dwglpt_encrypt.py             # RSA加密工具模块
├── dwglpt_http.py                # 异步HTTP会话管理类
├── dwglpt_person_api.py          # 人员和组织API封装
├── dwglpt_pplan_api.py           # 生产计划API封装
├── iam_api.py                     # 数字身份认证平台API
└── orgcode_result.json            # 组织代码映射表
```

## 主要功能

### 1. 基础API类 (DwglptBaseAPI)
- 提供通用的登录、会话管理、HTTP请求等功能
- 支持资产域、人资域、计财域三大域

### 2. 资产域API (DwglptAssetAPI)
- 人员和组织信息查询
- 维护检修计划查询
- 工作票查询
- 操作票查询

### 3. 人员API (DwglptPersonAPI)
- 批量获取人员或组织详情
- 获取组织层级结构
- 用户组织链查询

### 4. 生产计划API (DwglptPPlanAPI)
- 维护检修计划查询
- 支持分页和时间范围查询

### 5. HTTP会话管理 (DwglptHttp)
- 异步HTTP请求支持
- 自动cookie管理和持久化
- 会话状态检查

## 使用方法

### 基本导入
```python
from api import DwglptAssetAPI, DwglptPersonAPI, DwglptPPlanAPI

# 创建API实例
asset_api = DwglptAssetAPI()
person_api = DwglptPersonAPI()
plan_api = DwglptPPlanAPI()
```

### 查询人员信息
```python
# 获取组织下的子节点
children = asset_api.asset_person_choose_children("组织ID")

# 批量查询人员详情
persons = asset_api.asset_person_choose_selectedData(["人员ID1", "人员ID2"])
```

### 查询计划信息
```python
# 查询维护检修计划
plans = asset_api.asset_pplan_queryPlanList(
    orgCode="组织代码",
    planBeginTime="2025-07-01",
    planEndTime="2025-07-30"
)
```

## 依赖要求

- Python 3.6+
- requests (用于同步HTTP请求)
- aiohttp (用于异步HTTP请求，可选)
- pycryptodome (用于RSA加密，可选)
- fuzzywuzzy (用于模糊匹配，可选)

## 注意事项

1. 如果缺少可选依赖模块，相关功能会显示警告信息但不会阻止程序运行
2. 所有API调用都需要有效的网络连接和登录凭据
3. 建议在生产环境中安装所有依赖模块以确保完整功能 