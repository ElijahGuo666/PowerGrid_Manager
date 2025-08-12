# 操作票验证器

## 功能概述

操作票验证器是一个用于验证电网管理平台操作票数据质量的Python类，提供以下三个主要验证功能：

### 1. 时间逻辑验证
- **单张票验证**：受令时间 < 填票时间 < 操作开始时间 < 操作结束时间 < 汇报时间
- **多张票验证**：同一操作人或监护人不能同时操作多张票（时间不能重叠）

### 2. 计划绑定验证
- 检查操作票是否关联了检修计划
- 支持多种计划编号字段：`planNumber`、`planId`、`planCode`

### 3. 内容正确性验证
- 预留功能，可根据具体需求扩展
- 可验证操作步骤完整性、安全措施正确性等

## 快速开始

### 基本使用

```python
from oticket_validator import OTicketValidator
import dwglpt_api

# 创建验证器
validator = OTicketValidator()

# 获取操作票数据
asset_api = dwglpt_api.DwglptAssetAPI()
otickets = asset_api.asset_oticket_query(
    "变电管理三所",
    "2025-08-01 00:00:00",
    "2025-08-01 23:59:59",
    ["3", "4"]
)["list"]

# 执行验证
result = validator.validate_all(otickets)

# 查看结果
print(f"验证结果: {'通过' if result['is_valid'] else '不通过'}")
```

### 单独验证

```python
# 只验证时间逻辑
time_result = validator.validate_time_logic(otickets)

# 只验证计划绑定
plan_result = validator.validate_plan_binding(otickets)

# 只验证内容正确性
content_result = validator.validate_content_correctness(otickets)
```

## 文件说明

- `oticket_validator.py` - 主验证器类
- `oticket_usage_example.py` - 使用示例
- `test_oticket_validator_simple.py` - 测试脚本
- `操作票验证器说明.md` - 详细说明文档

## 数据格式

操作票数据应包含以下字段：

```python
{
    'id': 'OT001',                           # 操作票ID
    'receiveOrderTime': '2025-08-01 08:00:00',  # 受令时间
    'fillTicketTime': '2025-08-01 08:30:00',    # 填票时间
    'operationStartTime': '2025-08-01 09:00:00', # 操作开始时间
    'operationEndTime': '2025-08-01 11:00:00',   # 操作结束时间
    'reportTime': '2025-08-01 11:30:00',         # 汇报时间
    'operatorName': '张三',                       # 操作人姓名
    'guardianName': '李四',                       # 监护人姓名
    'planNumber': 'P20250801001',                 # 计划编号
    'workContent': '110kV母线停电检修'              # 工作内容
}
```

## 运行测试

```bash
# 运行测试脚本
python test_oticket_validator_simple.py

# 运行使用示例
python oticket_usage_example.py
```

## 返回结果

验证器返回详细的验证结果，包括：

- `is_valid`: 总体验证结果
- `time_validation`: 时间验证结果
- `plan_validation`: 计划绑定验证结果
- `content_validation`: 内容验证结果
- `summary`: 统计信息

## 扩展功能

可以根据具体需求扩展内容验证功能，例如：

- 操作步骤完整性检查
- 安全措施正确性验证
- 设备编号有效性验证
- 操作人员资质验证
- 工作内容与计划匹配度检查

## 注意事项

1. 时间字段必须使用 `YYYY-MM-DD HH:mm:ss` 格式
2. 验证器会优雅地处理缺失字段和格式错误
3. 对于大量操作票，验证过程可能需要一些时间 