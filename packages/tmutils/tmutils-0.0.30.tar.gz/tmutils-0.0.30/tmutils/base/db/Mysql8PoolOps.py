from tmutils.base.db.Mysql8Pool import Mysql8Pool
from tmutils.base.utils import retry
import time
from tmutils.base.db.Mysql8Config import Mysql8Config
class Mysql8PoolOps(object):
    """
    mysql sql操作
    """
    def __init__(self,config: Mysql8Config,table_name="test_table_name",*args, **kwargs) -> None:
        self.config = config
        self.db = self.init_mysql_pool()
        self.table_name=table_name
        self.columnList=self.db.getTableInfo(self.table_name)['columnList']
        self.systems_field=["id","system_id","system_create_time","system_update_time","system_create_timestamp"]
        self.KeyCommentJson=self.db.getTableInfo(self.table_name)['KeyCommentJson']
        self.Allcolumns = ','.join([f"`{col}`" for col in self.columnList])
        self.columns = ','.join([f"`{col}`" for col in [x for x in self.columnList if x not in self.systems_field]])
        # print(self.KeyCommentJson)



    def __del__(self, *args, **kwargs):...

    def init_mysql_pool(self,retries=15, delay=5):
        for attempt in range(retries):
            try:
                return Mysql8Pool(self.config)
            except Exception as e:
                print(f"[尝试 {attempt+1}/{retries}] 数据库连接失败: {e}")
                time.sleep(delay)
        raise RuntimeError("数据库连接重试失败，已放弃。")


    def sequence_field(self,data,*args, **kwargs):
        """
            正序
        """
        # 找到两个字典的交集字段
        common_keys = set(data.keys()) & set(self.KeyCommentJson.keys())  # 获取交集的键
        # 过滤出交集部分的数据
        validInsertData = {key: data[key] for key in common_keys}
        # print(validInsertData)
        return validInsertData


    def reversed_field(self,data,*args, **kwargs):
        """
            反序
        """
        
        validInsertData = {key: value for key, value in data.items() if key in self.KeyCommentJson.values()}
        # 反转 KeyCommentJson，将中文描述映射到英文字段
        reversed_KeyCommentJson = {v: k for k, v in self.KeyCommentJson.items()}
        # 将 intersection 的键转换为对应的英文字段名
        reversed_validInsertData = {reversed_KeyCommentJson[key]: value for key, value in validInsertData.items() if key in reversed_KeyCommentJson}
        return reversed_validInsertData
    
    def reversed_lists(self,field_list,*args, **kwargs):
        """
            反序字段-列表
        """
        # 根据描述映射到实际的字段名
        description_to_key = {v: k for k, v in self.KeyCommentJson.items()}

        # 获取对应的字段名
        selected_keys = [description_to_key[desc] for desc in field_list if desc in description_to_key]

        return selected_keys
    @retry()
    def get_select_all(self, *args, **kwargs):
        select_sql="SELECT * FROM `"+self.table_name+"`;"
        GetSQL = self.db.fetchall(select_sql)
        return GetSQL

    @retry()
    def get_select_where_str(self,where_str, *args, **kwargs):
        where_select_sql="SELECT * FROM `"+self.table_name+"`"+" where "+where_str+";"
        # print(where_select_sql)
        GetSQL_where = self.db.fetchall(where_select_sql)
        return GetSQL_where
    @retry()
    def get_select_where_all(self,data,isReversed=True,keys=['URL'], *args, **kwargs):
        select_key_list=keys
        if(isReversed):
            InsertData=self.reversed_field(data=data)
            select_key_list=self.reversed_lists(field_list=select_key_list)
        else:
            InsertData=self.sequence_field(data=data)
        select_sql="SELECT * FROM `"+self.table_name+"` where "+' and '.join(f"`{col}`=%s" for col in select_key_list)+";"
        GetSQL = self.db.fetchall(select_sql,*(InsertData[key] for key in select_key_list))
        return GetSQL
    @retry()
    def insert(self,data,isReversed=True,*args, **kwargs):
        if(isReversed):
            InsertData=self.reversed_field(data=data)
        else:
            InsertData=self.sequence_field(data=data)
        data_columns = ','.join([f"`{col}`" for col in InsertData.keys()])
        insert_sql="INSERT INTO `"+self.table_name+"` ("+data_columns+")  VALUES ("+','.join(['%s'] * len(InsertData))+");"

        # print(insert_sql)
        # for i in InsertData.keys():
        #     print(InsertData[i])

        self.db.allCommit(insert_sql,*(InsertData[key] for key in InsertData.keys()))
    @retry()
    def update(self,data,isReversed=True,keys=['URL'],update_key_list=None,*args, **kwargs):
        select_key_list=keys
        if(isReversed):
            InsertData=self.reversed_field(data=data)
            select_key_list=self.reversed_lists(field_list=select_key_list)
        else:
            InsertData=self.sequence_field(data=data)
        if(update_key_list==None):
            update_key_list=list(InsertData.keys())
        update_sql="UPDATE `"+self.table_name+"` SET "+','.join(f"`{col}`=%s" for col in update_key_list)+" WHERE "+' and '.join(f"`{col}`=%s" for col in select_key_list)+";"
        self.db.allCommit(update_sql,*(InsertData[key] for key in update_key_list+select_key_list))

    @retry()
    def insert_update(self,data,keys=["URL"],isReversed=True,*args, **kwargs):
        GetSQL_data=self.get_select_where_all(data=data,keys=keys,isReversed=isReversed)
        if(len(GetSQL_data)==0):
            print("正在插入数据")
            self.insert(data=data,isReversed=isReversed)
        else:
            print("正在更新数据")
            self.update(data=data,keys=keys,isReversed=isReversed)

    def delete(self, *args, **kwargs):...
    def create_table_if_not_exists(self,comment="",*args, **kwargs):
        self.db.create_table_if_not_exists(table_name=self.table_name,comment=comment)

    def add_column_if_not_exists(self,column_name,comment,*args, **kwargs):
        self.db.add_column_if_not_exists(table_name=self.table_name,column_name=column_name,comment=comment)

    