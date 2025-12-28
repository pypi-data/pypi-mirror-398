from upplib import *
from datetime import datetime, timezone, timedelta
from typing import Any, Optional, Union
from aliyun.log import LogClient, GetLogsRequest

from huaweicloudsdkcore.auth.credentials import BasicCredentials
from huaweicloudsdklts.v2.region.lts_region import LtsRegion
from huaweicloudsdklts.v2 import *
from upplib import *


def query_sls_logs(logstore_name: str = '',
                   minute: int = 600,
                   limit: int = 500,
                   query: str = '',
                   query_sql: str = None,
                   trace_id_fixed_length: int = None,
                   replace_n_t: bool = True,
                   order_by_desc: bool = True,
                   remove_repeat_content: bool = False,
                   time_use_in_content: bool = True,
                   config_name: str = '',
                   country: str = '',
                   start_time: datetime | str | None = None,
                   forward_seconds: int = 2,
                   backward_seconds: int = 2,
                   method_length: int = 31,
                   end___time: datetime | str | None = None,
                   append_file: bool = False,
                   only_date_msg: bool = False,
                   msg_delete_prefix: int = 0,
                   file_name_suffix: str = '',
                   clean_up_msg_type: int = 0,
                   default_tz: str = '+07:00') -> None:
    """
        query:
        query_sql  : 当有 query_sql 的时候 query 就会被 覆盖
        replace_n_t: 转义 \\n, \\t 这些符号
        file_name_suffix: 在输出的文件后面加一个后缀
        forward_seconds: 往前查询的秒数
        backward_seconds: 往后查询的秒数
    """
    if start_time is None and end___time is None:
        start_time, end___time = (t[0], t[1]) if (t := get_from_txt()) and t[0] is not None else (get_timestamp() - 60 * minute, get_timestamp())

    if start_time is None and end___time is not None:
        start_time = end___time
        end___time = end___time

    if start_time is not None and end___time is None:
        start_time = start_time
        end___time = start_time

    if query_sql is not None:
        query = query_sql
    if ' limit ' not in query.lower():
        query += ' LIMIT ' + str(limit)
    start_time = get_timestamp(start_time) - forward_seconds
    end___time = get_timestamp(end___time) + backward_seconds
    if not append_file:
        to_print_file(country, logstore_name, mode='w', file_path='', file_name=logstore_name + '_' + str(country) + str(file_name_suffix))
        to_print_file(f'start_time : {to_datetime_str(start_time, tz=default_tz)}')
        to_print_file(f'end___time : {to_datetime_str(end___time, tz=default_tz)}')
    if '\n' not in query:
        for s in [' where ', ' WHERE ', ' order by ']:
            if s in query:
                s1, s2, s3 = query.partition(s)
                query = s1 + '\n' + s2.strip() + ' ' + s3
    to_print_file(query)
    c = get_config_data(config_name)
    response = (LogClient(c.get('endpoint'), c.get('access_key_id'), c.get('access_key_secret'))
                .get_logs(GetLogsRequest(c.get('project_name'), logstore_name, start_time, end___time, line=limit, query=query)))
    logs = response.get_logs()
    log_set = set()
    log_list = []
    for log in logs:
        if (
                msg := clean_up_msg(
                    get_log_msg(log.contents, replace_n_t=replace_n_t, default_tz=default_tz, time_use_in_content=time_use_in_content),
                    method_length=method_length,
                    trace_id_fixed_length=trace_id_fixed_length,
                    clean_up_type=clean_up_msg_type)) is not None:
            msg = simplify_msg(msg, only_date_msg=only_date_msg, msg_delete_prefix=msg_delete_prefix)
            if remove_repeat_content:
                log_set.add(msg)
            else:
                log_list.append(msg)
    if len(log_set) > 0:
        log_list = list(log_set)
        log_list.sort()
    if order_by_desc:
        log_list.reverse()
    to_print_file(f"从日志库中查询, 一共获得 {response.get_count()} 条日志, 处理完了以后, 共 {len(log_list)} 条日志")
    for log in log_list:
        to_print_file(log)
    to_print_file('END__END')


def query_lts_logs(logstore_name: str = '',
                   minute: int = 600,
                   limit: int = 500,
                   query: str = '',
                   trace_id_fixed_length: int = None,
                   query_sql: str = None,
                   replace_n_t: bool = True,
                   order_by_desc: bool = True,
                   remove_repeat_content: bool = False,
                   time_use_in_content: bool = True,
                   config_name: str = 'mx_huaweiyun_lts',
                   project_id='592974556c4a4f8db19f6d5f6fa8b8ad',
                   log_stream_id='f9555059-d0a8-4a8a-acd2-796ac9aeef2e',
                   country: str = '',
                   start_time: datetime | str | None = None,
                   forward_seconds: int = 2,
                   backward_seconds: int = 2,
                   method_length: int = 31,
                   end___time: datetime | str | None = None,
                   append_file: bool = False,
                   only_date_msg: bool = False,
                   msg_delete_prefix: int = 0,
                   file_name_suffix: str = '',
                   clean_up_msg_type: int = 0,
                   default_tz: str = '-06:00') -> None:
    """
        query:
        query_sql  : 当有 query_sql 的时候 query 就会被 覆盖
        replace_n_t: 转义 \\n, \\t 这些符号
        file_name_suffix: 在输出的文件后面加一个后缀
    """
    if start_time is None and end___time is None:
        start_time, end___time = (t[0], t[1]) if (t := get_from_txt()) and t[0] is not None else (get_timestamp() - 60 * minute, get_timestamp())

    if start_time is None and end___time is not None:
        start_time = end___time
        end___time = end___time

    if start_time is not None and end___time is None:
        start_time = start_time
        end___time = start_time

    if query_sql is not None:
        query = query_sql
    if ' limit ' not in query.lower():
        query += ' LIMIT ' + str(limit)
    start_time = get_timestamp_ms(start_time) - forward_seconds * 1000
    end___time = get_timestamp_ms(end___time) + backward_seconds * 1000
    if not append_file:
        to_print_file(country, logstore_name, mode='w', file_path='', file_name=logstore_name + '_' + str(country) + str(file_name_suffix))
        to_print_file(f'start_time : {to_datetime_str(start_time, tz=default_tz)}')
        to_print_file(f'end___time : {to_datetime_str(end___time, tz=default_tz)}')
    if '\n' not in query:
        for s in [' where ', ' WHERE ', ' order by ']:
            if s in query:
                s1, s2, s3 = query.partition(s)
                query = s1 + '\n' + s2.strip() + ' ' + s3
    to_print_file(query)
    c = get_config_data(config_name)
    credentials = BasicCredentials(c['ak'], c['sk'], project_id)
    client = LtsClient.new_builder().with_credentials(credentials).with_region(LtsRegion.value_of(c['region'])).build()
    request = ListStructuredLogsWithTimeRangeRequest()
    request.log_stream_id = log_stream_id
    request.body = QueryLtsStructLogParamsNew(
        whether_to_rows=True,
        time_range=TimeRange(
            sql_time_zone="UTC",
            # start_time=start_time,
            # end_time=end___time,
            # 兼容问题, 因为 lts 日志库的时间是 utc 时间, 所以要减去 14 小时
            # 具体的原因可以参考 https://support.huaweicloud.com/intl/zh-cn/api-lts/ListStructuredLogsWithTimeRange.html
            start_time=start_time - 14 * 60 * 60 * 1000,
            end_time=end___time - 14 * 60 * 60 * 1000,
            start_time_gt=False,
            end_time_lt=False
        ),
        format="k-v",
        query=query,
    )
    response = client.list_structured_logs_with_time_range(request)
    # to_print_file(f"从日志库中查询, 一共获得 {len(response.body['result'])} 条日志")
    log_set = set()
    log_list = []
    for log in response.body['result']:
        if (msg := clean_up_msg(
                get_log_msg(log, replace_n_t=replace_n_t, default_tz=default_tz, time_use_in_content=time_use_in_content),
                method_length=method_length,
                trace_id_fixed_length=trace_id_fixed_length,
                clean_up_type=clean_up_msg_type)) is not None:
            msg = simplify_msg(msg, only_date_msg=only_date_msg, msg_delete_prefix=msg_delete_prefix)
            if remove_repeat_content:
                log_set.add(msg)
            else:
                log_list.append(msg)
    if len(log_set) > 0:
        log_list = list(log_set)
        log_list.sort()
    if order_by_desc:
        log_list.reverse()
    to_print_file(f"从日志库中查询, 一共获得 {len(response.body['result'])} 条日志, 处理完了以后, 共 {len(log_list)} 条日志")
    for log in log_list:
        to_print_file(log)
    to_print_file('END__END')
