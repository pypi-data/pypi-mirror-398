import pandas as pd
from google.cloud import bigquery
import os,sys

class BQops(object):
    """
    api文档
    https://cloud.google.com/bigquery/docs/reference/libraries?hl=zh-cn
    管理的后台
    https://console.cloud.google.com/bigquery
    """
    def __new__(cls, *args, **kwargs):
        return object.__new__(cls)
    def __init__(self,BQ_config:dict,table,api_json_file_path=None,*args, **kwargs) -> None:
        """
            table: netbug.table
            api_json_file_path="./config/BQ-config.json"
        """
        if(api_json_file_path==None):
            self.client = bigquery.Client.from_service_account_info(BQ_config)
        else:
            self.client = bigquery.Client.from_service_account_json(api_json_file_path)
        self.table=table
    def __del__(self) -> None:...
    def excel_insert(self,filePath='./config/insert.xlsx'):
        #准备数据
        df = pd.read_excel(filePath)
        # Client 认证
        # 将 DataFrame 转换为 BigQuery 表
        table_id = self.table # Database.table
        job_config = bigquery.LoadJobConfig()

        #下面这一句加了则replace，不加则insert
        # job_config.write_disposition = bigquery.WriteDisposition.WRITE_TRUNCATE
        job = self.client.load_table_from_dataframe(df, table_id, job_config=job_config)
        job.result()  # 等待导入操作完成

    def insert(self,df,isReplace=False):
        # 将 DataFrame 转换为 BigQuery 表
        table_id = self.table # Database.table
        job_config = bigquery.LoadJobConfig()
        if(isReplace):
            # 下面这一句加了则replace，不加则insert
            job_config.write_disposition = bigquery.WriteDisposition.WRITE_TRUNCATE

        job = self.client.load_table_from_dataframe(df, table_id, job_config=job_config)
        job.result()  # 等待导入操作完成 
