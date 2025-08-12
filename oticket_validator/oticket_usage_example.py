#!/usr/bin/env python3
# -*- coding: UTF-8 -*- 

import dwglpt_api
from oticket_validator import OTicketValidator
import json

def main():
    """
    操作票验证使用示例
    """
    print("=== 操作票验证器使用示例 ===\n")
    
    # 1. 创建资产域API实例
    print("1. 初始化资产域API...")
    asset_api = dwglpt_api.DwglptAssetAPI()
    
    # 2. 查询操作票数据
    print("2. 查询操作票数据...")
    try:
        otickets_response = asset_api.asset_oticket_query(
            "变电管理三所",
            "2025-08-01 00:00:00",
            "2025-08-01 23:59:59",
            ["3", "4"]
        )
        
        otickets = otickets_response.get("list", [])
        print(f"查询到 {len(otickets)} 张操作票")
        
        if not otickets:
            print("未查询到操作票数据，使用示例数据进行演示...")
            # 使用示例数据
            otickets = get_sample_otickets()
            
    except Exception as e:
        print(f"查询操作票失败: {e}")
        print("使用示例数据进行演示...")
        otickets = get_sample_otickets()
    
    # 3. 创建操作票验证器
    print("3. 创建操作票验证器...")
    validator = OTicketValidator()
    
    # 4. 执行验证
    print("4. 执行操作票验证...")
    result = validator.validate_all(otickets)
    
    # 5. 输出验证结果
    print("\n=== 验证结果 ===")
    print_validation_result(result)
    
    # 6. 详细分析
    print("\n=== 详细分析 ===")
    analyze_validation_result(result, otickets)

def get_sample_otickets():
    """
    获取示例操作票数据
    """
    return [
        {
            'id': 'OT001',
            'receiveOrderTime': '2025-08-01 08:00:00',
            'fillTicketTime': '2025-08-01 08:30:00',
            'operationStartTime': '2025-08-01 09:00:00',
            'operationEndTime': '2025-08-01 11:00:00',
            'reportTime': '2025-08-01 11:30:00',
            'operatorName': '张三',
            'guardianName': '李四',
            'planNumber': 'P20250801001',
            'workContent': '110kV母线停电检修'
        },
        {
            'id': 'OT002',
            'receiveOrderTime': '2025-08-01 10:00:00',
            'fillTicketTime': '2025-08-01 10:30:00',
            'operationStartTime': '2025-08-01 11:00:00',  # 与OT001时间重叠
            'operationEndTime': '2025-08-01 13:00:00',
            'reportTime': '2025-08-01 13:30:00',
            'operatorName': '张三',  # 与OT001操作人相同
            'guardianName': '王五',
            'planNumber': 'P20250801002',
            'workContent': '220kV开关检修'
        },
        {
            'id': 'OT003',
            'receiveOrderTime': '2025-08-01 14:00:00',
            'fillTicketTime': '2025-08-01 14:30:00',
            'operationStartTime': '2025-08-01 15:00:00',
            'operationEndTime': '2025-08-01 17:00:00',
            'reportTime': '2025-08-01 17:30:00',
            'operatorName': '赵六',
            'guardianName': '钱七',
            # 没有计划编号，用于测试计划绑定验证
            'workContent': '设备维护'
        }
    ]

def print_validation_result(result):
    """
    打印验证结果
    """
    print(f"总体验证结果: {'✅ 通过' if result['is_valid'] else '❌ 不通过'}")
    print(f"总票数: {result['summary']['total_tickets']}")
    print(f"时间错误数: {result['summary']['time_errors']}")
    print(f"计划绑定错误数: {result['summary']['plan_errors']}")
    print(f"内容错误数: {result['summary']['content_errors']}")
    
    # 时间验证结果
    time_result = result['time_validation']
    if not time_result['is_valid']:
        print("\n🔍 时间逻辑验证:")
        for error in time_result['single_ticket_errors']:
            print(f"  ❌ {error}")
        for error in time_result['multi_ticket_errors']:
            print(f"  ❌ {error}")
    else:
        print("\n✅ 时间逻辑验证通过")
    
    # 计划绑定验证结果
    plan_result = result['plan_validation']
    if not plan_result['is_valid']:
        print("\n🔍 计划绑定验证:")
        for ticket in plan_result['unbound_tickets']:
            print(f"  ❌ {ticket} 未绑定计划")
    else:
        print("\n✅ 计划绑定验证通过")
    
    # 内容验证结果
    content_result = result['content_validation']
    if not content_result['is_valid']:
        print("\n🔍 内容正确性验证:")
        for error in content_result['errors']:
            print(f"  ❌ {error}")
    else:
        print("\n✅ 内容正确性验证通过")

def analyze_validation_result(result, otickets):
    """
    详细分析验证结果
    """
    print("📊 验证统计:")
    
    # 时间验证分析
    time_result = result['time_validation']
    print(f"  时间验证: {len(time_result['single_ticket_errors'])} 个单票错误, {len(time_result['multi_ticket_errors'])} 个多票冲突")
    
    # 计划绑定分析
    plan_result = result['plan_validation']
    bound_count = len(plan_result['bound_tickets'])
    unbound_count = len(plan_result['unbound_tickets'])
    print(f"  计划绑定: {bound_count} 张已绑定, {unbound_count} 张未绑定")
    
    # 内容验证分析
    content_result = result['content_validation']
    print(f"  内容验证: {len(content_result['errors'])} 个错误, {len(content_result['warnings'])} 个警告")
    
    # 建议
    print("\n💡 改进建议:")
    if not result['is_valid']:
        if time_result['single_ticket_errors'] or time_result['multi_ticket_errors']:
            print("  - 检查操作票时间逻辑，确保时间顺序正确")
            print("  - 避免同一人员同时操作多张票")
        
        if plan_result['unbound_tickets']:
            print("  - 为未绑定的操作票关联相应的检修计划")
        
        if content_result['errors']:
            print("  - 完善操作票内容，确保信息完整准确")
    else:
        print("  - 所有验证通过，操作票数据质量良好")

def validate_specific_tickets():
    """
    验证特定操作票的示例
    """
    print("\n=== 特定操作票验证示例 ===")
    
    validator = OTicketValidator()
    
    # 只验证时间逻辑
    sample_tickets = get_sample_otickets()
    time_result = validator.validate_time_logic(sample_tickets)
    print("时间逻辑验证结果:", "通过" if time_result['is_valid'] else "不通过")
    
    # 只验证计划绑定
    plan_result = validator.validate_plan_binding(sample_tickets)
    print("计划绑定验证结果:", "通过" if plan_result['is_valid'] else "不通过")
    
    # 只验证内容正确性
    content_result = validator.validate_content_correctness(sample_tickets)
    print("内容正确性验证结果:", "通过" if content_result['is_valid'] else "不通过")

if __name__ == "__main__":
    main()
    validate_specific_tickets() 