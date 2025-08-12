#!/usr/bin/env python3
# -*- coding: UTF-8 -*- 

import datetime
from typing import List, Dict, Any, Tuple, Optional
import logging

# 设置日志
logger = logging.getLogger(__name__)


def _to_millis(timestamp_value: Any) -> Optional[int]:
    """将多种时间表示转为毫秒时间戳。

    支持:
    - int/float: 直接认为是毫秒
    - 纯数字字符串: 解析为毫秒
    - 日期时间字符串: 按常见格式解析后转为毫秒
    """
    if timestamp_value is None:
        return None

    # int / float
    if isinstance(timestamp_value, (int, float)):
        try:
            ivalue = int(timestamp_value)
            return ivalue
        except Exception:
            return None

    # string
    if isinstance(timestamp_value, str):
        text = timestamp_value.strip()
        if not text:
            return None
        if text.isdigit():
            try:
                return int(text)
            except Exception:
                return None

        # 尝试多种常见格式
        dt_formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y/%m/%d %H:%M:%S',
            '%Y-%m-%d',
            '%Y/%m/%d',
        ]
        for fmt in dt_formats:
            try:
                dt = datetime.datetime.strptime(text, fmt)
                # 认为本地时间，转毫秒
                return int(dt.timestamp() * 1000)
            except Exception:
                continue
        return None

    return None


class OTicketValidator:
    """
    操作票验证器

    提供三大核心校验：
    - validate_time(otickets): 时间逻辑（单票顺序 + 多票冲突）
    - validate_plan_binding(otickets, plan_list=None): 检修计划绑定
    - validate_content(otickets): 内容规范性和完整性

    统一返回“错误列表”而非布尔标志：
    - 若无错误，返回空列表 []
    - 若有错误，列表中每个元素都是“仅包含与错误相关字段 + error 文案”的字典
    """

    def __init__(self) -> None:
        """初始化操作票验证器"""
        # 需求文档中涉及的时间顺序：受令时间 -> 填票时间 -> 操作开始 -> 操作结束 -> 汇报时间
        # 字段在不同来源中命名可能不同，做兼容映射
        self.time_field_candidates: Dict[str, List[str]] = {
            'receive': ['receiveOrderTime', 'takeOrderTime'],          # 受令/接单
            'fill': ['fillTicketTime', 'generateDate', 'createTime'],  # 填票/生成/创建
            'start': ['operationStartTime'],                           # 操作开始
            'end': ['operationEndTime'],                               # 操作结束
            'report': ['reportTime'],                                  # 汇报
        }

    # -------- 标识符与通用提取 --------
    def _get_ticket_identifier(self, ticket: Dict[str, Any], ticket_index: int) -> str:
        """获取操作票标识符，优先使用起始/结束序号与功能位置。"""
        start_no = (
            ticket.get('serialNoStart')
            or ticket.get('startTicketNumber')
            or ticket.get('startTicketNo')
        )
        end_no = (
            ticket.get('serialNoEnd')
            or ticket.get('endTicketNumber')
            or ticket.get('endTicketNo')
        )
        location = (
            ticket.get('functionLocationName')
            or ticket.get('workLocation')
            or ticket.get('location')
            or ticket.get('workPlace')
        )
        base = f"起始票号: {start_no}, 结束票号: {end_no}, 工作地点: {location}"
        fallback = ticket.get('id') or ticket.get('ticketId') or ticket.get('ticketNo') or f"#{ticket_index}"
        return f"{base} (id={fallback})"

    def _format_ms(self, millis: Optional[int]) -> Optional[str]:
        """将毫秒时间戳格式化为 'YYYY-MM-DD HH:MM:SS' 字符串。"""
        if millis is None:
            return None
        try:
            dt = datetime.datetime.fromtimestamp(millis / 1000)
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            return None

    def _first_available_millis(self, ticket: Dict[str, Any], keys: List[str]) -> Optional[int]:
        for k in keys:
            if k in ticket:
                ms = _to_millis(ticket.get(k))
                if ms is not None:
                    return ms
        return None

    def _collect_common_fields(self, ticket: Dict[str, Any]) -> Dict[str, Any]:
        """收集要求输出的公共字段，并将时间统一转为字符串。"""
        receive_ms = self._first_available_millis(ticket, self.time_field_candidates['receive'])
        fill_ms = self._first_available_millis(ticket, self.time_field_candidates['fill'])
        start_ms = self._first_available_millis(ticket, self.time_field_candidates['start'])
        end_ms = self._first_available_millis(ticket, self.time_field_candidates['end'])
        report_ms = self._first_available_millis(ticket, self.time_field_candidates['report'])

        return {
            'serialNoStart': ticket.get('serialNoStart'),
            'serialNoEnd': ticket.get('serialNoEnd'),
            'functionLocationName': ticket.get('functionLocationName'),
            'takeOrderTime': self._format_ms(receive_ms),
            'generateDate': self._format_ms(fill_ms),
            'operationStartTime': self._format_ms(start_ms),
            'operationEndTime': self._format_ms(end_ms),
            'reportTime': self._format_ms(report_ms),
            'operatorUnames': ticket.get('operatorUnames'),
            'guardianUnames': ticket.get('guardianUnames'),
            'watchUname': ticket.get('watchUname'),
        }

    # -------- 需求方法：validate_time --------
    def validate_time(self, otickets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """检查操作票的时间逻辑，包括单票顺序与多票冲突。

        返回值为错误列表，每个元素是仅含相关字段的数据与错误信息：
        [
          {
            ...相关字段,
            'errorInfo': '错误信息'
          },
          ...
        ]
        """
        errors: List[Dict[str, Any]] = []
        if not otickets:
            return errors

        # 单票顺序校验
        for idx, ticket in enumerate(otickets):
            ticket_identifier = self._get_ticket_identifier(ticket, idx)
            receive_ms = self._first_available_millis(ticket, self.time_field_candidates['receive'])
            fill_ms = self._first_available_millis(ticket, self.time_field_candidates['fill'])
            start_ms = self._first_available_millis(ticket, self.time_field_candidates['start'])
            end_ms = self._first_available_millis(ticket, self.time_field_candidates['end'])
            report_ms = self._first_available_millis(ticket, self.time_field_candidates['report'])

            def push_err(final_msg: str) -> None:
                data = self._collect_common_fields(ticket)
                # 错误信息最后插入，确保为最后一个键
                data['errorInfo'] = final_msg
                errors.append(data)

            # 缺失检查
            missing_fields = []
            if receive_ms is None:
                missing_fields.append('受令时间')
            if fill_ms is None:
                missing_fields.append('填票时间')
            if start_ms is None:
                missing_fields.append('操作开始时间')
            if end_ms is None:
                missing_fields.append('操作结束时间')
            if report_ms is None:
                missing_fields.append('汇报时间')
            if missing_fields:
                msg = f"操作票（{ticket_identifier.split(' (id=')[0]}），缺少时间字段：" + '、'.join(missing_fields)
                push_err(msg)
                # 即便缺失，也继续做能做的顺序检查

            # 顺序检查（仅在两端都有值时比较）
            def check_pair(prev_label: str, prev_ms: Optional[int], next_label: str, next_ms: Optional[int]) -> None:
                if prev_ms is not None and next_ms is not None and prev_ms > next_ms:
                    prev_str = self._format_ms(prev_ms)
                    next_str = self._format_ms(next_ms)
                    msg = (
                        f"操作票（{ticket_identifier.split(' (id=')[0]}），存在时间逻辑错误："
                        f"{prev_label}({prev_str}) 晚于 {next_label}({next_str})"
                    )
                    push_err(msg)

            check_pair('受令时间', receive_ms, '填票时间', fill_ms)
            check_pair('填票时间', fill_ms, '操作开始时间', start_ms)
            check_pair('操作开始时间', start_ms, '操作结束时间', end_ms)
            check_pair('操作结束时间', end_ms, '汇报时间', report_ms)

        # 多票冲突校验（按人员）
        def expand_names(name_field: Any) -> List[str]:
            if not name_field:
                return []
            if isinstance(name_field, str):
                # 逗号/中文逗号/空白分隔
                parts = [p.strip() for p in name_field.replace('，', ',').split(',')]
                return [p for p in parts if p]
            return []

        groups: Dict[Tuple[str, str], List[Tuple[int, Dict[str, Any]]]] = {}
        role_fields = [('操作人', 'operatorUnames'), ('监护人', 'guardianUnames'), ('值班负责人', 'watchUname')]
        for idx, ticket in enumerate(otickets):
            start_ms = self._first_available_millis(ticket, self.time_field_candidates['start'])
            end_ms = self._first_available_millis(ticket, self.time_field_candidates['end'])
            if start_ms is None or end_ms is None:
                continue
            for role_label, field_name in role_fields:
                for person in expand_names(ticket.get(field_name)):
                    key = (role_label, person)
                    groups.setdefault(key, []).append((idx, {'start': start_ms, 'end': end_ms}))

        for (role_label, person), ranges in groups.items():
            # 两两比较
            for i in range(len(ranges)):
                for j in range(i + 1, len(ranges)):
                    idx_i, r_i = ranges[i]
                    idx_j, r_j = ranges[j]
                    if not (r_i['end'] <= r_j['start'] or r_j['end'] <= r_i['start']):
                        t_i = otickets[idx_i]
                        t_j = otickets[idx_j]
                        # 生成两个错误记录：分别针对两张票
                        ti = self._collect_common_fields(t_i)
                        tj = self._collect_common_fields(t_j)

                        range_i = f"{self._format_ms(r_i['start'])}~{self._format_ms(r_i['end'])}"
                        range_j = f"{self._format_ms(r_j['start'])}~{self._format_ms(r_j['end'])}"

                        # 另一张票的简要标识（不含 id）
                        other_j = self._get_ticket_identifier(t_j, idx_j).split(' (id=')[0]
                        other_i = self._get_ticket_identifier(t_i, idx_i).split(' (id=')[0]

                        # 针对第一张票的错误
                        ti['errorInfo'] = (
                            f"{role_label}{person}同时持有多张操作票，与{other_j}在操作时间上有重叠："
                            f"{range_i} 与 {range_j} 时间重叠"
                        )
                        errors.append(ti)

                        # 针对第二张票的错误
                        tj['errorInfo'] = (
                            f"{role_label}{person}同时持有多张操作票，与{other_i}在操作时间上有重叠："
                            f"{range_j} 与 {range_i} 时间重叠"
                        )
                        errors.append(tj)
        
        return errors
    
    # -------- 需求方法：validate_plan_binding --------
    def validate_plan_binding(self, otickets: List[Dict[str, Any]], plan_list: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """检查操作票是否正确绑定了检修计划。

        - 若提供 plan_list，则要求 `workPlanIds` 或 `workPlanNos` 存在且在列表中。
        - 若未提供 plan_list，则只要求字段存在且非空。

        返回错误列表，每个元素含相关字段与错误信息。
        """
        errors: List[Dict[str, Any]] = []
        if not otickets:
            return errors

        plan_set = set(plan_list or [])

        for idx, ticket in enumerate(otickets):
            plan_id = (ticket.get('workPlanIds') or ticket.get('workPlanId') or '').strip() if isinstance(ticket.get('workPlanIds') or ticket.get('workPlanId'), str) else (ticket.get('workPlanIds') or ticket.get('workPlanId'))
            plan_no = (ticket.get('workPlanNos') or ticket.get('workPlanNo') or '').strip() if isinstance(ticket.get('workPlanNos') or ticket.get('workPlanNo'), str) else (ticket.get('workPlanNos') or ticket.get('workPlanNo'))

            bound_present = bool(plan_id) or bool(plan_no)
            if not bound_present:
                data = self._collect_common_fields(ticket)
                # 错误信息最后插入
                data['errorInfo'] = '未绑定检修计划（缺少 workPlanIds/workPlanNos）'
                errors.append(data)
                continue
                
            if plan_list is not None:
                id_ok = (str(plan_id) in plan_set) if plan_id else False
                no_ok = (str(plan_no) in plan_set) if plan_no else False
                if not (id_ok or no_ok):
                    data = self._collect_common_fields(ticket)
                    data['workPlanIds'] = plan_id
                    data['workPlanNos'] = plan_no
                    # 错误信息最后插入
                    data['errorInfo'] = '绑定的检修计划不在允许列表中'
                    errors.append(data)
        
        return errors
    
    # -------- 需求方法：validate_content --------
    def validate_content(self, otickets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """检查操作票内容的规范性和完整性（基础规则，可按需扩展）。

        规则（最小集合）：
        - 必填：`operationTask`、`functionLocationName`、`operatorUnames`、`guardianUnames`
        - 步骤：若存在 `stepCount` 与 `mainStepCount`，要求 `0 < mainStepCount <= stepCount`
        """
        errors: List[Dict[str, Any]] = []
        if not otickets:
            return errors

        for _, ticket in enumerate(otickets):
            def push_err(msg: str) -> None:
                data = self._collect_common_fields(ticket)
                # 错误信息最后插入
                data['errorInfo'] = msg
                errors.append(data)

            # 必填项
            required_fields = [
                ('operationTask', '操作任务(operationTask)为空'),
                ('functionLocationName', '工作地点(functionLocationName)为空'),
                ('operatorUnames', '操作人(operatorUnames)为空'),
                ('guardianUnames', '监护人(guardianUnames)为空'),
            ]
            for key, msg in required_fields:
                val = ticket.get(key)
                if val is None or (isinstance(val, str) and not val.strip()):
                    push_err(msg)

            # 步骤约束
            step_count = ticket.get('stepCount')
            main_step_count = ticket.get('mainStepCount')
            try:
                if step_count is not None and main_step_count is not None:
                    sc = int(step_count)
                    msc = int(main_step_count)
                    if sc <= 0 or msc <= 0 or msc > sc:
                        push_err(f'步骤数不合法: stepCount={sc}, mainStepCount={msc}')
            except Exception:
                push_err('步骤数字段格式错误')

        return errors

    # 不保留旧接口：本文件只导出上述三大方法


if __name__ == '__main__':
    # 使用示例：仅用于快速手工验证（生产环境不要依赖此输出格式）
    sample = [{
        'serialNoStart': 2500058,
        'serialNoEnd': 2500058,
        'functionLocationName': '35kV镇龙站',
        'takeOrderTime': 1754000220000,
        'generateDate': 1754000507000,
        'operationStartTime': 1754000580000,
        'operationEndTime': 1754000880000,
        'reportTime': 1754001000000,
        'operatorUnames': '李春娇',
        'guardianUnames': '凌福',
        'watchUname': '凌福',
        'workPlanIds': '5c78e23da25a45f4bdb0c9e85c3fcc42',
        'workPlanNos': 'SCWH0401250623001803',
        'operationTask': '将35kV百镇线312线路全部保护投入',
        'stepCount': 10,
        'mainStepCount': 3,
    }]

    v = OTicketValidator()
    print('validate_time ->', v.validate_time(sample))
    print('validate_plan_binding ->', v.validate_plan_binding(sample))
    print('validate_content ->', v.validate_content(sample))