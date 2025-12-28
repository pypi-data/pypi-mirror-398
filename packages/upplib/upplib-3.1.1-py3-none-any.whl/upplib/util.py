from upplib import *
from upplib.clean_up_msg import *
from datetime import datetime, timezone, timedelta
from typing import Any, Optional, Union, Callable, List


def get_log_msg(contents: dict,
                replace_n_t=True,
                time_use_in_content=True,
                default_tz: Optional[Union[str, timezone]] = None) -> str | None:
    """
    获得日志
    """
    # time
    # 2025-09-22T03:19:30+07:00
    _time_ = None
    for k in ['_time_', 'time', '__time__']:
        if k in contents and contents[k] != 'null':
            _time_ = to_datetime_str(contents[k], default_tz=default_tz)
            break
    level = None
    if 'level' in contents and contents['level'] != 'null':
        level = contents['level']
    # content
    content = None
    for k in ['content', 'message', 'msg']:
        if k in contents and contents[k] != 'null':
            content = contents[k]
            break
    if content is not None and len(str(content).split(' ')) >= 2:
        time_str = ' '.join(str(content).split(' ')[0:2])
        time_1 = to_datetime(time_str, error_is_none=True)
        # content 中, 含有时间，是以时间开头的字符串
        if time_1 is not None:
            content = content[len(time_str):].strip()
            if _time_ is None or time_use_in_content:
                _time_ = to_datetime_str(time_str, default_tz=default_tz)
    if content is None:
        return None
    if level is not None and content.strip().startswith(level + ' '):
        content = content[len(level + ' '):].strip()
    return ' '.join(filter(lambda s: s is not None, [_time_, level, content.replace('\n', '\\n').replace('\t', '\\t') if replace_n_t else content]))


def get_from_txt(file_name: str = '_start_time_end_time_str.txt',
                 second: int | float = 0.5) -> tuple[datetime | None, datetime | None]:
    """
        从配置文件中获得 datetime
        file_name : 指定文件, 自动忽略掉文件中的 # 开头的行
        second : 获得时间，在 second 基础上，前后冗余多少秒
        获得日志
    """
    date_list = to_list_from_txt(file_name)
    date_list = list(filter(lambda x: len(x) > 0 and not str(x).strip().startswith('#'), date_list))
    if len(date_list) == 0:
        return None, None
    date_time_list = []
    for date_one in date_list:
        date_time_list.append(to_datetime(date_one))
    date_time_list.sort()
    min_time = to_datetime_add(date_time_list[0], seconds=-second)
    max_time = to_datetime_add(date_time_list[-1], seconds=second)
    return min_time, max_time


def get_rpc_context_seq_id_from_txt(file_name: str = 'a.txt') -> list[str] | None:
    """
        "Rpc-Context": "{\"requester\": \"yangpu\", \"seq_id\": \"yangpu__20250928170935489115\", \"biz_type\": \"APPLY\"}"
        从 txt 文件中获得 seq_id , 去重复以后，返回 list(seq_id)
    """
    # 找到所有包含 "Rpc-Context" 的行
    lines = to_list_from_txt(file_name)
    rpc_lines = [line.strip() for line in lines if line.strip().startswith('"Rpc-Context"')]
    seq_ids = set()
    if not rpc_lines:
        return None
    else:
        for i, line in enumerate(rpc_lines, start=1):
            # 提取 JSON 字符串（去掉外层引号）
            json_str = line.split(':', 1)[1].strip().strip('"')
            # 去掉内层的转义符
            clean_json_str = json_str.replace('\\"', '"')
            # 解析 JSON
            data_rpc_context = json.loads(clean_json_str)
            # 获取 seq_id
            seq_id = data_rpc_context.get('seq_id')
            if seq_id:
                seq_ids.add(seq_id)
    r_list = list(seq_ids)
    r_list.sort()
    return r_list


def get_trace_id_from_txt(file_name: str = 'a.txt',
                          trace_id_type: int = 0
                          ) -> list[str] | None:
    """
        2025-09-29T14:56:27.411-06:00 rcs.biz.aspect.RcsReportAspec rcs-gateway-0a0f21a6-488646-218 - Rpc-context:{"requester": "yangpu", "seq_id": "yangpu__20250929144002669164", "biz_type": "APPLY"}
        从 txt 文件中获得 trace_id , 去重复以后，返回 list(trace_id)
    """
    trace_id_lines = to_list_from_txt(file_name)
    trace_id_ids = set()
    if not trace_id_lines:
        return None
    else:
        for trace_id_line in trace_id_lines:
            if trace_id_type == 1:
                try:
                    if ' - ' in trace_id_line:
                        trace_id = trace_id_line[0:130].split(' - ')[1].strip()
                        trace_id_ids.add(trace_id)
                except Exception as e:
                    continue
    r_list = list(trace_id_ids)
    r_list.sort()
    return r_list
