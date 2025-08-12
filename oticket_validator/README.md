# 操作票验证器包

## 文件夹结构

```
oticket_validator/
├── __init__.py                    # 包初始化文件
├── oticket_validator.py           # 核心验证器类
├── oticket_usage_example.py       # 详细使用示例
├── test_oticket_validator_simple.py  # 测试脚本
├── test_oticket_validator.py      # 完整测试脚本
├── 使用示例.py                    # 在main.py中的集成示例
├── 操作票验证器说明.md            # 详细说明文档
├── README_操作票验证器.md         # 快速开始指南
└── README.md                      # 本文件
```

## 快速使用

### 在main.py中使用

```python
# 在main.py中导入和使用
from oticket_validator import OTicketValidator

# 创建验证器
validator = OTicketValidator()

# 验证操作票数据
result = validator.validate_all(otickets)

# 查看结果
print(f"验证结果: {'通过' if result['is_valid'] else '不通过'}")
```

### 单独使用

```python
# 导入验证器
from oticket_validator import OTicketValidator

# 创建验证器实例
validator = OTicketValidator()

# 只验证时间逻辑
time_result = validator.validate_time_logic(otickets)

# 只验证计划绑定
plan_result = validator.validate_plan_binding(otickets)

# 只验证内容正确性
content_result = validator.validate_content_correctness(otickets)
```

## 运行测试

```bash
# 运行简化测试
python oticket_validator/test_oticket_validator_simple.py

# 运行完整测试
python oticket_validator/test_oticket_validator.py

# 运行使用示例
python oticket_validator/oticket_usage_example.py

# 运行集成示例
python oticket_validator/使用示例.py
```

## 主要功能

1. **时间逻辑验证** - 验证操作票时间顺序和人员时间冲突
2. **计划绑定验证** - 验证操作票是否关联了检修计划
3. **内容正确性验证** - 验证操作票内容的完整性和准确性（预留功能）

## 文件说明

- `__init__.py` - 包初始化文件，导出主要类
- `oticket_validator.py` - 核心验证器类，包含所有验证逻辑
- `oticket_usage_example.py` - 详细的使用示例和错误处理
- `test_oticket_validator_simple.py` - 简化的测试脚本
- `test_oticket_validator.py` - 完整的测试脚本
- `使用示例.py` - 展示如何在main.py中集成验证器
- `操作票验证器说明.md` - 详细的功能说明文档
- `README_操作票验证器.md` - 快速开始指南

## 注意事项

1. 确保在项目根目录下运行main.py
2. 验证器会自动处理缺失字段和格式错误
3. 时间字段必须使用 `YYYY-MM-DD HH:mm:ss` 格式
4. 可以根据具体需求扩展内容验证功能
5. **时间顺序验证**：验证器不依赖数据传入时的键值顺序，严格按照预定义的时间逻辑顺序进行验证

## 最新更新

### v1.0.4 - 操作票标识符简化
- **日期**: 2024-12-19
- **更新内容**: 
  - 简化了 `_get_ticket_identifier` 方法的逻辑
  - 由于确认传入的操作票数据肯定会包括起始票号、结束票号、工作地点的信息，移除了复杂的分类判断逻辑
  - 直接使用起始票号、结束票号和工作地点的组合构建标识符
  - 代码更加简洁和高效
  - 详细说明请参考：`test_simplified_identifier.py`

### v1.0.3 - 操作票标识符更新
- 更新了操作票标识符逻辑，使用起始票号、结束票号和工作地点的组合
- 支持多种字段名称：`startTicketNumber`、`startTicketNo`、`endTicketNumber`、`endTicketNo`、`workLocation`、`location`、`workPlace`
- 确保不同工作地点的相同票号范围不会产生冲突
- 提供更详细和准确的错误信息
- 详细说明请参考：`操作票标识符更新说明.md`

### v1.0.2 - 起始票号处理
- 优化了操作票标识符的显示，优先使用起始票号
- 支持多种字段名称：`startTicketNumber`、`startTicketNo`、`ticketNumber`、`ticketNo`、`ticketId`、`id`
- 提供更准确和有用的错误信息
- 详细说明请参考：`起始票号处理说明.md`

### v1.0.1 - 时间顺序验证修复
- 修复了时间逻辑验证在处理不同键值顺序数据时的问题
- 现在无论操作票数据来自哪个数据源，无论键值顺序如何，都能正确进行时间逻辑验证
- 详细说明请参考：`时间顺序验证修复说明.md` 