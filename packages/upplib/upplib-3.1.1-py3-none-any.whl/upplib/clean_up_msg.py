from upplib import *
from datetime import datetime, timezone, timedelta
from typing import Any, Optional, Union


def simplify_msg(msg: str = None,
                 only_date_msg: bool = False,
                 msg_delete_prefix: int = 0,
                 ) -> str | None:
    """
        only_date_msg: 只输出日期+消息
        msg_delete_prefix: 删除消息的前缀的数量
    """
    res_msg = msg
    if only_date_msg:
        # 只需要日期+消息的部分，其他的不需要了
        msg_date = res_msg.partition(' ')[0]
        msg_1 = res_msg.split(' - ')[2]
        res_msg = msg_date.strip() + ' ' + msg_1.strip()
    if msg_delete_prefix > 0:
        msg_date, _, msg_1 = res_msg.partition(' ')
        res_msg = msg_date.strip() + ' ' + msg_1.strip()[msg_delete_prefix:]
    return res_msg


def clean_up_msg(msg: str = None,
                 clean_up_type: int = 1,
                 trace_id_fixed_length: int = None,
                 method_length: int = 31
                 ) -> str | None:
    if msg is None:
        return None
    formatters: list[Callable[[str], Optional[str]]] = [
        clean_up_msg_1,
        clean_up_msg_2,
        clean_up_msg_3,
        clean_up_msg_4,
        clean_up_msg_5,
    ]
    formatter_map: dict[int, Callable[[str], Optional[str]]] = {
        i + 1: formatter for i, formatter in enumerate(formatters)
    }
    if clean_up_type in formatter_map:
        return formatter_map[clean_up_type](msg, trace_id_fixed_length, method_length)
    return msg


def get_thread_id_for_log(thread_id_str: str = None) -> str:
    """
        格式化线程 ID 用于日志输出。
        规则：
          - None 或空字符串 -> '--'
          - 长度1 -> '-x'
          - 长度≥2 -> 最后两位
        返回格式: ' -XX- '
        """
    if not thread_id_str:  # 处理 None 和 空字符串
        suffix = '--'
    elif len(thread_id_str) == 1:
        suffix = '-' + thread_id_str
    else:  # 长度 >= 2
        suffix = thread_id_str[-2:]
    return f' -{suffix}- '


def clean_up_msg_1(msg: str = None, trace_id_fixed_length: int = None, method_length: int = 31) -> str:
    try:
        """
            2025-09-28T19:38:41.146111-06:00 com.leo.digest.aop.ApiLogAspect - traceId: - (catTraceId:rcs-gateway-0a0f2154-488625-102) - ===>API GatewayFacadeImpl#gatewayRequest START
            2025-09-28T19:38:41.146111-06:00 com.leo.digest.aop.ApiLogAspect - rcs-gateway-0a0f2154-488625-102 - ===>API GatewayFacadeImpl#gatewayRequest START

            2025-09-29T10:26:55.161111-06:00 c.c.f.a.spring.annotation.SpringValueProcessor - traceId: - Monitoring key: spring.mvc.servlet.path, beanName: swaggerWelcome, field: org.springdoc.webmvc.ui.SwaggerWelcomeWebMvc.mvcServletPath
            2025-09-29T10:26:55.161111-06:00 annotation.SpringValueProcessor - Monitoring key: spring.mvc.servlet.path, beanName: swaggerWelcome, field: org.springdoc.webmvc.ui.SwaggerWelcomeWebMvc.mvcServletPath
            
            2025-10-09T11:29:30.561111+08:00 [http-nio-8080-exec-5097] INFO  com.leo.rcs.biz.aspect.RcsReportAspect - traceId: - (catTraceId:datafeaturecore-0a5a030c-488883-287895) - RequestBody:{"bizData":{"user_id":1073850014231710218,"gaid":"364de12f-2fc9-4769-b2b6-e0b47bdf841d"},"extContext":{"mainDecisionId":"20251009112924085WITHDRAW02124","standardScene":"WITHDRAW"},"ignoreCache":false,"ignoreStatus":false,"interfaceId":"mobilewalla","methodId":"multiagents"}
            2025-10-09T11:29:30.561111+08:00 -97- .rcs.biz.aspect.RcsReportAspect - datafeaturecore-0a5a030c-488883-287895 - RequestBody:{"bizData":{"user_id":1073850014231710218,"gaid":"364de12f-2fc9-4769-b2b6-e0b47bdf841d"},"extContext":{"mainDecisionId":"20251009112924085WITHDRAW02124","standardScene":"WITHDRAW"},"ignoreCache":false,"ignoreStatus":false,"interfaceId":"mobilewalla","methodId":"multiagents"}
        
            2025-10-22T10:40:31.278820+08:00 [http-nio-8080-exec-399] INFO  com.leo.rcs.biz.aspect.RcsReportAspect - traceId:79d9b9b22cae6c9f8ce4f23a4d788f06 - (catTraceId:xdecisionengine-0a5a0512-489194-161829) - RequestURI:/v1/gateway
            2025-10-22T10:40:31.278820+08:00 -99- .rcs.biz.aspect.RcsReportAspect - 79d9b9b22cae6c9f8ce4f23a4d788f06 - RequestURI:/v1/gateway
        
            2025-10-13T14:01:26.365139+08:00 INFO 2025-10-13 14:01:26.365 main SnifferConfigInitializer : Config file found in /data/application/skywalking/config/agent.config.
            2025-10-13T14:01:26.365139+08:00 skywalking/config/agent.config. - INFO 2025-10-13 14:01:26.365 main SnifferConfigInitializer : Config file found in /data/application/skywalking/config/agent.config.
        """
        time1, _, msg0 = msg.strip().partition(' ')
        method, _, other = msg0.strip().partition(' - traceId:')
        other = msg0.strip() if not other else other
        thread_id = get_thread_id_for_log(method.strip().partition('] ')[0].rpartition('-')[2]) if '] ' in method else ' '
        method = method.strip()[-method_length:].rjust(method_length)
        if '(catTraceId:' in other:
            trace_id = re.search(r'\(catTraceId:([^)]+)\)', other).group(1).strip()
            other_after = other.strip().partition(trace_id)[2][3:].strip()
            trace_id_new = other.split(' - (catTraceId:')[0].strip()
            if trace_id_new:
                trace_id = trace_id_new
            other = other_after
        else:
            trace_id = ''
        other = other[2:].strip() if other.strip().startswith('- ') else other.strip()
        if trace_id_fixed_length is not None:
            if len(trace_id) > trace_id_fixed_length:
                trace_id = trace_id[:trace_id_fixed_length]
        trace_id = f' - {trace_id} - ' if trace_id else ' - '
        return f'{time1}{thread_id}{method}{trace_id}{other}'
    except:
        return msg


def clean_up_msg_2(msg: str = None, trace_id_fixed_length: int = None, method_length: int = 31) -> str:
    try:
        """
            2025-10-09T13:45:49.687123+08:00 INFO 8 --- [nio-8080-exec-4] c.l.r.b.s.device.impl.DeviceServiceImpl  : (catTraceId:customer-product-0a5a0329-488885-107496) - checkDeviceId lock key: 1073852969169211259
            2025-10-09T13:45:49.687123+08:00 --4- s.device.impl.DeviceServiceImpl - customer-product-0a5a0329-488885-107496 - checkDeviceId lock key: 1073852969169211259
            
            2025-10-10T20:16:30.071887+08:00 INFO 8 --- [ay-task-query-5] c.l.r.b.s.d.s.i.DelayTaskCoreServiceImpl : DelayTaskCoreServiceImpl queryTaskResult response: {"sign":null,"hitResultList":[],"branchRejectInfo":[]}
            2025-10-10T20:16:30.071887+08:00 --5- .d.s.i.DelayTaskCoreServiceImpl - DelayTaskCoreServiceImpl queryTaskResult response: {"sign":null,"hitResultList":[],"branchRejectInfo":[]}
        """
        time1, _, msg0 = msg.strip().partition(' ')
        thread_id = get_thread_id_for_log(msg0.strip().rpartition('] ')[0].rpartition('-')[2])
        method, _, other = msg0.strip().rpartition(' : ')
        method = method.strip()[-method_length:].rjust(method_length)
        trace_id = ''
        if '(catTraceId:' in other:
            trace_id = re.search(r'\(catTraceId:([^)]+)\)', other).group(1)
            other = other.strip().partition(trace_id)[2][3:].strip()
        other = other[1:].strip() if other.startswith(':') else other
        trace_id = f' - {trace_id} - ' if trace_id else ' - '
        return f'{time1}{thread_id}{method}{trace_id}{other}'
    except:
        return msg


def clean_up_msg_3(msg: str = None, trace_id_fixed_length: int = None, method_length: int = 31) -> str:
    try:
        """
            2025-10-09T14:25:28.096+07:00 INFO com.itn.idn.review.aop.LogAspect - traceId:db57046b7cba9d5c55fa5ff93727c4df - ReviewBackController.queryCreditCasesByUserIdsV2: request log info-------------> {"userIds":[1011450014961537063]}
            2025-10-09T14:25:28.096+07:00 om.itn.idn.review.aop.LogAspect - db57046b7cba9d5c55fa5ff93727c4df - ReviewBackController.queryCreditCasesByUserIdsV2: request log info-------------> {"userIds":[1011450014961537063]}
        """
        SEP_S = ' - traceId:'
        time1, _, msg0 = msg.strip().partition(' ')
        msg1 = msg0.strip().split(SEP_S)
        method = ' ' + msg1[0].strip()[-method_length:].rjust(method_length)
        trace_id, _, other = msg1[1].strip().partition(' - ')
        trace_id = f' - {trace_id} - ' if trace_id else ' - '
        return f'{time1}{method}{trace_id}{other}'
    except:
        return msg


def clean_up_msg_4(msg: str = None, trace_id_fixed_length: int = None, method_length: int = 15) -> str:
    try:
        """
            2025-10-11T10:49:24.071000+07:00 INFO [TID: N/A] [8] [strategyAsyncExecutor-1] [FlowExecutor] [-] [33f7a5cfed3548f9aa3cc39079d1e407]:(catTraceId:rcs-provider-server-0a1e0d61-488931-966531) - requestId has generated
            2025-10-11T10:49:24.071000+07:00 --1-    FlowExecutor - rcs-provider-server-0a1e0d61-488931-966531 - requestId has generated
            
            2025-10-09T15:00:33.751000+07:00 INFO [TID: N/A] [8] [http-nio-10009-exec-1] [GatewayController] [WITHDRAW-1080478239721884577] Call response: length=632929
            2025-10-09T15:00:33.751000+07:00 --1- tewayController - WITHDRAW-1080478239721884577 - Call response: length=632929
            
            2025-10-10T09:14:47.178000+07:00 INFO [TID: N/A] [8] [strategyAsyncExecutor-26] [DefaultLogHandler] [-] [Forest] Request (okhttp3): [Type Change]: GET -> POSTPOST http://xdecisionengine-svc.java/engine/apply HTTPHeaders: \trequester: rcsbatch\tapp: 360Kredi\tbiz_flow_number: 28085377ee25467ea3941b1e3f681c55\tinner_app: 360Kredi\ttpCode: rcsBatch\treport_id: 7721fe0bbfc0415c94e2b91dfa622aca\trequestId: 28085377ee25467ea3941b1e3f681c55\tbiz_type: MARKET_MODEL_CALCULATE\tseq_id: 11f0724b4a0b48a8a5e9cdbe54bc22d7\tsource_type: other\ttimestamp: 1760046298655\tscene: MARKET_MODEL_CALCULATE\tContent-Type: application/jsonBody: {"engineCode":"jcl_20250917000001","organId":20,"fields":{"app":"360Kredi","requester":"rcsbatch","biz_flow_number":"28085377ee25467ea3941b1e3f681c55","inner_app":"360Kredi","user_id":1021847804368362617,"report_id":"7721fe0bbfc0415c94e2b91dfa622aca","cust_no":"1021847804368362617","biz_type":"MARKET_MODEL_CALCULATE","seq_id":"11f0724b4a0b48a8a5e9cdbe54bc22d7","source_type":"other","user_no":"1021847804368362617","timestamp":1760046298655}}
            2025-10-10T09:14:47.178000+07:00 -26- faultLogHandler - [-] [Forest] Request (okhttp3): [Type Change]: GET -> POSTPOST http://xdecisionengine-svc.java/engine/apply HTTPHeaders: 	requester: rcsbatch	app: 360Kredi	biz_flow_number: 28085377ee25467ea3941b1e3f681c55	inner_app: 360Kredi	tpCode: rcsBatch	report_id: 7721fe0bbfc0415c94e2b91dfa622aca	requestId: 28085377ee25467ea3941b1e3f681c55	biz_type: MARKET_MODEL_CALCULATE	seq_id: 11f0724b4a0b48a8a5e9cdbe54bc22d7	source_type: other	timestamp: 1760046298655	scene: MARKET_MODEL_CALCULATE	Content-Type: application/jsonBody: {"engineCode":"jcl_20250917000001","organId":20,"fields":{"app":"360Kredi","requester":"rcsbatch","biz_flow_number":"28085377ee25467ea3941b1e3f681c55","inner_app":"360Kredi","user_id":1021847804368362617,"report_id":"7721fe0bbfc0415c94e2b91dfa622aca","cust_no":"1021847804368362617","biz_type":"MARKET_MODEL_CALCULATE","seq_id":"11f0724b4a0b48a8a5e9cdbe54bc22d7","source_type":"other","user_no":"1021847804368362617","timestamp":1760046298655}}
        """
        SEP_S = '] '
        time1, _, msg0 = msg.strip().partition(' ')
        msg1 = msg0.split(SEP_S)
        thread_id = get_thread_id_for_log(msg1[2].strip().rpartition('-')[2])
        method = msg1[3].strip().strip()[-method_length:].strip().replace('[', '').rjust(method_length)
        if ']:(catTraceId:' in msg1[5]:
            trace_id = re.search(r'\(catTraceId:([^)]+)\)', msg0).group(1)
            other = msg0.partition(trace_id)[2][3:].strip()
        else:
            trace_id = msg1[4].strip().partition('[')[2].strip()
            trace_id = trace_id[1:].strip() if trace_id.startswith('-') else trace_id
            other = msg0.strip().partition(method)[2][1:].strip() if not trace_id else msg0.strip().partition(trace_id)[2][1:].strip()
        trace_id = f' - {trace_id} - ' if trace_id else ' - '
        return f'{time1}{thread_id}{method}{trace_id}{other}'
    except:
        return msg


def clean_up_msg_5(msg: str = None, trace_id_fixed_length: int = None, method_length: int = 31) -> str:
    try:
        """
            2025-10-10T09:59:36.118111+07:00 [http-nio-8080-exec-13][AUDIT.1070150904958674814][20251010095936118AUDIT04869][jcl_20250109000001][][MAIN] INFO - (catTraceId:xdecisionengine-0a1e0845-488906-400194) - putAll to context ,value={"app":"kredi","ip":"192.168.1.8","session_id":"","source_type":"ANDROID","product_name":"kredi"} - cn.xinfei.xdecision.engine.domain.context.PipelineContextHolder.()
            2025-10-10T09:59:36.118111+07:00 -13- n.context.PipelineContextHolder - xdecisionengine-0a1e0845-488906-400194 - putAll to context ,value={"app":"kredi","ip":"192.168.1.8","session_id":"","source_type":"ANDROID","product_name":"kredi"}
        
            2025-10-10T13:45:56.000000+08:00 [xdecision-reentry-server_2-thread_757][1080554879087872098][20251010135455914APPLY03025][jcl_20240927000001_59][][] INFO -  Release distributed lock，clientId=10.90.0.132,lockKey=LOCK_PENDING_REENTRY_20251010135455914APPLY03025 - cn.xinfei.xdecision.redis.RedisLock.()
            2025-10-10T13:45:56.000000+08:00 -57- infei.xdecision.redis.RedisLock - -INFO - Release distributed lock，clientId=10.90.0.132,lockKey=LOCK_PENDING_REENTRY_20251010135455914APPLY03025
            
            2025-10-10T13:55:57.000000+08:00 [xdecision-decision-table_8-thread_460][1090894420147560136][20251010140508949REPAY_ADJUST03055_1_1][jcl_20250807000007_65][jcb_20250817000001][CHILD] ERROR- custNo is empty - cn.xinfei.xdecision.engine.domain.context.PipelineContextHolder.()
            2025-10-10T13:55:57.000000+08:00 -60- n.context.PipelineContextHolder - ERROR - custNo is empty
            
            2025-10-13T10:27:09.986000+07:00 [xdecision-nodelog-server_3-thread_119][WITHDRAW.1070152631535528873][20251013102645283WITHDRAW05920_1_1][jcl_20250916000001_64][][CHILD] INFO - (catTraceId:xdecisionengine-0a1e0804-488979-145805) - [NodeLogLocalThreadConsumer] engineNodeLog:{"dataSourceTypeCode":null,"requestId":"WITHDRAW.1070152631535528873","decisionId":"20251013102645283WITHDRAW05920_1_1","mainDecisionId":"20251013102645283WITHDRAW05920","engineCode":"jcl_20250916000001","nodeCode":"jcl_20250916000001_64","nodeType":"externalDataConsulting","nodeName":"iluma","versionNo":0,"input":{},"output":{"xd_node_xdata_duration":0,"xd_node_terminal":false,"xd_node_duration":25},"context":{"extend_his_changemobile_cnt":-999,"itn_newcust_mix2_v7_37_lr_score":-1.0,"app_version_num":301000,"cbi_inquiry_score_v1":10,"interGroup":"jcl_20250916000001_4","adv_max_30d_cnt":6.0,"vip_code":"-999","_mix3_v8_desc_grp_partner":"null","idn_idd_battery":5000.0,"cbi_debtor_active_credit_card_i_limit_mean":3000000.0,"idn_idd_memory_size":4.0,"_mix3_v9_desc_grp":"null","msg_id":"2ffed582-2ce9-42b9-9932-4565714dcd56","a_card_element_v1":"\"{\\\"a_extend_address_elong\\\":3.0,\\\"a_extend_address_long\\\":16.0,\\\"a_extend_address_nlong\\\":0.0,\\\"a_extend_age\\\":41.0,\\\"a_extend_child_count\\\":3.0,\\\"a_extend_company_address_long\\\":30.0,\\\"a_extend_company_address_nlong\\\":0.0,\\\"a_extend_company_name_long\\\":5.0,\\\"a_extend_company_phone_code\\\":-999,\\\"a_extend_company_phone_list\\\":-999,\\\"a_extend_company_province_city_area\\\":2.0,\\\"a_extend_contact_phone_list\\\":0.0,\\\"a_extend_contact_phone_list_3m\\\":0.0,\\\"a_extend_contact_phone_long\\\":-999,\\\"a_extend_contact_phone_set\\\":0.0,\\\"a_extend_contact_phone_set_3m\\\":0.0,\\\"a_extend_driver_license\\\":0.0,\\\"a_extend_education\\\":4.0,\\\"a_extend_first_name_long\\\":8.0,\\\"a_extend_first_name_num\\\":2.0,\\\"a_extend_first_name_set_ratio\\\":0.75,\\\"a_extend_income_source_elong\\\":0.0,\\\"a_extend_income_source_long\\\":0.0,\\\"a_extend_job_payday\\\":7.0,\\\"a_extend_job_type\\\":1.0,
            2025-10-13T10:27:09.986000+07:00 -19-      NodeLogLocalThreadConsumer - xdecisionengine-0a1e0804-488979-145805 - engineNodeLog:{"dataSourceTypeCode":null,"requestId":"WITHDRAW.1070152631535528873","decisionId":"20251013102645283WITHDRAW05920_1_1","mainDecisionId":"20251013102645283WITHDRAW05920","engineCode":"jcl_20250916000001","nodeCode":"jcl_20250916000001_64","nodeType":"externalDataConsulting","nodeName":"iluma","versionNo":0,"input":{},"output":{"xd_node_xdata_duration":0,"xd_node_terminal":false,"xd_node_duration":25},"context":{"extend_his_changemobile_cnt":-999,"itn_newcust_mix2_v7_37_lr_score":-1.0,"app_version_num":301000,"cbi_inquiry_score_v1":10,"interGroup":"jcl_20250916000001_4","adv_max_30d_cnt":6.0,"vip_code":"-999","_mix3_v8_desc_grp_partner":"null","idn_idd_battery":5000.0,"cbi_debtor_active_credit_card_i_limit_mean":3000000.0,"idn_idd_memory_size":4.0,"_mix3_v9_desc_grp":"null","msg_id":"2ffed582-2ce9-42b9-9932-4565714dcd56","a_card_element_v1":""{\"a_extend_address_elong\":3.0,\"a_extend_address_long\":16.0,\"a_extend_address_nlong\":0.0,\"a_extend_age\":41.0,\"a_extend_child_count\":3.0,\"a_extend_company_address_long\":30.0,\"a_extend_company_address_nlong\":0.0,\"a_extend_company_name_long\":5.0,\"a_extend_company_phone_code\":-999,\"a_extend_company_phone_list\":-999,\"a_extend_company_province_city_area\":2.0,\"a_extend_contact_phone_list\":0.0,\"a_extend_contact_phone_list_3m\":0.0,\"a_extend_contact_phone_long\":-999,\"a_extend_contact_phone_set\":0.0,\"a_extend_contact_phone_set_3m\":0.0,\"a_extend_driver_license\":0.0,\"a_extend_education\":4.0,\"a_extend_first_name_long\":8.0,\"a_extend_first_name_num\":2.0,\"a_extend_first_name_set_ratio\":0.75,\"a_extend_income_source_elong\":0.0,\"a_extend_income_source_long\":0.0,\"a_extend_job_payday\":7.0,\"a_extend_job_type\":1.0,
        """
        time1, _, msg0 = msg.strip().partition(' ')
        thread_id = get_thread_id_for_log(msg0.strip().partition('][')[0].strip().rpartition('-')[2])
        if msg0.endswith('.()'):
            msg0, _, method = msg0.rpartition(' - ')
        else:
            method = msg0.rpartition(') - [')[2].strip().rpartition('] ')[0].strip()
        method = method.strip().replace('.()', '')[-method_length:].rjust(method_length)
        trace_id = ''
        other = ''
        if '(catTraceId:' in msg0:
            trace_id = re.search(r'\(catTraceId:([^)]+)\)', msg0).group(1)
            other = msg0.partition(trace_id)[2][3:].strip()
        else:
            for sep in ['] INFO - ', '] ERROR- ', '] WARN - ']:
                if sep in msg0:
                    other = msg0.partition(sep)[2].strip()
                    trace_id = re.sub(r'[^a-zA-Z0-9]', '', sep).rjust(5, '-')
                    break
        if f'[{method.strip()}]' in other:
            other = other.partition(f'[{method.strip()}]')[2].strip()
        trace_id = f' - {trace_id} - ' if trace_id else ' - '
        return f'{time1}{thread_id}{method}{trace_id}{other}' if other else msg
    except:
        return msg
