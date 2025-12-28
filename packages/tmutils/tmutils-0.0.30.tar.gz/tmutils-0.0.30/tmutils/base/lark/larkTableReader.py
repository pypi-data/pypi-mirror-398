from tmutils.base.lark.larkOps import larkOps
from tmutils.base.lark.larkConfig import larkConfig
from tmutils.base.utils import find_first_key_value


class larkTableReader(object):
    def __init__(self, config:larkConfig ,token: str, table_id: str, view_id: str, field_map: list[str]):
        self.config = config
        self.token = token
        self.table_id = table_id
        self.view_id = view_id

        self.field_names = [item["name"] for item in field_map]
        self.field_map=field_map

    # def extract_text(self, field, key: str) -> str:
    #     """提取指定字段中的文本内容"""
    #     try:
    #         value = find_first_key_value(data=field, target_key=key)
    #         texts = find_keys(value, target_key="text")
    #         return texts[0] if texts else ""
    #     except Exception:
    #         return ""
            
    def extract_text(self,fields, field) -> str:
        """
        提取字段内容：
        - 如果 type 是 text：返回第一个元素的 "text"
        - 如果 type 是 list：返回第一个元素的 "name"
        """
        try:
            field_name = field.get("name")
            field_type = field.get("type")

            value_list = fields.get(field_name, [])

            if field_type == "text":
                first_text=find_first_key_value(data=fields,target_key="text")
                return first_text
                # return value_list[0].get("text", "")

            elif field_type == "list":
                return value_list[0].get("name", "")
            


            return ""
        except Exception as e:
            print(f"extract_text error for {fields}: {e}")
            return ""


    def get_records(self, page_size: int = 500) -> list[dict]:
        """获取所有记录，返回提取后的字段列表"""
        results = []
        page_token = None
        has_more = True
        
        # i=0
        while has_more:
            # if(i==1):break
            # i+=1
            ops_data = larkOps(config=self.config,token=self.token).multidimensional_table_query_records(
                table_id=self.table_id,
                view_id=self.view_id,
                field_names=self.field_names,
                page_token=page_token,
                page_size=page_size
            )

            data_items = ops_data.items
            has_more = ops_data.has_more
            page_token = ops_data.page_token if has_more else None

            for item in data_items:
                if not item or not hasattr(item, "fields") or not item.fields:
                    continue
                # json_print(item.fields)

                # row_data={}
                # for field in self.field_map:
                #     value = self.extract_text(item.fields, field)
                #     row_data[field] = value
                
                row_data = {
                    field["name"]: self.extract_text(item.fields, field)
                    for field in self.field_map
                }


                results.append(row_data)

        return results
