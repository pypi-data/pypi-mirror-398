"""
字节 AI 模型的 SDK
https://www.volcengine.com/docs/82379/1302008
也有对应的API
https://www.volcengine.com/docs/82379/1263272


key
https://console.volcengine.com/ark/region:ark+cn-beijing/apiKey?apikey=%7B%7D&projectName=undefined

模型DeepSeek-R1-Distill-Qwen-32B、DeepSeek-R1、DeepSeek-V3、DeepSeek-R1-Distill-Qwen-7B
https://console.volcengine.com/ark/region:ark+cn-beijing/openManagement?LLM=%7B%7D&OpenTokenDrawer=false&projectName=undefined

"""

from tmutils.base.download import fetch_url_with_retries
import os
from volcenginesdkarkruntime import Ark
import json
import re

class Volcengine(object):
    def __new__(cls, *args, **kwargs):
        return object.__new__(cls)
    def __init__(self,name,key,model,*args, **kwargs) -> None:
        self.name=name
        self.key=key
        self.model=model
    def __del__(self) -> None:...
    def single_round(self):
        # completion-单轮
        client = Ark(api_key=os.environ.get("api-key-20250211151839"))
        completion = client.chat.completions.create(
            model="DeepSeek-R1",
            messages=[
                {"role": "system", "content": "你是豆包，是由字节跳动开发的 AI 人工智能助手"},
                {"role": "user", "content": "常见的十字花科植物有哪些？"},
            ],
        )
        print(completion.choices[0].message.content)


    def api_v3_chat_completions(self,user_content,system_content):
        """
        https://console.volcengine.com/ark/region:ark+cn-beijing/endpoint?config=%7B%7D
        
        https://www.volcengine.com/docs/82379/1330310#582da738
        模型id
        deepseek-r1就是deepseek-r1-250120
        """

        url = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer "+self.key
        }

        data = {
            # "model": "deepseek-r1-250120",
            "model": self.model,
            # "model": "deepseek-r1-distill-qwen-32b-250120",
            "messages": [
                {"role": "system","content": system_content},
                {
                    "role": "user",
                    # "content": "123这个是负面影响吗？回答：是或者不是其他的不要输出"
                    "content": user_content
                }
                
            ]
        }

        response = fetch_url_with_retries(method="POST",url=url, headers=headers, data=json.dumps(data),timeout=(90,100))
        response_data=response.json()
        
        try:
            content_data={
                "sentiment":"",
                "confidence":"",
                "tags":"",
                "summary":"",
            }
            raw_text=response_data['choices'][0]['message']['content']
            # print(json.dumps(response_data,indent=4,ensure_ascii=False))
            if(self.model=="deepseek-r1-250120"):
                match = re.search(r'```json\n([\s\S]+?)\n```', raw_text)
                if match:
                    json_str = match.group(1)
                    # 2. 解析json字符串
                    content_data = json.loads(json_str)
                return {"content":content_data,"reasoning_content":response_data['choices'][0]['message']['reasoning_content']}
            
            else:
                content_data = json.loads(raw_text)
                return {"content":content_data}
        except Exception as e:
            return {"content":content_data}

