import json
import requests
import traceback

class FeiShu(object):
    def __new__(cls, *args, **kwargs):
        # 调用父类的（object）的new方法，返回一个Ansible实例，这个实例传递给init的self参数
        return object.__new__(cls)
    def __init__(self,*args, **kwargs) -> None:
        self.dingtalk_url="https://open.feishu.cn/open-apis/bot/v2/hook/"
        self.dingtalkHeaders={"Content-Type": "application/json"}
        self.timeout=10

    def __del__(self) -> None:...
    def send(self,key,content,*args, **kwargs) -> None:
        try:
            self.data_dict={
                "msg_type": "interactive",
                "card": {
                    "elements":[
                        {
                            "tag": "div",
                            "text": {
                                "tag": "lark_md",
                                "content": content
                            }
                        }
                    ]
                }
            }
            self.send_data = json.dumps(self.data_dict).encode('utf-8')
            requests.request(method="POST",url=self.dingtalk_url+key,timeout=self.timeout,headers=self.dingtalkHeaders,data=self.send_data)
        except Exception as e:
            error_message = traceback.format_exc()
            content="错误日志--->报错如下:\n"+str(e)+"\n报错栈如下:\n"+str(error_message)
            print(content)