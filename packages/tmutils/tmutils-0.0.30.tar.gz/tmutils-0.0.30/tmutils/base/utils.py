import traceback
from urllib.parse import unquote, urlparse, parse_qs
from datetime import datetime, timezone, timedelta
import re,math,json,time,os
import functools
from bs4 import BeautifulSoup
from tqdm import tqdm
import uuid
import schedule
import unicodedata
import ast
import sys
import string


def get_now_time():
    now_time=datetime.now().strftime("%Y年%m月%d日%H时%M分%S秒")
    return now_time

def get_unique_id():
    unique_id = str(uuid.uuid4())
    return unique_id

def get_last_cli_arg() -> str:
    """
    获取命令行中最后一个参数（不包括脚本文件名本身）。
    若没有提供参数，则返回空字符串。
    """
    if len(sys.argv) > 1:
        return sys.argv[-1]
    return ""


def get_valid_input(value="yes"):
    """
    等待用户输入，判断输入是否符合预期，如果不符合则要求重新输入。

    :param value: 预期值的列表或集合
    :return: 符合预期的输入值
    """
    while True:
        user_input = input("请输入值：")  # 等待用户输入
        if(user_input=='exit'):
            exit(0)
        if user_input == value:
            return user_input
        else:
            print(f"输入无效，请重新输入")

def extract_rating(text):
    """
        5 out of 5 stars --> 5
        4.5 out of 5 stars --> 4.5
        This is not a rating --> None 
    """
    match = re.search(r'^(\d(?:\.\d)?) out of 5 stars$', text.strip())
    if match:
        return match.group(1)
    else:
        return None

# 读取 JSON 文件
def read_json_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            return data
    except FileNotFoundError:
        print(f"The file at {file_path} was not found.")
    except json.JSONDecodeError:
        print(f"Error decoding the JSON file: {file_path}")
    except Exception as e:
        print(f"An error occurred: {e}")

def decoded_url(url):
    # url = "/sspa/click?ie=UTF8&amp;spc=MTo1OTU2MTUzNTIyMzcwNzE2OjE3MzUwOTE2MTg6c3BfYXRmOjMwMDM3OTgzMTg2MzMwMjo6MDo6&amp;url=%2FSimeider-Glueless-Plucked-Closure-Density%2Fdp%2FB0D6BNF5TG"
    decoded_url = unquote(url.replace("&amp;", "&"))
    return {"decoded_url":decoded_url}

def alert_print_error(e):
    error_message = traceback.format_exc()
    content="错误日志--->报错如下:\n"+str(e)+"\n报错栈如下:\n"+str(error_message)
    print(content)

def uri_get_url(url):
    """
    处理 URL 中的参数，返回完整的 URL
    :param url: 原始 URL
    :return: 完整的 URL
    """
    # url='https://www.amazon.com/IAMFUPO-Front-Density-Frontal-Plucked/dp/B0DHBXSCXH/ref=sr_1_1_sspa?crid=3U1ISFQPLITJW&dib=eyJ2IjoiMSJ9.71MHe44fy4iOhL_0s8pOYDmgs9L9DU9BJ7SrTYJ6Gg536jaqEdkjqVc6t3Fii9bWDlPkKOM3kwHtKSOA4FCrYwMko33Cx5idCqA9BMu1XRA58jrxUQ2_Y8GP0M2c0CUNpmTF31nDQ5BQ-PFRQMTy957FYKQCCSd4KXqbDABC4UAvBlGbzWctSGgHfWdUrJKCy1VzeaVA76c7kMDN5mWbLaXbEokxIJIzJbqjRB0Q2bdC5pYuHPej-7maEVa6LjyJ9MvJv1Wsm1sLJJtYyeX19Dtav1KLbT1U7jtooClcyCE.SbrkZ349QgaJpS2slZ1tvPB6YRHTk385FaNG5irvaeA&dib_tag=se&keywords=human+hair+wig&qid=1734344206&s=beauty&sprefix=human+hair+wig%2Cbeauty%2C872&sr=1-1-spons&sp_csd=d2lkZ2V0TmFtZT1zcF9hdGY&psc=1'
    # url = "https://www.amazon.com/sspa/click?ie=UTF8&spc=MToxMTkxNDg4NDIyNDMyOTU4OjE3MzUwOTgzMDM6c3BfYXRmOjMwMDU5MTc1MzUxNzQwMjo6MDo6&url=%2FPlucked-Bleached-Frontal-Density-Glueless%2Fdp%2FB0DLMT3QXV%2Fref%3Dsr_1_1_sspa%3Fcrid%3D13OPBCOANL41Z%26dib%3DeyJ2IjoiMSJ9.3S7n2T24TNkgXfrmz9WxAbrXQ9V5XDL0wBPE8qXNdSU3uOq3Irbg7Zl3oqYwKq45Sgjx1LCM8YHYUfiYdk2LpyeWYBWgHuCCLePlex5xFV4idYITdVe_WzcvYVNqYuMKkvxqiOVk02kymTjuCDISAWRY0RccYyei15H4bf4A9whi1qQFFMU9j8KQbwkGi9MvvGyM6sbDWmwsWyBhgLUpINQCkdScHwvdktwQAuKywyvC3AuszoXLvm4nkkRVHS44cBAnStUWvfe8PxhqAy0W3pXpHV8y0W0xpxC5GgMkMt4.ppkJ9hZ7pKO2XfIl7EsePeJq_OLIH8jVJU3t1TkGqak%26dib_tag%3Dse%26keywords%3Dhuman%2Bhair%2Bwig%26qid%3D1735098303%26s%3Dbeauty%26sprefix%3D%252Cbeauty%252C1209%26sr%3D1-1-spons%26sp_csd%3Dd2lkZ2V0TmFtZT1zcF9hdGY%26psc%3D1"
    if("url=" in url):
        domain = url.split('/')[0] + '//' + url.split('/')[2]
        # 解析 URL 参数
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        # 提取并解码 'url' 参数
        decoded_uri = unquote(query_params.get('url', [''])[0])
        # 拼接完整链接
        complete_url = f"{domain}{decoded_uri}"
        return complete_url
    else:
        return url
    
def html_prettify_print(html_str):
    """
    美观地输出 HTML
    :param html_str: HTML 字符串
    """
    soup = BeautifulSoup(html_str, 'html.parser')
    # 美观地输出 HTML
    formatted_html = soup.prettify()
    print(formatted_html)

def get_html_soup(html_str):
    soup = BeautifulSoup(html_str, 'html.parser')
    return soup

def is_valid_email(email):
    # 正则表达式，用来判断邮箱格式
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if re.match(pattern, email):
        return True
    return False

def clean_invisible_chars(text):
    """
    清除文本中的不可见字符
    :param text: 输入文本
    :return: 清除不可见字符后的文本
    参考链接：https://www.unicode.org/reports/tr9/#Invisible_Characters
    参考链接：https://www.unicode.org/reports/tr44/#General_Category_Values
    """
    if not isinstance(text, str):
        print(text)
        raise ValueError(f"传入的 text 不是字符串，而是: {type(text)}")
    return re.sub(r'[\u200b-\u200f\u202a-\u202e\u2060-\u206f]', '', text)


def get_str_email(value):
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    # 使用正则表达式删除所有非字母、数字和邮箱符号的字符
    value_str = re.sub(r'[^\w\s@._-]', '', value)
    try:
        if(is_valid_email(re.findall(email_pattern, value_str)[0])):
            email=re.findall(email_pattern, value_str)[0]
        else:
            email=""
    except:
        email=""
    return email

def int_to_time(value):
    """
        https://q1my9tkfihy.feishu.cn/sheets/C6N1sGNeRhwDyOtPh9UciqH7nIh?sheet=1IOdje
        https://open.feishu.cn/document/server-docs/docs/sheets-v3/sheets-faq#a0bc47ca

        日期字段返回的是45658就是自 1899 年 12 月 30 日以来的天数；
        45658, 'Tape in Hair: Hair Extension',....
    """
    # 1899年12月30日作为起始日期
    start_date = datetime(1899, 12, 30)
    # 45658 天后
    delta = timedelta(days=value)
    result_date = start_date + delta
    # 输出转换后的日期
    return result_date.strftime('%Y-%m-%d')

def time_to_int(date_str):
    """
        print(time_to_int('2024-03-12'))  # 输出：45286
    """
    start_date = datetime(1899, 12, 30)
    target_date = datetime.strptime(date_str, '%Y-%m-%d')
    delta = target_date - start_date
    return delta.days

def json_print(data):
    print(json.dumps(data,indent=4,ensure_ascii=False))

def find_keys(data, target_key) -> list:
    results = []
    if isinstance(data, dict):
        for k, v in data.items():
            if k == target_key:
                results.append(v)
            results.extend(find_keys(v, target_key))
    elif isinstance(data, list):
        for item in data:
            results.extend(find_keys(item, target_key))
    return results

def find_json_list(data, json_key, path="", *a, **k) -> list:
    """
        data是一个dict或list
        json_key需要搜索的关键字
        这里会返回一个列表，包含所有找到的列表节点
    """
    results = []  # 用来存储所有找到的edges内容
    if isinstance(data, dict):
        for key, value in data.items():
            if key == json_key and isinstance(value, list):
                results.extend(value)  # 找到就把整个列表加入
            else:
                # 递归调用，并把子结果合并进来
                results.extend(find_json_list(value, json_key=json_key, path=path + f".{key}"))
    elif isinstance(data, list):
        for index, item in enumerate(data):
            # 同样递归调用并合并子结果
            results.extend(find_json_list(item, json_key=json_key, path=path + f"[{index}]"))
    return results

def find_first_key_value(data, target_key, *a, **k):
    """
    递归查找指定key的第一个value，找到就返回，没找到返回None
    :param data: 任意嵌套的dict或list
    :param target_key: 目标key
    :return: 第一个找到的value或者None
    """
    if isinstance(data, dict):
        for key, value in data.items():
            if key == target_key:
                return value  # 找到就直接返回
            found = find_first_key_value(value, target_key)
            if found is not None:
                return found  # 子层找到就直接返回
    elif isinstance(data, list):
        for item in data:
            found = find_first_key_value(item, target_key)
            if found is not None:
                return found
    return None  # 都没找到返回None

def timestamp_to_datetime(timestamp, timezone_offset=8)->dict:
    import datetime
    """
    自动判断时间戳是秒级还是毫秒级，并转换为可读时间格式（本地时间+UTC时间）
    :param timestamp: int or str，Unix时间戳（秒级或毫秒级都支持）
    :param timezone_offset: int，时区偏移（默认东八区：北京时间）
    :return: dict，包含UTC时间和本地时间
    """
    # 确保时间戳是整数类型
    timestamp = int(timestamp)
    # 判断是秒级还是毫秒级（长度10是秒级，13是毫秒级）
    if len(str(timestamp)) == 13:
        # 毫秒级时间戳，先转成秒
        timestamp = timestamp / 1000
    # UTC时间
    # utc_time = datetime.datetime.utcfromtimestamp(timestamp) #方法已弃用
    utc_time = datetime.datetime.fromtimestamp(timestamp, tz=datetime.timezone.utc)
    # 本地时间（带时区偏移）
    local_time = utc_time + datetime.timedelta(hours=timezone_offset)
    return {
        "utc_time": utc_time.strftime("%Y-%m-%d %H:%M:%S"),
        "local_time": local_time.strftime("%Y-%m-%d %H:%M:%S"),
        "timezone_offset": f"UTC+{timezone_offset}"
    }

def isdigit(value):
    """检查字符串是否为数字，返回布尔值"""
    try:
        float(value)  # Try converting to a float
        return True
    except ValueError:
        return False

def is_url(value):
    # URL 的正则表达式模式
    pattern = re.compile(
        r'^(https?|ftp)://[^\s/$.?#].[^\s]*$', re.IGNORECASE)
    # 如果匹配正则表达式，说明是 URL
    return bool(pattern.match(value))

def has_real_characters(text):
    """
        L代表字母（包括中文、日文、韩文、英文等所有文字字符）。
        N代表数字。
        空格、表情符号、特殊符号都不会算。
    """
    # 去掉空白字符
    text = text.strip()
    # 遍历每个字符
    for char in text:
        # 跳过空白符、表情符号、特殊符号等
        if char.isspace():
            continue
        
        # 获取字符的类别（General Category），比如：So=Symbol Other，Lo=Letter Other
        char_category = unicodedata.category(char)
        
        # 只要是字母、数字、汉字这些就算是"有正常字符"
        if char_category.startswith(('L', 'N')):
            return True
    return False

def retry(max_retries=5, delay=3,is_valid=False,is_raise=False,default_return=None):
    """通用的重试装饰器
    max_retries: 最大重试次数
    delay: 失败后等待的秒数
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    retries += 1
                    print(f"尝试操作{retries}/{max_retries}")
                    alert_print_error(e)
                    if retries == max_retries:
                        print("尝试次数达到最大")

                        if(is_valid):
                            print("确保程序没有问题,然后输入go on继续操作:")
                            get_valid_input(value="go on")

                        if is_raise:
                            raise
                        
                        return default_return
                    time.sleep(delay)  # 正确使用 delay
        return wrapper
    return decorator  # 确保返回的是装饰器

def get_html_script_json(html,script_id="",script_type="application/ld+json",key="",*args, **kwargs) -> dict:
    """
    从 HTML 中获取 <script> 里的 JSON 数据
    :param html: HTML 源码
    :param script_type: <script> 标签的 type (默认 "application/ld+json")
    :return: JSON 数据列表
    """
    # 使用 BeautifulSoup 解析 HTML
    soup = BeautifulSoup(html, 'html.parser')

    # 查找特定的 <script> 标签
    #获取一个
    # json_script = soup.find('script', type="application/ld+json")
    #获取多个
    if script_id:
        json_scripts = soup.find_all("script", {"type": script_type})
    else:
        json_scripts = soup.find_all("script", {"type": script_type,"id":script_id})
    for script in json_scripts:
        html_str=script.string
        if html_str:  # 确保内容不为空
            try:
                json_data = json.loads(html_str)
                # 如果指定了 key，则过滤出包含该 key 的 JSON
                if key:
                    if key in json_data:
                        return json_data
            except Exception as e:
                print("JSON 解析失败:", html_str[:100])  # 打印部分内容进行调试
                alert_print_error(e)

    return {}

def get_html_script_re_str(html,script_type="text/javascript",key=""):
    """
    从 HTML 中获取 <script> 里的 str 数据
    :param html: HTML 源码
    :param script_type: <script> 标签的 type (默认 "text/javascript")
    :return: 字符串数据
    """
    soup = BeautifulSoup(html, 'html.parser')
    json_scripts = soup.find_all("script", {"type": script_type})
    html_str=""
    for script in json_scripts:
        html_str=script.string
        if(key not in str(html_str)):continue
    return html_str


def set_cookie_json(set_cookie):
    """
    请求头中获取到set_cookie: PHPSESSID=qsodepo9rhnh19k0cke46lsnv0; path...
    将下面的这个变成json格式
    PHPSESSID=qsodepo9rhnh19k0cke46lsnv0; path=/, mysid=d35e0cee8708c90d4b530e3e60e6301d; expires=Thu, 03-Apr-2025 03:42:25 GMT; Max-Age=604800; path=/;, user_token=627990-miaomao572167e4c9215fda5; expires=Thu, 03-Apr-2025 03:42:25 GMT; Max-Age=604800; path=/
    """
    cookie_dict = {}
    cookies = set_cookie.split(", ")  # 先按 `, ` 拆分（多个 Set-Cookie）
    for c in cookies:
        parts = c.split(";")[0]  # 取 `key=value` 部分
        if "=" in parts:
            key, value = parts.split("=", 1)  # 只分割第一个 `=`
            cookie_dict[key.strip()] = value.strip()
    return cookie_dict




def normalize_fancy_letters(text: str) -> str:
    """
    将 Unicode fancy 字母（如数学粗体、斜体、花体等）还原为普通英文 A-Z / a-z。
    """
    result = ""
    for char in text:
        code = ord(char)
        # 数学粗体大写 A-Z
        if 0x1D400 <= code <= 0x1D419:
            result += chr(code - 0x1D400 + ord('A'))
        # 数学粗体小写 a-z
        elif 0x1D41A <= code <= 0x1D433:
            result += chr(code - 0x1D41A + ord('a'))
        # 数学斜体 A-Z
        elif 0x1D434 <= code <= 0x1D44D:
            result += chr(code - 0x1D434 + ord('A'))
        # 数学斜体 a-z
        elif 0x1D44E <= code <= 0x1D467:
            result += chr(code - 0x1D44E + ord('a'))
        # 数学粗斜体 A-Z
        elif 0x1D468 <= code <= 0x1D481:
            result += chr(code - 0x1D468 + ord('A'))
        # 数学粗斜体 a-z
        elif 0x1D482 <= code <= 0x1D49B:
            result += chr(code - 0x1D482 + ord('a'))
        # 花体大写 A-Z（跳过空位）
        elif code in range(0x1D4D0, 0x1D4E9):
            result += chr(code - 0x1D4D0 + ord('A'))
        # 花体小写 a-z
        elif 0x1D4EA <= code <= 0x1D503:
            result += chr(code - 0x1D4EA + ord('a'))
        # 双线体小写 a-z
        elif 0x1D552 <= code <= 0x1D56B:
            result += chr(code - 0x1D552 + ord('a'))
        # 双线体大写 A-Z（不连续）
        elif 0x1D538 <= code <= 0x1D551:
            result += chr(code - 0x1D538 + ord('A'))
        # 𝓐–𝔃 花体、哥特体（常见组合）——明确编码范围
        elif 0x1D4D0 <= code <= 0x1D4F9:  # 𝓐–𝓩
            result += chr(code - 0x1D4D0 + ord('A'))
        elif 0x1D4EA <= code <= 0x1D503:  # 𝓪–𝔃
            result += chr(code - 0x1D4EA + ord('a'))
        # 特例字符（无法通过编码计算）
        elif char in 'ℂℍℕℙℚℝℤ':
            result += {
                'ℂ': 'C', 'ℍ': 'H', 'ℕ': 'N', 'ℙ': 'P',
                'ℚ': 'Q', 'ℝ': 'R', 'ℤ': 'Z'
            }[char]
        else:
            result += char
    return result


def deep_get(dic, keys, default=None):
    """多级键安全获取"""
    for key in keys:
        if isinstance(dic, dict):
            dic = dic.get(key, default)
        else:
            return default
    return dic


def dict_list_to_rows(dict_list, fields=None):
    """
    将一组字典按指定字段顺序转换为二维列表。
    
    :param dict_list: List[Dict]，如 data
    :param fields: List[str]，要提取的字段顺序
    :return: List[List]，二维列表
    """
    if not dict_list:
        return []

    if fields is None:
        fields = list(dict_list[0].keys())  # 默认按第一个字典的键顺序

    return [[d.get(field, '') for field in fields] for d in dict_list]






def get_config_json(config_path="config/settings_prod.json") -> None:
    try:
        settings_prod_data = read_json_file(config_path)
        return settings_prod_data
    except Exception as e:
        alert_print_error(e)
        exit(127)



def schedule_run(get_time_at, job, config_path="config/settings_prod.json", time_int: int = 1, day: str = None) -> None:
    """
    按指定时间和周期调度任务。

    参数:
        get_time_at (str): settings_prod_data 中时间字段的 key。
        job (function): 要执行的函数。
        config_path (str): 配置文件路径，默认是 "config/settings_prod.json"。
        time_int (int): 调度轮询间隔（秒），默认 60 秒。
        day (str or None): 指定星期几执行（如 "friday"）。为 None 时每天执行。
    """
    try:
        settings_prod_data = read_json_file(config_path)
        at_time = settings_prod_data[get_time_at]
    except (FileNotFoundError, KeyError) as e:
        print(f"[ERROR] 配置读取失败: {e}")
        exit(127)

    day = day.lower() if day else None

    if day is None:
        schedule.every().day.at(at_time).do(job)
    elif day in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]:
        getattr(schedule.every(), day).at(at_time).do(job)
    else:
        print(f"[ERROR] 不支持的星期参数: {day}")
        exit(127)
    

    # if(day==None):
    #     schedule.every().day.at(at_time).do(job)
    # elif(day=="friday"):
    #     schedule.every().friday.at(at_time).do(job)


    print(f"[INFO] 已调度任务: {day or 'every day'} at {at_time}")

    while True:
        schedule.run_pending()
        time.sleep(time_int)



def safe_extract_mapping(list_map, key, value):
    """
    从字典列表中安全提取指定字段键值对，构建映射关系。
    参数:
        list_map (list): 字典组成的列表。
        key (str): 映射中作为键的字段名。
        value (str): 映射中作为值的字段名。

    返回:
        dict: 由 key 到 value 的映射字典。仅包含同时存在两个字段的项。
    """
    mapping = {}
    for item in list_map:
        if isinstance(item, dict) and key in item and value in item:
            mapping[item[key]] = item[value]
    return mapping

    
def show_progress(iterable, desc="Processing",disable=False,leave=False,bar_format='{l_bar}{bar} {n_fmt}/{total_fmt}', *a,**k):
    """
    显示进度条
    """
    return tqdm(iterable, desc=desc, disable=disable, bar_format=bar_format, **k)


def iter_with_progress(items, prefix="开始处理"):
    total = len(items)
    for idx, item in enumerate(items, start=1):
        print(f"{prefix} [{idx}/{total}]: {item}")
        yield item



def extract_first_email(text):
    emails = re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', text)
    first_email = emails[0] if emails else ""
    email = first_email.lstrip('-.')
    return email


def run_cmd(cmd):
    """
    兼容 Python 3.6+ 的 shell 命令执行
    返回 str
    """
    kwargs = {
        "shell": True,
        "stderr": subprocess.STDOUT
    }
    # Python 3.7+ 支持 text=True
    if sys.version_info >= (3, 7):
        kwargs["text"] = True
    else:
        kwargs["universal_newlines"] = True
    return subprocess.check_output(cmd, **kwargs).strip()
