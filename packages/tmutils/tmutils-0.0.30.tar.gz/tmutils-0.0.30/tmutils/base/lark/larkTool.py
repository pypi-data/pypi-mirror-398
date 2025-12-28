from tmutils.base.lark.larkOps import larkOps
from tmutils.base.lark.larkConfig import larkConfig
from tmutils.base.utils import clean_invisible_chars, find_keys, alert_print_error

def get_feishu_sheets_data(config:larkConfig,token,range,index:int=0,key_index:int=0,values_index:int=1,*args, **kwargs) -> dict:
    """
    获取飞书表格数据
    :param token: 飞书表格的token
    :param range: 表格的范围
    :param index: 表格的索引
    :param key_index: 键的索引
    :param values_index: 值的索引
    :return: 返回一个字典，包含键和值
    """
    data=larkOps(config,token=token).sheets_spreadsheets(range=range)
    original=data['data']['valueRange']['values']
    keys =original[key_index]
    values = original[values_index:]
    index_data=[]
    # print(values)
    # index_data=[clean_invisible_chars(item[index]) for item in values]
    for i, item in enumerate(values):
        try:
            value = item[index]
            if not isinstance(value, (str, int,float)):
                continue  # 跳过非字符串和非整数
            clean_value = clean_invisible_chars(str(value))
            index_data.append(clean_value)
        except Exception as e:
            alert_print_error(e)
            print(f"[错误] 第 {i} 项处理失败: {item}，错误信息: {e}")
    
    all_values_text = []
    for value in values:
        temp = []
        for item in value:
            if isinstance(item, (list,dict)):
                texts = find_keys(item, "text")
                if texts:
                    temp.append(clean_invisible_chars(texts[0]))
                else:
                    temp.append("")
            else:
                temp.append(clean_invisible_chars(str(item)))
        all_values_text.append(temp)


    return {
        "original":original,
        "keys":keys,
        "values":values,
        "index_data":index_data,
        "all_values_text":all_values_text,
        "values_map_json":[dict(zip(keys, row)) for row in values]

    }