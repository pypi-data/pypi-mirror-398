from tmutils.base.lark.larkConfig import larkConfig
import json
import lark_oapi as lark
from lark_oapi.api.wiki.v2 import *
from lark_oapi.api.bitable.v1 import *
import requests
from tmutils.base.download import fetch_url_with_retries
import time

from typing import Dict, List, Optional, Any
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class larkOps(object):
    def __new__(cls, *args, **kwargs):
        # 调用父类的（object）的new方法，返回一个Ansible实例，这个实例传递给init的self参数
        return object.__new__(cls)

    def __init__(self,config:larkConfig,token,*args, **kwargs) -> None:
        self.config = config
        self.App_ID=self.config.App_ID
        self.App_Secret=self.config.App_Secret
        self.token=token
        # 创建client
        self.client = lark.Client.builder() \
            .app_id(self.App_ID) \
            .app_secret(self.App_Secret) \
            .log_level(lark.LogLevel.INFO) \
            .build()
    def __del__(self) -> None:...

    def get_knowledge_space_node_info(self,obj_type="wiki",*args, **kwargs):
        """
            获取知识空间节点信息
        """
        # 构造请求对象
        request: GetNodeSpaceRequest = GetNodeSpaceRequest.builder() \
            .token(self.token) \
            .obj_type(obj_type) \
            .build()
        # 发起请求
        response: GetNodeSpaceResponse = self.client.wiki.v2.space.get_node(request)
        # 处理失败返回
        if not response.success():
            lark.logger.error(
                f"client.wiki.v2.space.get_node failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}, resp: \n{json.dumps(json.loads(response.raw.content), indent=4, ensure_ascii=False)}")
            exit(127)
        # data=lark.JSON.marshal(response.data)
        # lark.logger.info(lark.JSON.marshal(response.data, indent=4))
        return response.data

    def build_search_request(self, app_token, table_id, view_id, field_names, page_size, page_token=None, automatic_fields=False, filter_info=None):
        # 统一请求构建逻辑
        request_body = SearchAppTableRecordRequestBody.builder() \
            .view_id(view_id) \
            .field_names(field_names) \
            .automatic_fields(automatic_fields)
        
        # 如果有过滤条件
        if filter_info:
            request_body = request_body.filter(filter_info)
        
        # 构建请求
        request_builder = SearchAppTableRecordRequest.builder() \
            .app_token(app_token) \
            .table_id(table_id) \
            .page_size(page_size) \
            .request_body(request_body.build())
        
        # 添加page_token
        if page_token:
            request_builder = request_builder.page_token(page_token)

        return request_builder.build()

    def multidimensional_table_query_records(self, table_id, view_id, page_size=20, field_names=[], automatic_fields=False, page_token=None, isFilter=False, filter_field_name="合作进度", filter_operator="is", filter_value=["已发布"], *args, **kwargs):
        app_token = self.get_knowledge_space_node_info().node.obj_token
        
        # 构建过滤条件
        filter_info = None
        if isFilter:
            filter_info = FilterInfo.builder() \
                .conjunction("and") \
                .conditions([Condition.builder()
                            .field_name(filter_field_name)
                            .operator(filter_operator)
                            .value(filter_value)
                            .build()
                            ]) \
                .build()

        # 构建请求
        request = self.build_search_request(app_token, table_id, view_id, field_names, page_size, page_token, automatic_fields, filter_info)

        # 发起请求
        response: SearchAppTableRecordResponse = self.client.bitable.v1.app_table_record.search(request)

        # 处理失败返回
        if not response.success():
            lark.logger.error(
                f"client.bitable.v1.app_table_record.search failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}, resp: \n{json.dumps(json.loads(response.raw.content), indent=4, ensure_ascii=False)}")
            exit(127)
        
        # 返回处理后的数据
        # lark.logger.info(lark.JSON.marshal(response.data, indent=4))
        return response.data

    def sheets_spreadsheets(self, range) -> dict:
        """
            如果知识库就是节点信息中的obj_token,云空间就是url中的token
            range设置为sheet_id
            默认就是获取所有数据
            后台需要开通：
            查看、评论、编辑和管理云空间中所有文件
            查看、评论和下载云空间中所有文件
            查看、评论、编辑和管理电子表格
            查看、评论和导出电子表格
        """
        doc_token = self.token

        # 构造请求对象
        request: lark.BaseRequest = lark.BaseRequest.builder() \
            .http_method(lark.HttpMethod.GET) \
            .uri("/open-apis/sheets/v2/spreadsheets/{}/values/{}".format(doc_token,range)) \
            .token_types({lark.AccessTokenType.TENANT}) \
            .build()

        # 发起请求
        response: lark.BaseResponse = self.client.request(request)

        # 处理失败返回
        if not response.success():
            lark.logger.error(
                f"client.request failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}")

        # 处理业务结果
        # lark.logger.info(str(response.raw.content, lark.UTF_8))
        str_data=str(response.raw.content, lark.UTF_8)
        data=json.loads(str_data)
        return data


class tenant_access_token(object):
    def __new__(cls, *args, **kwargs):
        return object.__new__(cls)

    def __init__(self,config:larkConfig,*args, **kwargs) -> None:
        self.config = config
        self.App_ID=self.config.App_ID
        self.App_Secret=self.config.App_Secret
        self.get_token()
        self.headers = {
            "Authorization": f"Bearer {self.tenant_access_token}",
            "Content-Type": "application/json; charset=utf-8"
        }

    def __del__(self) -> None:...

    def get_token(self):
        url = f"https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        headers={
            "Content-Type":"application/json; charset=utf-8"
        }
        body = {
            "app_id": self.App_ID,
            "app_secret": self.App_Secret
    }
        response = fetch_url_with_retries(method="POST",url=url, headers=headers, data=json.dumps(body))
        # print(response.json())
        self.tenant_access_token=response.json().get("tenant_access_token")

    def sheets_prepend_values(self,spreadsheet_token: str, sheet_range: str, values: list[list]) -> dict:
        """
        写入飞书表格
        :param token: 飞书 tenant 或 user access token（形如 t-xxxx）
        :param spreadsheet_token: 表格 token（非 URL）
        :param sheet_range: 写入范围，如 'Sheet1!A1:F5'
        :param values: 二维数组，每个元素是一行数据，例如 [["a", 1, "url", 12], ["b", 2, 3, "email"]]
        :return: 返回接口响应（字典）
        """
        url = f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{spreadsheet_token}/values_prepend"


        body = {
            "valueRange": {
                "range": sheet_range,
                "values": values
            }
        }

        response = fetch_url_with_retries(method="POST",url=url, headers=self.headers, data=json.dumps(body))
        try:
            return response.json()
        except Exception as e:
            return {"error": str(e), "status_code": response.status_code}
        
    def sheets_get_info(self, spreadsheet_token: str):
        """
            https://open.feishu.cn/document/server-docs/docs/sheets-v3/spreadsheet-sheet/get
        """
        url = f"https://open.feishu.cn/open-apis/sheets/v3/spreadsheets/{spreadsheet_token}/sheets/query"

        response = fetch_url_with_retries(url=url, headers=self.headers)
        try:
            return response.json()
        except Exception as e:
            return {"error": str(e), "status_code": response.status_code}

    def sheets_get_sheet_info(self, spreadsheet_token: str, sheet_id: str):
        """
            https://open.feishu.cn/document/server-docs/docs/sheets-v3/spreadsheet-sheet/get
        """
        url = f"https://open.feishu.cn/open-apis/sheets/v3/spreadsheets/{spreadsheet_token}/sheets/{sheet_id}"

        response = fetch_url_with_retries(url=url, headers=self.headers)
        try:
            return response.json()
        except Exception as e:
            return {"error": str(e), "status_code": response.status_code}

    def sheets_clear_sheet(self, spreadsheet_token: str, sheet_id: str,batch_size: int = 4000) -> None:
        """
            https://open.feishu.cn/document/server-docs/docs/sheets-v3/data-operation/prepend-data
            一次最多删除4999个需要从1开始而且必须保留一行
        """
        url = f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{spreadsheet_token}/dimension_range"

        if batch_size > 4999:
            batch_size = 4999

        while(True):
            time.sleep(3)
            info_data=self.sheets_get_sheet_info(spreadsheet_token=spreadsheet_token,sheet_id=sheet_id)
            # json_print(info_data)
            try:
                row_count=int(info_data['data']['sheet']['grid_properties']['row_count'])
            except Exception as e:
                row_count=0
            if(row_count==1):break
            if(batch_size>row_count):
                body = {
                    "dimension":{
                        "sheetId":sheet_id,
                        "majorDimension":"ROWS",
                        "startIndex":2,
                        "endIndex":row_count
                    }
                }
                response = fetch_url_with_retries(method="DELETE",retries=3,url=url, headers=self.headers, data=json.dumps(body))
                if(response==None):
                    print("文档有异常请检查,睡眠10秒钟")
                    time.sleep(10)
                # print(response.text)
            else:
                body = {
                    "dimension":{
                        "sheetId":sheet_id,
                        "majorDimension":"ROWS",
                        "startIndex":2,
                        "endIndex":batch_size
                    }
                }
                response = fetch_url_with_retries(method="DELETE",retries=3,url=url, headers=self.headers, data=json.dumps(body))
                # print(response.text)
                if(response==None):
                    print("文档有异常请检查,睡眠10秒钟")
                    time.sleep(10)

    def sheets_clear_first_row(self, spreadsheet_token: str, sheet_id: str) -> dict:
        """
        清空飞书多维表格第一行的所有值
        """
        url = f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{spreadsheet_token}/dimension_range"
        body = {
                "dimension":{
                    "sheetId":sheet_id,
                    "majorDimension":"ROWS",
                    "startIndex":1,
                    "endIndex":1
                }
            }
        fetch_url_with_retries(method="DELETE",retries=3,url=url, headers=self.headers, data=json.dumps(body))

    def sheets_write_first_row(self, spreadsheet_token: str, sheet_name: str, values: list[list]) -> dict:

        url = f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{spreadsheet_token}/values"

        body = {
            "valueRange":{
                "range": sheet_name+"!A1:Z1",
                "values": values
            }
        }

        write_response = fetch_url_with_retries(
            method="PUT",
            url=url,
            headers=self.headers,
            data=json.dumps(body)
        )

        try:
            return write_response.json()
        except Exception as e:
            return {"error": str(e), "status_code": write_response.status_code}


    def base_batch_write_record(self,app_token,table_id,data):
        """
        base 飞书多维表格
        批量数据写入
        在多维表格数据表中新增多条记录，单次调用最多新增 1,000 条记录。
        """
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_create"
        # data = {
        #     "records": [
        #         {"fields": {"GID": "张三", "获取时间": "内容1", "邮箱": "内容1", "标签": "内容1", "是否认证": "内容1"}},
        #         {"fields": {"GID": "张", "获取时间": "内容121", "邮箱": "内123容1", "标签": "内sda容1", "是否认证": "内容asd1"}},
        #     ]
        # }
        fetch_url_with_retries(method="POST",url=url,data=json.dumps(data),headers=self.headers)






class FeishuSheetClient:
    """飞书多维表格操作客户端"""
    # 飞书API基础URL
    BASE_URL = "https://open.feishu.cn"
    # 获取access_token的API端点
    TOKEN_URL = f"{BASE_URL}/open-apis/auth/v3/tenant_access_token/internal"
    # 多维表格API基础端点
    SHEET_BASE_URL = f"{BASE_URL}/open-apis/bitable/v1/apps"
    def __init__(self, app_id: str, app_secret: str):
        """
        初始化飞书客户端
        :param app_id: 飞书应用的app_id
        :param app_secret: 飞书应用的app_secret
        """
        self.app_id = app_id
        self.app_secret = app_secret
        self.access_token = None
        self.token_expire_time = 0  # 令牌过期时间（时间戳）
    def get_access_token(self) -> Optional[str]:
        """
        获取飞书应用的access_token
        :return: access_token字符串，如果获取失败则返回None
        """
        # 检查令牌是否仍然有效（提前60秒过期，避免网络延迟问题）
        if self.access_token and time.time() < self.token_expire_time - 60:
            return self.access_token
        try:
            headers = {"Content-Type": "application/json"}
            data = {
                "app_id": self.app_id,
                "app_secret": self.app_secret
            }
            response = requests.post(self.TOKEN_URL, json=data, headers=headers)
            response.raise_for_status()  # 抛出HTTP错误状态码
            result = response.json()
            if result.get("code") == 0:
                self.access_token = result.get("tenant_access_token")
                # 计算过期时间（当前时间 + 有效期，有效期单位为秒）
                self.token_expire_time = time.time() + result.get("expire", 3600)
                logger.info("成功获取access_token")
                return self.access_token
            else:
                logger.error(f"获取access_token失败: {result.get('msg')}")
                return None
        except Exception as e:
            logger.error(f"获取access_token时发生错误: {str(e)}")
            return None
    def _get_headers(self) -> Optional[Dict[str, str]]:
        """
        获取请求头（包含access_token）
        :return: 包含认证信息的请求头字典，如果获取token失败则返回None
        """
        token = self.get_access_token()
        if not token:
            return None
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
    def get_records(self, app_token: str, table_id: str, view_id: str, payload: dict, page_size=500):
        """
        https://open.feishu.cn/document/docs/bitable-v1/app-table-record/search
        """
        payload["view_id"] = view_id
        payload["automatic_fields"] = True
        result = []
        page_token = None
        headers = self._get_headers()
        while True:
            url = f"{self.SHEET_BASE_URL}/{app_token}/tables/{table_id}/records/search?page_size={page_size}"
            if page_token:
                url += f"&page_token={page_token}"
            response = requests.post(url, headers=headers, data=json.dumps(payload))
            resp_json = response.json()
            # print(json.dumps(resp_json, indent=4, ensure_ascii=False))
            if resp_json['code'] != 0:
                print(json.dumps(response.json(), indent=4, ensure_ascii=False))
                print('接口请求失败，退出程序')
                exit(127)
            result.extend(resp_json["data"]["items"])
            if resp_json["data"].get("has_more"):
                page_token = resp_json["data"].get("page_token")
                if not page_token:
                    break
            else:
                break
        return result
    def query_sheet_data(self, app_token: str, table_id: str, filter: Optional[str] = None,
                         fields: Optional[List[str]] = None, page_size: int = 100) -> Optional[List[Dict[str, Any]]]:
        """
        根据条件查询多维表格数据
        https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/reference/bitable-v1/filter
        :param app_token: 多维表格应用的token
        :param table_id: 表格ID
        :param filter: 筛选条件
        :param fields: 需要返回的字段列表，如果为None则返回所有字段
        :param page_size: 每页数据量
        :return: 符合条件的数据列表，如果查询失败则返回None
        """
        headers = self._get_headers()
        if not headers:
            return None
        all_records = []
        page_token = None
        try:
            while True:
                url = f"{self.SHEET_BASE_URL}/{app_token}/tables/{table_id}/records"
                params = {"page_size": page_size}
                if page_token:
                    params["page_token"] = page_token
                if filter:
                    params["filter"] = filter
                if fields:
                    params["field_names"] = json.dumps(fields, ensure_ascii=False)
                response = requests.get(url, headers=headers, params=params)
                response.raise_for_status()
                result = response.json()
                if result.get("code") != 0:
                    logger.error(f"查询表格数据失败: {result.get('msg')}")
                    print(f"查询表格数据失败: {result}")
                    return None
                records = result.get("data", {}).get("items", [])
                if not records:
                    break
                all_records.extend(records)
                page_token = result.get("data", {}).get("page_token")
                if not page_token:
                    break
            logger.info(f"成功查询到{len(all_records)}条数据")
            return all_records
        except Exception as e:
            logger.error(f"查询表格数据时发生错误: {str(e)}")
            return None
    def get_sheet_record(self, app_token: str, table_id: str, record_id: str) -> Optional[Dict[str, Any]]:
        """
        获取单条记录详情
        :param app_token: 多维表格应用的token
        :param table_id: 表格ID
        :param record_id: 记录ID
        :return: 记录详情字典，如果查询失败则返回None
        """
        headers = self._get_headers()
        if not headers:
            return None
        try:
            url = f"{self.SHEET_BASE_URL}/{app_token}/tables/{table_id}/records/{record_id}"
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            result = response.json()
            if result.get("code") != 0:
                logger.error(f"获取记录详情失败: {result.get('msg')}")
                return None
            logger.info(f"成功获取记录 {record_id} 的详情")
            return result.get("data", {}).get("record")
        except Exception as e:
            logger.error(f"获取记录详情时发生错误: {str(e)}")
            return None
    def update_sheet_record(self, app_token: str, table_id: str, record_id: str,
                            fields: Dict[str, Any]) -> bool:
        """
        更新多维表格中的记录
        :param app_token: 多维表格应用的token
        :param table_id: 表格ID
        :param record_id: 要更新的记录ID
        :param fields: 要更新的字段字典，例如{"姓名": "李四", "年龄": 30}
        :return: 更新成功返回True，否则返回False
        """
        headers = self._get_headers()
        if not headers:
            return False
        try:
            url = f"{self.SHEET_BASE_URL}/{app_token}/tables/{table_id}/records/{record_id}"
            # 构建更新数据，飞书API要求字段数据放在fields键下
            data = {"fields": fields}
            response = requests.put(url, json=data, headers=headers)
            response.raise_for_status()
            result = response.json()
            print(result)
            if result.get("code") == 0:
                logger.info(f"成功更新记录 {record_id}")
                return True
            else:
                logger.error(f"更新记录失败: {result}")
                return False
        except Exception as e:
            logger.error(f"更新记录时发生错误: {str(e)}")
            return False
    def delete_sheet_record(self, app_token: str, table_id: str, record_id: str) -> bool:
        """
        删除多维表格中的记录
        :param app_token: 多维表格应用的token
        :param table_id: 表格ID
        :param record_id: 要删除的记录ID
        :return: 删除成功返回True，否则返回False
        """
        headers = self._get_headers()
        if not headers:
            return False
        try:
            url = f"{self.SHEET_BASE_URL}/{app_token}/tables/{table_id}/records/{record_id}"
            response = requests.delete(url, headers=headers)
            response.raise_for_status()
            result = response.json()
            if result.get("code") == 0:
                logger.info(f"成功删除记录 {record_id}")
                return True
            else:
                logger.error(f"删除记录失败: {result.get('msg')}")
                return False
        except Exception as e:
            logger.error(f"删除记录时发生错误: {str(e)}")
            return False
    def create_sheet_record(self, app_token: str, table_id: str, data_list: List[Dict[str, Any]]) -> Optional[
        List[Dict[str, Any]]]:
        """
        在多维表格中创建新记录
        :param app_token: 多维表格应用的token
        :param table_id: 表格ID
        :param fields: 新记录的字段字典
        :return: 新创建记录的ID，如果创建失败则返回None
        """
        headers = self._get_headers()
        if not headers:
            return None
        try:
            url = f"{self.SHEET_BASE_URL}/{app_token}/tables/{table_id}/records/batch_create"
            records = []
            for item in data_list:
                records.append({"fields": item})
            data = {
                "records": records
            }
            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()
            result = response.json()
            if result.get("code") == 0:
                records_created = result.get("data", {}).get("records", [])
                logger.info(f"成功创建新记录，data: {records_created}")
                return records_created
            else:
                logger.info(f'{result}')
                logger.error(f"创建记录失败: {result.get('msg')}")
                return None
        except Exception as e:
            logger.error(f"创建记录时发生错误: {str(e)}")
            return None




if __name__ == "__main__":
    APP_TOKEN = "APP_TOKEN"
    TABLE_ID = "TABLE_ID"
    client = FeishuSheetClient()
    token = client.get_access_token()
    if token:
        print(f"获取到access_token: {token}")
    # 示例：查询记录这里查询的数据不能过大
    records = client.query_sheet_data(APP_TOKEN, TABLE_ID, filter="CurrentValue.[年龄]>35", fields=["文本", "年龄"])
    if records:
        print(f"查询到{len(records)}条记录:")
        for record in records:
            print(record)
    modify_record_id = records[-1].get('record_id')
    sheet_record = client.get_sheet_record(APP_TOKEN, TABLE_ID, modify_record_id)
    print(sheet_record)
    # 示例：创建记录
    records_created = client.create_sheet_record(APP_TOKEN, TABLE_ID, [{
        "文本": "用户",
        "年龄": 30
    }, {
        "文本": "用户2",
        "年龄": 10
    }])
    if records_created:
        print(f"创建新记录成功: {records_created}")
    # 示例：更新记录
    update_success = client.update_sheet_record(APP_TOKEN, TABLE_ID, modify_record_id, {
        "年龄": 35,
        "文本": "工程师"
    })
    print(f"更新记录{'成功' if update_success else '失败'}")
    # 示例：删除记录
    delete_success = client.delete_sheet_record(APP_TOKEN, TABLE_ID, modify_record_id)
    print(f"删除记录{'成功' if delete_success else '失败'}")