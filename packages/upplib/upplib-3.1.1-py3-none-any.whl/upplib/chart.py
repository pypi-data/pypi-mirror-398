from upplib import *
from upplib.common_package import *


def to_html(html_param: list | str,
            name: str = None) -> str:
    name = 'html' if name is None else name
    return to_txt(data_param=html_param,
                  file_name=str(name),
                  file_name_is_date=True,
                  file_path='html',
                  fixed_name=False,
                  suffix='.html')


def to_text_html(text_list: list,
                 title: str = None,
                 return_file: bool = True) -> str | None:
    """
    text_list = [{
        name: '王小虎',
        text: '上海市普陀区金沙江路 1518 弄'
    }, {
        name: '王小虎',
        text: '上海市普陀区金沙江路 1517 弄'
    }, {
        name: '王小虎',
        text: '上海市普陀区金沙江路 1516 弄'
    }]
    """
    title = 'text' if title is None else title
    h_d = to_text_list_html(text_list, title)
    return to_html(h_d, title) if return_file else h_d


def to_table_html(table: list,
                  title: str = None,
                  name: str = None,
                  return_file: bool = True) -> str | None:
    """
    table的 html 模板代码
    table_list = [{
        date: '2016-05-02',
        name: '王小虎',
        address: '上海市普陀区金沙江路 1518 弄'
    }, {
        date: '2016-05-04',
        name: '王小虎',
        address: '上海市普陀区金沙江路 1517 弄'
    }, {
        date: '2016-05-03',
        name: '王小虎',
        address: '上海市普陀区金沙江路 1516 弄'
    }]
    title = {
        date: '日期',
        name: '名称',
        address: '地址'
    }
    以下另外另外一种 api
    table_list : table = [
          ['x轴的数据', 'line1', 'line2', 'line3'],
          ['2020-01-01', 120, 132, 101],
          ['2020-01-02', 100, 102, 131],
          ['2020-01-03', 123, 165, 157],
          ['2020-01-04', 126, 109, 189],
          ['2020-01-05', 150, 156, 128],
          ['2020-01-06', 178, 134, 140],
          ['2020-01-07', 157, 148, 161],
     ]
    """
    header = []
    table_list = []
    # 是一种两个 list 的形式的 api
    is_list = False
    if isinstance(table[0], list) or isinstance(table[0], tuple) or isinstance(table[0], set):
        is_list = True
    if is_list:
        first_line = table[0]
        for o_obj in first_line:
            header.append(str(o_obj) + ": '" + str(o_obj) + "'")
        for o_line in table[1:]:
            l = []
            for i in range(len(o_line)):
                l.append(str(first_line[i]) + ': "' + str(o_line[i]) + '"')
            table_list.append('{' + ', '.join(l) + '}')
    else:
        if title is None:
            title = {}
            for k in table[0]:
                title[k] = k
        for obj_one in table:
            l = []
            for k in obj_one:
                l.append(str(k) + ': "' + str(obj_one[k]) + '"')
            table_list.append('{' + ', '.join(l) + '}')
        for k in title:
            header.append(str(k) + ": '" + str(title[k]) + "'")
    name = 'table' if name is None else name
    h_d = to_table_list_html(table_list, header, name)
    return to_html(h_d, name) if return_file else h_d


def insert_data_to_chart(html_data: str,
                         name: str = None,
                         x_list: Any = None,
                         y_list: Any = None,
                         legend: Any = None,
                         series: Any = None,
                         smooth: int = 0,
                         height_limit: int = 0,
                         height_value: int = 0,
                         show_text: int = 1,
                         legend_show: bool = False,
                         tooltip_simple: bool = True,
                         x_min: int | float | None = None,
                         x_max: int | float | None = None,
                         y_min: int | float | None = None,
                         y_max: int | float | None = None,
                         return_file: bool = True) -> str:
    """
        将 html 中的占位符 替换成数据
        并且 导出 生成后的 html 文件
        height_limit : 图形的高度是否限制, 0:不限制, 1:限制
        show_text    : 图形上是否显示文本, 0:不显示, 1:显示
    """
    # 构建参数字典
    param_obj = {
        'chart_name': name,
        'name': name,
        'x_list': x_list,
        'y_list': y_list,
        'legend': legend,
        'series': series,
        'smooth': smooth,
        'height_limit': height_limit,
        'legend_show': str(legend_show).lower(),
        'tooltip_simple': str(tooltip_simple).lower(),
        'height_value': height_value,
        'show_text': show_text,
        'x_min': x_min,
        'x_max': x_max,
        'y_min': y_min,
        'y_max': y_max,
    }
    param_obj_use = {key: value for key, value in param_obj.items() if value is not None}
    replace_dict = {}
    for key, value in param_obj_use.items():
        one_p = f'-{key}-'
        if isinstance(value, (list, tuple, set, dict)):
            value = json.dumps(value, indent=4)
        else:
            value = str(value)
        replace_dict[one_p] = value
    for key, value in replace_dict.items():
        if key in html_data:
            html_data = html_data.replace(key, value.replace('\n', '\n' + get_space(html_data=html_data, key=key)))
    return to_html(html_data, name) if return_file else html_data


def to_chart(x_list: list,
             y_list: list | None = None,
             name: str = None,
             name_raw: bool = False,
             return_file: bool = True) -> str:
    """
    将数据整理成折线图
    情况1:
    x轴数据 : x_list = [
          ['x轴的数据', 'line1', 'line2', 'line3'],
          ['2020-01-01', 120, 132, 101],
          ['2020-01-02', 100, 102, 131],
          ['2020-01-03', 123, 165, 157],
          ['2020-01-04', 126, 109, 189],
          ['2020-01-05', 150, 156, 128],
          ['2020-01-06', 178, 134, 140],
          ['2020-01-07', 157, 148, 161],
     ]
     --- 以上这种情况,当 y_list 为空的时候,就说明有可能是这种情况
     --- 以上这种情况,数据与 excel 中的数据对齐
    情况2:
    x轴数据 : x_list = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    y轴数据 : y_list = [
          [120, 132, 101, 134, 90, 230, 210],
    	  [220, 182, 191, 234, 290, 330, 310],
    	  [150, 232, 201, 154, 190, 330, 410],
    	  [320, 332, 301, 334, 390, 330, 320],
    	  [820, 932, 901, 934, 1290, 1330, 1320]
    ]
    情况3--标准情况下的数据:
    x轴数据 : x_list = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    y轴数据 : y_list = [
                {
                    name: 'Email',
                    hide: True,
                    smooth: True,
                    data: [120, 132, 101, 134, 90, 230, 210],
                },
                {
                    name: 'Union Ads',
                    hide: 1,
                    smooth: 1,
                    data: [220, 182, 191, 234, 290, 330, 310],
                },
                {
                    name: 'Video Ads',
                    data: [150, 232, 201, 154, 190, 330, 410],
                },
                {
                    name: 'Direct',
                    data: [320, 332, 301, 334, 390, 330, 320],
                },
                {
                    name: 'Search Engine',
                    data: [820, 932, 901, 934, 1290, 1330, 1320],
                },
            ]
     name : 文件名称,折线图的名称
     name_raw : 用原始的名字,不用带上属性 line_stack
    """
    # 当 y_list 没有的话, 需要整理出 y_list 的数据
    if y_list is None:
        data_list = x_list
        x_list = []
        y_list = []
        for i in range(len(data_list)):
            line_one = data_list[i]
            # 第一行数据
            if i == 0:
                for y in range(1, len(line_one)):
                    y_list.append({'name': line_one[y], 'data': []})
            # 第二行开始的数据
            if i > 0:
                x_list.append(line_one[0])
                for y in range(1, len(line_one)):
                    y_list[y - 1]['data'].append(line_one[y])
    name_list = []
    name_hide = {}
    for y_index in range(len(y_list)):
        y_one = y_list[y_index]
        name_one = y_one['name'] if 'name' in y_one else str(y_index + 1) + '_' + random_letter(3)
        name_list.append(str(name_one))
        if 'hide' in y_one and y_one['hide']:
            name_hide[name_one] = 0
    legend = {
        'top': 0,
        'data': name_list,
        'selected': name_hide,
    }
    # {
    #     name: 'Email',
    #     type: 'line',
    #     smooth: 1,
    #     data: [120, 132, 101, 134, 90, 230, 210],
    # }
    # [120, 132, 101, 134, 90, 230, 210],
    series = []
    for y_index in range(len(y_list)):
        y_o = {}
        y_one = y_list[y_index]
        y_o['name'] = name_list[y_index]
        y_o['data'] = y_one['data'] if 'data' in y_one else y_one
        y_o['type'] = 'line'
        y_o['itemStyle'] = {'normal': {'color': get_default_color_list()[y_index % len(get_default_color_list())]}}
        if 'smooth' in y_one and y_one['smooth']:
            y_o['smooth'] = 1
        # 只有一条线,就不显示 name 了
        if len(y_list) == 1:
            del y_o['name']
        series.append(y_o)

    if not name_raw:
        name = 'line_stack' if name is None else name
    series_str = '[\n    ' + ',\n    '.join(list(map(str, series))) + '\n]'
    return insert_data_to_chart(html_data=to_line_stack_html(),
                                name=name,
                                x_list=str(x_list),
                                legend=legend,
                                series=series_str,
                                return_file=return_file)


def to_chart_table(x_list: list | None = None,
                   y_list: list = None,
                   name: str = None,
                   name_raw: bool = False) -> str:
    """
    即使用 table 也使用 chart
    情况1:
    x轴数据 : x_list = [
          ['x轴的数据', 'line1', 'line2', 'line3'],
          ['2020-01-01', 120, 132, 101],
          ['2020-01-02', 100, 102, 131],
          ['2020-01-03', 123, 165, 157],
          ['2020-01-04', 126, 109, 189],
          ['2020-01-05', 150, 156, 128],
          ['2020-01-06', 178, 134, 140],
          ['2020-01-07', 157, 148, 161],
     ]
     --- 以上这种情况,当 y_list 为空的时候,就说明有可能是这种情况
     --- 以上这种情况,数据与 excel 中的数据对齐
    情况2:
    x轴数据 : x_list = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    y轴数据 : y_list = [
        [120, 132, 101, 134, 90, 230, 210],
    	  [220, 182, 191, 234, 290, 330, 310],
    	  [150, 232, 201, 154, 190, 330, 410],
    	  [320, 332, 301, 334, 390, 330, 320],
    	  [820, 932, 901, 934, 1290, 1330, 1320]
    ]
    """
    if x_list is None:
        x_list = []
    html_chart = to_chart(x_list, y_list, name, name_raw, False)
    if y_list is not None:
        x_list.extend(y_list)
    html_table = to_table_html(x_list, None, name, False)
    return to_html([html_chart, html_table], name)


def to_chart_table_text(x_list: list | None = None,
                        y_list: list | None = None,
                        text_list: list | None = None,
                        name: str = None,
                        name_raw: bool = False) -> str:
    """
    生成 chart , table , text 的操作
    """
    if x_list is None:
        x_list = []
    html_chart = to_chart(x_list, y_list, name, name_raw, False)
    r_list = [html_chart]
    if y_list is not None:
        x_list.extend(y_list)
    html_table = to_table_html(x_list, None, name, False)
    r_list.append(html_table)
    if text_list is not None:
        # 生成 text 的操作
        text_html = to_text_html(text_list, name, False)
        r_list.append(text_html)
    return to_html(r_list, name)


def to_chart_one(data_list: list,
                 name: str = None,
                 x_index: int = 0,
                 x_key: str = 'name',
                 y_index: int = 1,
                 y_key: str = 'value',
                 is_area: bool = False,
                 smooth: bool = False) -> str:
    """
    将数据整理成折线图
    一条折线
    数据 : data_list = [
                ['2020-01-01', 132],
                ['2021-01-01', 181],
                ['2022-01-01', 147]
            ]
    x_index : x 轴数据的下标
    y_index : y 轴数据的下标
    或者
    数据 : data = [
           {name: "Search Engine", value: 1048 },
           {name: "Direct", value: 735 },
           {name: "Email", value:580 },
           {name: "Union Ads", value:484 },
           {name: "Video Ads", value:300 }
          }]
     x_key : 当元素为对象的时候, x 的 key
     y_key : 当元素为对象的时候, y 的 key
    is_area : 是否使用 area 图
    smooth : 曲线是否平滑
    """
    x_list = []
    y_list = []
    name = 'line' if name is None else name + '_line'
    name = name + '_smooth' if smooth else name
    name = name + '_area' if is_area else name
    sm = 1 if smooth else 0
    for d_one in data_list:
        if isinstance(d_one, list):
            x = d_one[x_index]
            y = d_one[y_index]
        else:
            x = d_one[x_key]
            y = d_one[y_key]
        x_list.append(x)
        y_list.append(y)
    if is_area:
        return insert_data_to_chart(html_data=to_line_area_html(),
                                    name=name,
                                    x_list=x_list,
                                    y_list=y_list,
                                    smooth=sm)
    else:
        return to_chart(x_list=x_list,
                        y_list=[{'name': name, 'data': y_list, 'smooth': sm}],
                        name=name,
                        name_raw=True)


def to_chart_pie(data_list: list,
                 name: str = None,
                 name_index: int = 0,
                 name_key: str = 'name',
                 value_index: int = 1,
                 value_key: str = 'value') -> str:
    """
    将数据整理成饼状图
    数据 : data = [
            { value: 1048, name: "Search Engine" },
            { value: 735, name: "Direct" },
            { value: 580, name: "Email" },
            { value: 484, name: "Union Ads" },
            { value: 300, name: "Video Ads" }
          ]
     name_key : 当元素为对象的时候, x 的 key
     value_key : 当元素为对象的时候, y 的 key
    或者
    数据 : data = [
            [ "Search Engine", 1048 ],
            [ "Direct", 735 ],
            [ "Email",580 ],
            [ "Union Ads",484 ],
            [ "Video Ads",300 ]
          ]
     name_index : 当元素为数组的时候, name 的下标
     value_index : 当元素为数组的时候, value 的下标
    """
    x_list = []
    name = 'pie' if name is None else name + '_pie'
    for one_data in data_list:
        if isinstance(one_data, list):
            x = one_data[name_index]
            y = one_data[value_index]
        else:
            x = one_data[name_key]
            y = one_data[value_key]
        x_list.append({'name': x, 'value': y})
    x_list_str = '[\n    ' + ',\n    '.join(list(map(str, x_list))) + '\n]'
    return insert_data_to_chart(html_data=to_pie_html(),
                                name=name,
                                x_list=x_list_str)


def to_chart_bar(data_list: list,
                 name: str = None,
                 name_index: int = 0,
                 name_key: str = 'name',
                 value_index: int = 1,
                 value_key: str = 'value') -> str:
    """
    将数据整理成柱状图
    数据 : data = [
            { value: 1048, name: "Search Engine" },
            { value: 735, name: "Direct" },
            { value: 580, name: "Email" },
            { value: 484, name: "Union Ads" },
            { value: 300, name: "Video Ads" }
          ]
     name_key : 当元素为对象的时候, x 的 key
     value_key : 当元素为对象的时候, y 的 key
    或者
    数据 : data = [
            [ "Search Engine", 1048 ],
            [ "Direct", 735 ],
            [ "Email",580 ],
            [ "Union Ads",484 ],
            [ "Video Ads",300 ]
          ]
     name_index : 当元素为数组的时候, name 的下标
     value_index : 当元素为数组的时候, value 的下标
    """
    x_list = []
    y_list = []
    name = 'bar' if name is None else name + '_bar'
    for one_data in data_list:
        if isinstance(one_data, list):
            x = one_data[name_index]
            y = one_data[value_index]
        else:
            x = one_data[name_key]
            y = one_data[value_key]
        x_list.append(x)
        y_list.append(y)
    return insert_data_to_chart(html_data=to_bar_html(),
                                name=name,
                                x_list=x_list,
                                y_list=y_list)


def to_chart_gantt(x_list: list = None,
                   y_list: list | None = None,
                   name: str = None,
                   use_color: bool = True
                   ) -> str:
    """
    # 将数据整理成性能分析图
        x_list = [
            ['categoryA', 0, 1],
            ['categoryA', 2, 2],
            ['categoryB', 2, 1],
            ['categoryB', 6, 9],
            ['categoryC', 4, 3],
            ['categoryC', 9, 3],
        ]

    categoryA : name
    0         : x 轴的开始位置
    1         : x 轴的持续(时间,数量)

    第二种 api :
    x_list = [
    		{
    			"value": [0, 0, 5782, 5782]
    		},
    		{
    			"value": [0, 7015, 7566, 551]
    		},
    		{
    			"value": [1, 0, 847, 847]
    		},
    		{
    			"value": [1, 1690, 3983, 2293]
    		},
    		{
    			"value": [2, 0, 1710, 1710]
    		},
    		{
    			"value": [2, 3660, 9838, 6178]
    		},
    		{   
    		    'value': [0, 3264, 4771, 1507], 
    		    'itemStyle': {
    		        'normal': {
    		            'color': '#ffebcd'
    		        }
    		    }
    		}
    	]
    "value": [0, 1, 5783, 5782]
    0    : y_list 的 index
    1    : x 轴的开始位置
    5783 : x 轴的结束位置
    5782 : x 轴的持续(时间,数量)

    y_list = ['categoryA', 'categoryB', 'categoryC']
    """
    if y_list is None:
        y_list = []
    if x_list is None:
        x_list = []
    x_p_list: list[dict[str, list, dict[str, Any]]] = x_list
    # x_p_list = x_list
    y_p_list = y_list
    if y_p_list is None or len(y_p_list) == 0:
        x_p_list: list[dict[str, list[int]]] = []
        y_p_list = list(set(map(lambda x: x[0], x_list)))
        y_p_list.sort()
        for x_d in x_list:
            x_p_list.append({
                'value': [
                    y_p_list.index(x_d[0]),  # int
                    x_d[1],  # int
                    x_d[1] + x_d[2],  # int
                    x_d[2],  # int
                ],
            })
    color_list = get_default_color_list()
    if use_color:
        color_index_map = {}
        for x_d in x_p_list:
            y_p_index = x_d['value'][0]
            color_index_map.setdefault(y_p_index, 0)
            color = color_list[color_index_map[y_p_index] % len(color_list)]
            x_d.setdefault('itemStyle', {'normal': {'color': color}})
            color_index_map[y_p_index] += 1
    index_map = {}
    for x_d in x_p_list:
        value_list = x_d['value']
        x_index = y_p_list[value_list[0]]
        if x_index not in index_map:
            index_map[x_index] = 1
        if len(value_list) <= 4:
            x_d['value'].append(str(x_index) + '#' + str(index_map[x_index]))
            index_map[x_index] += 1
    x_min = min((x_d['value'][1] for x_d in x_p_list), default=None)
    x_max = max((x_d['value'][2] for x_d in x_p_list), default=None)
    name = 'gantt' if name is None else name + '_gantt'
    x_list_str = '[\n    ' + ',\n    '.join(list(map(str, x_p_list))) + '\n]'
    return insert_data_to_chart(html_data=to_gantt_html(),
                                name=name,
                                x_min=x_min,
                                x_max=x_max,
                                x_list=x_list_str,
                                y_list=str(y_p_list))


def get_default_color_list():
    return ['#7fffd4', '#dc143c', '#ffd700', '#6b8e23', '#4682b4', '#ff7f50', '#90ee90', '#ff1493', '#ffa500',
            '#add8e6', '#d02090', '#d2691e', '#9acd32', '#d3d3d3', '#bc8f8f', '#dda0dd']


def to_chart_line_x(x_list: list[list[list[str | int]]] = None,
                    date_is_time: bool = False,
                    height_limit: int = 1,
                    height_value: int = 0,
                    show_text: int = 0,
                    name: str = None,
                    ) -> str:
    """
        将数据整理成沿着x轴走向的断断续续的图,用于观察中间的间隔
        x_list = [
            [
                ['a', 0, 1],
                ['b', 2, 4],
                ['c', 3, 6]
            ],
            [
                ['1', 0, 1],
                ['2', 2, 2],
                ['3', 2, 6]
            ]
        ]
    a : 名称
    2 : x 轴的开始位置
    4 : x 轴的结束位置

    date_is_time : 数据是否是时间
        x_list = [
            [
                ['a', '2025-10-17T16:07:10.838000+07:00', 2025-10-17T16:07:11.838000+07:00],
                ['b', '2025-10-17T16:07:12.838000+07:00', 2025-10-17T16:07:13.838000+07:00],
                ['c', '2025-10-17T16:07:15.838000+07:00', 2025-10-17T16:07:17.838000+07:00],
            ],
            [
                ['1', '2025-10-17T16:07:16.838000+07:00', 2025-10-17T16:07:17.038000+07:00],
                ['2', '2025-10-17T16:07:17.838000+07:00', 2025-10-17T16:07:18.838000+07:00],
                ['3', '2025-10-17T16:07:19.838000+07:00', 2025-10-17T16:07:19.938000+07:00],
            ]
        ]
    """
    if x_list is None:
        x_list = []
    x_p_list: list[dict] = []
    color_list = get_default_color_list()
    y_list = []
    for x_d_one_i in range(len(x_list)):
        y_list.append('')
        x_one_list = x_list[x_d_one_i]
        for x_d_i in range(len(x_one_list)):
            x_d = x_one_list[x_d_i]
            start_index = get_timestamp_ms(x_d[1]) if date_is_time else int(x_d[1])
            end_index = get_timestamp_ms(x_d[2]) if date_is_time else int(x_d[2])
            x_p_list.append(
                {'value': [x_d_one_i,
                           start_index,
                           end_index,
                           end_index - start_index,
                           str(x_d[0]),
                           str(x_d[1]),
                           str(x_d[2])],
                 'itemStyle': {'normal': {'color': color_list[x_d_i % len(color_list)]}}})
    x_min = min((x_d['value'][1] for x_d in x_p_list), default=None)
    x_max = max((x_d['value'][2] for x_d in x_p_list), default=None)
    name = 'line_x' if name is None else name + '_line_x'
    x_list_str = '[\n    ' + ',\n    '.join(list(map(str, x_p_list))) + '\n]'
    return insert_data_to_chart(html_data=to_gantt_html(),
                                name=name,
                                x_min=x_min,
                                x_max=x_max,
                                height_limit=height_limit,
                                height_value=height_value,
                                show_text=show_text,
                                y_list=str(y_list),
                                x_list=x_list_str)


def to_chart_segment(data_list: list[list[list[str | Any]]],
                     name: str = None,
                     date_is_time: bool = False,
                     legend_show: bool = False,
                     tooltip_simple: bool = True,
                     symbol_size: int = 15,
                     line_style_width: int = 5,
                     name_raw: bool = False,
                     return_file: bool = True) -> str:
    """
    将数据整理成线段图, 一段一段的, 非连续的图
    x轴数据 : data_list = [
        [
            ['a', 1, 3, 4],
            ['b', 5, 6],
            ['c', 6, 9, 10, 11, 14]
        ]
     ]
     'a' : 线段名称
      1  : 开始 index
      3  : 中间 index
      4  : 结束 index
    name            : 文件名称,折线图的名称
    name_raw        : 用原始的名字,不用带上属性 line_stack
    date_is_time    : 数据是否是时间
    symbol_size     : 线上的点的大小
    line_style_width: 线的粗细
    legend_show     : 是否显示图例
    tooltip_simple  : 当鼠标放上去的时候,就简单的显示一下,不要显示那么多的信息
    """
    # {
    #     data: [
    #         [1, 1, {'name': 'a', 'differ': 1, 'from': '1', 'to': '2'}],
    #         [2, 1, {'name': 'a', 'differ': 1, 'from': '1', 'to': '2'}],
    #     ],
    #     symbolSize: 15,
    #     'itemStyle': {
    #         'normal': {
    #             'color': '#7fffd4'
    #         }
    #     },
    #     type: 'line'
    # }
    series = []
    x_min = None
    x_max = None
    color_list = get_default_color_list()
    color_index = 0
    for y_i in range(len(data_list)):
        d_list = data_list[y_i]
        for y_index in range(len(d_list)):
            d_o_data = []
            d_one = d_list[y_index]
            name_this = d_one[0]
            start_index = get_timestamp_ms(d_one[1]) if date_is_time else int(d_one[1])
            end_index = get_timestamp_ms(d_one[-1]) if date_is_time else int(d_one[-1])
            x_min = start_index if x_min is None else min(x_min, start_index)
            x_max = end_index if x_max is None else max(x_max, end_index)
            differ = end_index - start_index
            info_json = {'differ': differ, 'from': d_one[1], 'to': d_one[-1]}
            if len(d_one) >= 4:
                info_json['middle'] = d_one[2:-1]
            info_json_flag = True
            for p_point in d_one[1:]:
                d_o_data.append([get_timestamp_ms(p_point) if date_is_time else int(p_point), y_i + 1])
                if info_json_flag:
                    d_o_data[-1].append(info_json)
                    info_json_flag = False
            series.append({
                'name': name_this,
                'data': d_o_data,
                'symbolSize': symbol_size,
                'lineStyle': {'width': line_style_width},
                'itemStyle': {
                    'normal': {
                        'color': color_list[color_index % len(color_list)]
                    }
                },
                'type': 'line'
            })
            color_index += 1
    if not name_raw:
        name = 'line_segment' if name is None else name
    series_str = '[\n    ' + ',\n    '.join(list(map(str, series))) + '\n]'
    return insert_data_to_chart(html_data=to_line_segment_html(),
                                name=name,
                                series=series_str,
                                legend_show=legend_show,
                                tooltip_simple=tooltip_simple,
                                x_min=x_min,
                                y_min=0,
                                x_max=x_max,
                                y_max=len(data_list) + 1,
                                return_file=return_file)
