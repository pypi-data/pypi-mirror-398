import requests
import time
import urllib3
urllib3.disable_warnings()
def fetch_url_with_retries(url, headers=None, data=None, json=None, retries=15, delay=3, method="GET",proxies=None,cookies=None,params=None,verify=False,isReturnNone=True,stream=False,timeout=(60, 90)):
    """
    发送请求并在失败时重试。
    
    参数:
    - url: 请求的 URL。
    - headers: 请求头（可选）。
    - data: 表单数据（可选，用于 POST 请求）。
    - json: JSON 数据（可选，用于 POST 请求）。
    - retries: 最大重试次数。
    - delay: 每次重试之间的延迟时间（秒）。
    - method: 请求方法（"GET" 或 "POST"）。
    - proxies: 代理配置字典（可选）。
    timeout=(10, 20),  # (连接超时 10s, 读取超时 20s)
    返回:
    - 响应对象或 None（如果所有尝试都失败）。
    """
    try:
        print('-' * 10 + f"正在下载：{url}" + '-' * 10)
        attempt = 0
        while attempt < retries:
            try:
                if attempt + 1 != 1:
                    print(f"Attempt {attempt + 1}/{retries}")
                
                if method.upper() == "POST":
                    try:
                        response = requests.post(url, headers=headers, data=data, json=json, proxies=proxies,cookies=cookies,params=params,timeout=timeout,verify=verify,stream=stream)
                    except KeyboardInterrupt:
                        print("手动中断了请求！程序继续运行...")
                elif(method.upper() == "DELETE"):
                    try:
                        response = requests.delete(url, headers=headers, data=data, json=json, proxies=proxies,cookies=cookies,params=params,timeout=timeout,verify=verify,stream=stream)
                    except KeyboardInterrupt:
                        print("手动中断了请求！程序继续运行...")
                elif(method.upper() == "PUT"):
                    try:
                        response = requests.put(url, headers=headers, data=data, json=json, proxies=proxies,cookies=cookies,params=params,timeout=timeout,verify=verify,stream=stream)
                    except KeyboardInterrupt:
                        print("手动中断了请求！程序继续运行...")
                else:  # 默认使用 GET 请求
                    try:
                        response = requests.get(url, headers=headers, proxies=proxies, timeout=timeout,cookies=cookies,params=params,verify=verify,stream=stream)
                    except KeyboardInterrupt:
                        print("手动中断了请求！程序继续运行...")
                    
                response.raise_for_status()  # 如果状态码不是 2xx，则抛出 HTTPError
                return response
            except Exception as e:
                print(f"Request failed: {e}")
                attempt += 1
                if attempt < retries:
                    print(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
                else:
                    print("All retries failed.")
        if(isReturnNone):
            return None
        else:
            return response
    except Exception as e:
        if(isReturnNone):
            return None
        else:
            return response

