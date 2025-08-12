#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
按照《操作票检查程序需求说明》构造输入并测试 `OTicketValidator` 的三个核心校验：
1) validate_time(otickets)
2) validate_plan_binding(otickets, plan_list=None)
3) validate_content(otickets)

运行方式（在项目根目录执行）：
  python -m oticket_validator.test_requirements_input
或：
  python oticket_validator/test_requirements_input.py
"""

from oticket_validator import OTicketValidator


def build_sample_tickets():
    """构造三张示例操作票：
    - ticket_ok: 完全正确，无时间/计划/内容错误
    - ticket_time_and_content_error: 时间顺序错误 + 缺少必填内容 + 未绑定计划
    - ticket_overlap_and_plan_invalid: 与 ticket_ok 操作人时间重叠 + 计划绑定不在白名单

    时间字段统一使用毫秒级时间戳，字段命名符合需求说明（takeOrderTime/generateDate/operationStartTime/...）。
    """
    # 正确票（A）
    ticket_ok = {
        "id": "OT-A-001",
        "serialNoStart": 2500058,
        "serialNoEnd": 2500058,
        "functionLocationName": "35kV镇龙站",
        "operationTask": "将35kV百镇线312线路全部保护投入",
        # 时间：受令/接单 → 填票/生成 → 开始 → 结束 → 汇报（均为毫秒）
        "takeOrderTime": 1754000220000,
        "generateDate": 1754000507000,
        "operationStartTime": 1754000580000,
        "operationEndTime": 1754000880000,
        "reportTime": 1754001000000,
        # 人员
        "operatorUnames": "张三",
        "guardianUnames": "李四",
        "watchUname": "王五",
        # 步骤
        "stepCount": 10,
        "mainStepCount": 3,
        # 计划绑定（白名单中允许）
        "workPlanIds": "PLAN-OK",
        "workPlanNos": "SCWH0401250623001803",
    }

    # 时间顺序与内容错误票（B）
    ticket_time_and_content_error = {
        "id": "OT-B-002",
        "serialNoStart": 2500060,
        "serialNoEnd": 2500060,
        "functionLocationName": "35kV镇龙站",
        "operationTask": "备用变压器切换",
        # 故意制造时间错误：接单时间 晚于 填票/生成时间
        "takeOrderTime": 1754000700000,   # 晚于 generateDate → 错误
        "generateDate": 1754000500000,
        "operationStartTime": 1754000800000,
        "operationEndTime": 1754000900000,
        "reportTime": 1754001000000,
        # 人员：缺少 guardianUnames（监护人）→ 内容错误
        "operatorUnames": "李四",
        # "guardianUnames": 缺失
        # 步骤：设置为合法
        "stepCount": 5,
        "mainStepCount": 2,
        # 未绑定计划 → 计划错误
        # "workPlanIds": 缺失
        # "workPlanNos": 缺失
    }

    # 时间重叠与计划不在白名单（C）
    ticket_overlap_and_plan_invalid = {
        "id": "OT-C-003",
        "serialNoStart": 2500061,
        "serialNoEnd": 2500061,
        "functionLocationName": "35kV镇龙站",
        "operationTask": "继电保护装置检修",
        # 与 ticket_ok 的操作时间重叠（相同操作人“张三”）
        "takeOrderTime": 1754000400000,
        "generateDate": 1754000505000,
        "operationStartTime": 1754000700000,  # 与 A(1754000580000~1754000880000) 重叠
        "operationEndTime": 1754001100000,
        "reportTime": 1754001200000,
        # 人员
        "operatorUnames": "张三",
        "guardianUnames": "赵六",
        # 步骤：设置为合法
        "stepCount": 6,
        "mainStepCount": 2,
        # 计划绑定但不在白名单
        "workPlanIds": "PLAN-BAD",
    }

    return [ticket_ok, ticket_time_and_content_error, ticket_overlap_and_plan_invalid]


def main():
    print("=== 按需求说明的输入测试 ===\n")
    tickets = build_sample_tickets()
    validator = OTicketValidator()

    # 1) 时间逻辑校验
    print("1) validate_time 结果：")
    time_errors = validator.validate_time(tickets)
    print(time_errors)
    print(f"  错误条数: {len(time_errors)}")
    for i, err in enumerate(time_errors, 1):
        print(f"  [{i}] {err.get('errorInfo')}")
        # 展示关键字段，便于对照
        print(f"      serialNoStart={err.get('serialNoStart')}, serialNoEnd={err.get('serialNoEnd')}, functionLocationName={err.get('functionLocationName')}")
        print(f"      takeOrderTime={err.get('takeOrderTime')}, generateDate={err.get('generateDate')}")
        print(f"      operationStartTime={err.get('operationStartTime')}, operationEndTime={err.get('operationEndTime')}, reportTime={err.get('reportTime')}")
    print()

    # 2) 计划绑定校验（白名单仅允许 PLAN-OK）
    print("2) validate_plan_binding 结果（白名单: ['PLAN-OK']）：")
    plan_errors = validator.validate_plan_binding(tickets, plan_list=["PLAN-OK"])  # 仅允许 PLAN-OK
    print(plan_errors)
    print(f"  错误条数: {len(plan_errors)}")
    for i, err in enumerate(plan_errors, 1):
        print(f"  [{i}] {err.get('errorInfo')}  (workPlanIds={err.get('workPlanIds')}, workPlanNos={err.get('workPlanNos')})")
        # 展示关键字段，便于对照
        print(f"      serialNoStart={err.get('serialNoStart')}, serialNoEnd={err.get('serialNoEnd')}, functionLocationName={err.get('functionLocationName')}")
        print(f"      takeOrderTime={err.get('takeOrderTime')}, generateDate={err.get('generateDate')}")
        print(f"      operationStartTime={err.get('operationStartTime')}, operationEndTime={err.get('operationEndTime')}, reportTime={err.get('reportTime')}")
    print()

    # 3) 内容校验
    print("3) validate_content 结果：")
    content_errors = validator.validate_content(tickets)
    print(content_errors)
    print(f"  错误条数: {len(content_errors)}")
    for i, err in enumerate(content_errors, 1):
        print(f"  [{i}] {err.get('errorInfo')}")
        # 展示关键字段，便于对照
        print(f"      serialNoStart={err.get('serialNoStart')}, serialNoEnd={err.get('serialNoEnd')}, functionLocationName={err.get('functionLocationName')}")
        print(f"      operatorUnames={err.get('operatorUnames')}, guardianUnames={err.get('guardianUnames')}, watchUname={err.get('watchUname')}")


if __name__ == "__main__":
    main()


