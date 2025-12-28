from tmutils.base.db.Mysql8PoolOps import Mysql8PoolOps
from tmutils.base.db.Mysql8Config import Mysql8Config

class TableValidator(object):
    """
    校验并创建表结构
    """
    def __new__(cls, *args, **kwargs):
        return object.__new__(cls)
    def __init__(self,config:Mysql8Config,*args, **kwargs) -> None:
        self.config = config
    def create_and_update_table(self,table_name,comment,columns,if_create_table_columns=True,*args, **kwargs):
        if(if_create_table_columns):
            Mysql8PoolOps(config=self.config,table_name=table_name).create_table_if_not_exists(comment=comment)
            self.columns=columns
            # 检查重复
            dup_col = [x for x in set([c["column_name"] for c in self.columns]) if sum(d["column_name"] == x for d in self.columns) > 1]
            dup_com = [x for x in set([c["comment"] for c in self.columns]) if sum(d["comment"] == x for d in self.columns) > 1]
            if dup_col or dup_com:
                if dup_col: print("重复的 column_name:", dup_col)
                if dup_com: print("重复的 comment:", dup_com)
                exit(127)
            else:
                for column in self.columns:
                    Mysql8PoolOps(config=self.config,table_name=table_name).add_column_if_not_exists(column_name=column['column_name'],comment=column['comment'])

