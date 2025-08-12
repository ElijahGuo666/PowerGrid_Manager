#!/usr/bin/env python3
# -*- coding: UTF-8 -*- 

"""
操作票验证器在main.py中的使用示例
"""

import dwglpt_api
from oticket_validator import OTicketValidator

def validate_otickets_in_main():
    """
    在main.py中集成操作票验证器的示例
    """
    print("=== 操作票验证器集成示例 ===\n")
    
    # 1. 创建资产域API实例
    asset_api = dwglpt_api.DwglptAssetAPI()
    
    # 2. 查询操作票数据
    try:
        otickets = asset_api.asset_oticket_query(
            "变电管理三所",
            "2025-08-01 00:00:00",
            "2025-08-01 23:59:59",
            ["3", "4"]
        )["list"]
        
        print(f"查询到 {len(otickets)} 张操作票")
        
        if not otickets:
            print("未查询到操作票数据，使用示例数据...")
            otickets = get_sample_otickets()
            
    except Exception as e:
        print(f"查询操作票失败: {e}")
        print("使用示例数据...")
        otickets = get_sample_otickets()
    
    # 3. 使用操作票验证器
    try:
        # 导入验证器
        from oticket_validator import OTicketValidator
        
        # 创建验证器实例
        validator = OTicketValidator()
        
        # 执行验证
        result = validator.validate_all(otickets)
        
        # 输出验证结果
        print(f"\n验证结果: {'通过' if result['is_valid'] else '不通过'}")
        print(f"总票数: {result['summary']['total_tickets']}")
        print(f"时间错误数: {result['summary']['time_errors']}")
        print(f"计划绑定错误数: {result['summary']['plan_errors']}")
        print(f"内容错误数: {result['summary']['content_errors']}")
        
        # 详细错误信息
        if not result['time_validation']['is_valid']:
            print("\n时间验证错误:")
            for error in result['time_validation']['single_ticket_errors']:
                print(f"  - {error}")
            for error in result['time_validation']['multi_ticket_errors']:
                print(f"  - {error}")
        
        if not result['plan_validation']['is_valid']:
            print("\n计划绑定错误:")
            for ticket in result['plan_validation']['unbound_tickets']:
                print(f"  - {ticket} 未绑定计划")
        
        # 4. 根据验证结果给出建议
        print("\n=== 改进建议 ===")
        if result['is_valid']:
            print("✅ 所有验证通过，操作票数据质量良好")
        else:
            if result['summary']['time_errors'] > 0:
                print("⚠️  建议检查操作票时间逻辑")
            if result['summary']['plan_errors'] > 0:
                print("⚠️  建议为未绑定的操作票关联检修计划")
            if result['summary']['content_errors'] > 0:
                print("⚠️  建议完善操作票内容信息")
                
    except ImportError as e:
        print(f"❌ 导入操作票验证器失败: {e}")
        print("请确保oticket_validator文件夹存在且包含必要的文件")
    except Exception as e:
        print(f"❌ 操作票验证失败: {e}")

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
            'operatorName': '张三',  # 同一操作人
            'guardianName': '王五',
            'planNumber': 'P20250801002',
            'workContent': '220kV开关检修'
        }
    ]

if __name__ == "__main__":
    validate_otickets_in_main() 