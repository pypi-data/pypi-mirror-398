from openai import OpenAI
import os
import re
import json
import time
from datetime import datetime, timezone, timedelta
from tmutils.base.utils import alert_print_error
from tmutils.base.utils import retry


class ChatGPT(object):
    def __new__(cls, *args, **kwargs):
        return object.__new__(cls)
    def __init__(self, api_key, model="gpt-4o", *args, **kwargs) -> None:
        self.api_key = api_key
        self.client = OpenAI(api_key=self.api_key)
        self.data={"results":[]}
        self.model=model
    def __del__(self) -> None:
        """
        清理资源
        """
        try:
            self.client = None
            print("ChatGPT助手已清理资源。")
        except Exception as e:
            pass

    def select_assistant(self, name):
        existing = self.client.beta.assistants.list()
        matched = [a.id for a in existing.data if a.name == name]
        if len(matched) == 0:
            print(f"没有找到名称为{name}的助手。")
            return None
        elif len(matched) == 1:
            print(f"找到名称为{name}的助手。")
            return matched[0]
        else:
            print(f"警告：存在多个名称为{name}的助手，id分别为：{matched}")
            exit(127)
        
    def delete_assistante(self, assistant_id):
        assistant=self.client.beta.assistants.delete(assistant_id)
        print(f"助手名字是:{assistant.name},模型是:{assistant.model},id是:{assistant.id}已被删除。")

    def update_assistant(self,assistant_id,name,instructions,*args, **kwargs):
        assistant=self.client.beta.assistants.update(
            assistant_id=assistant_id,
            name=name,
            instructions=instructions,
            tools=[{"type": "file_search"}],  # 启用 File Search
            temperature = 0.3,  # 比较平衡，常用于生成内容但保持可控，温度（控制输出的“随机程度”），0.0 → 极度确定（更像查字典或 QA），1.0 → 有创造性，有变动，>1.0 → 更随机（但风险也高）
            top_p = 0.9,  # Nucleus Sampling（控制输出内容的“多样性”）， 一般用于减少极端答案，和 temperature 搭配使用,
        )
        print(f"助手名字是:{assistant.name},模型是:{assistant.model},id是:{assistant.id}已被更新。")
        return assistant

    def create_assistants(self,name,instructions,*args, **kwargs):
        assistant=self.client.beta.assistants.create(
            name=name,
            model=self.model,
            instructions=instructions,
            tools=[{"type": "file_search"}],  # 启用 File Search
            temperature = 0.3,  # 比较平衡，常用于生成内容但保持可控，温度（控制输出的“随机程度”），0.0 → 极度确定（更像查字典或 QA），1.0 → 有创造性，有变动，>1.0 → 更随机（但风险也高）
            top_p = 0.9,  # Nucleus Sampling（控制输出内容的“多样性”）， 一般用于减少极端答案，和 temperature 搭配使用
        )
        print(f"助手名字是:{assistant.name},模型是:{assistant.model},id是:{assistant.id}已被创建。")
        return assistant

    def create_update_assistants(self,name,instructions,*args, **kwargs):
        assistant_id=self.select_assistant(name)
        if(assistant_id is None):
            # 创建一个新的助手
            assistant = self.create_assistants(
                name=name,
                model=self.model,
                instructions=instructions
            )
        else:
            assistant=self.update_assistant(assistant_id,name,instructions)
        return assistant

    def vector_update_to_assistants(self, assistant_id, vector_store_ids):
        """
        将一个或多个 Vector Store 绑定到指定的 Assistant。
        :param assistant_id: str，助手的唯一 ID
        :param vector_store_ids: list[str]，要绑定的 Vector Store ID 列表
        """
        if not isinstance(vector_store_ids, list):
            raise ValueError("vector_store_ids 必须是一个列表")
        response = self.client.beta.assistants.update(
            assistant_id=assistant_id,
            tool_resources={
                "file_search": {
                    "vector_store_ids": vector_store_ids
                }
            }
        )
        print(f"已更新助手 {assistant_id}，绑定 Vector Store ID: {vector_store_ids}")
        return response

    def set_assistants_config(self,name,instructions,filepath,vector_store_name,*args, **kwargs):
        """
        设置助手的配置，包括创建向量库和助手，并将向量库绑定到助手。
        :param name: str，助手的名称
        :param instructions: str，助手的指令
        :param filepath: str，向量库文件的路径
        :param vector_store_name: str，向量库的名称
        :return: None
        """
        self.vector_json=AssistantManager(self.client).create_vector(filepath=filepath,vector_store_name=vector_store_name)
        self.assistant=self.create_update_assistants(name=name,instructions=instructions)
        # 将向量库绑定到助手
        self.vector_update_to_assistants(assistant_id=self.assistant.id, vector_store_ids=[self.vector_json['vector_store_id']])

    def run_threads_assistants(self,role_user_content,*args, **kwargs):
        self.role_user_content=role_user_content
        thread = self.client.beta.threads.create()
        self.client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=role_user_content
        )
        run = self.client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=self.assistant.id,  # 你提前创建好的 Assistant ID
        )
        max_wait_seconds = 60  # 最多等 60 秒
        poll_interval = 1
        waited = 0

        while waited < max_wait_seconds:
            run_status = self.client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )
            if run_status.status == "completed":
                break
            elif run_status.status in ["failed", "cancelled", "expired"]:
                raise Exception(f"Run failed with status: {run_status.status}")
            time.sleep(poll_interval)  # 每隔1秒查询一次
            waited += poll_interval
        else:
            raise TimeoutError(f"Run timeout after {max_wait_seconds} seconds.")
        
        messages = self.client.beta.threads.messages.list(thread_id=thread.id)
        raw_text=""
        for m in messages.data[::-1]:
            if m.role == "assistant":
                raw_text=m.content[0].text.value
                return self.text_to_json(raw_text)
        return self.data
            # print(m.role, ":", m.content[0].text.value)

    @retry(max_retries=10, delay=10)
    def ops(self,role_system_content="",role_user_content="",isApp=False,*args, **kwargs) -> dict:
        """
        OpenAI API的操作
        """

        if(role_user_content==""):
            return self.data
        # TPM 限制：每分钟最多使用 30,000 个 token。
        # Error code: 429 - Rate limit reached for gpt-4o ... on tokens per min (TPM): Limit 30000, Used 28849, Requested 2545.
        response = self.client.chat.completions.create(
            model=self.model,  # 或 "gpt-4", "gpt-3.5-turbo","gpt-4o"
            messages=[
                # {"role": "system", "content": "你是一个为黑人假发产品分析用户VOC的专家(需要根据语意进行判断)"},
                # {"role": "user", "content": "I think I should gat a big discount  I buy from u all the time love your wigs"}
                {"role": "system", "content": role_system_content},
                {"role": "user", "content": role_user_content}
            ],
            temperature = 0.3,
            top_p = 0.9,
        )
        # print(response.choices[0].message.content)
        response_data = response.model_dump()
        # json_print(response_data)
        try:
            raw_text=response_data['choices'][0]['message']['content']
            # print("raw_text is:", raw_text)
            if(isApp):
                return raw_text
            self.data=self.text_to_json(raw_text)
        except Exception as e:
            alert_print_error(e)
            return self.data

    def text_to_json(self, text,*args, **kwargs) -> dict:
        """
        将文本转换为JSON格式
        :param text: 输入的文本
        :return: 转换后的JSON对象
        """
        try:
            data = self.data
            if("```json" in text):
                match = re.search(r'```json\n([\s\S]+?)\n```', text)
                if match:
                    json_str = match.group(1)
                    # 2. 解析json字符串
                    data = json.loads(json_str)
                    return data
            else:
                # 1. 尝试直接解析为JSON
                try:
                    data = json.loads(text)
                except Exception as e:
                    alert_print_error(e)
                    print(f"尝试直接解析json失败,原文是:{self.role_user_content}")
                    print(f"这不是一个json的字符串!raw_text是:{text}")
                return data
        except Exception as e:
            alert_print_error(e)
            return data


        

class AssistantManager:
    def __init__(self, client):
        self.client = client

    def list_files(self):
        """列出当前已上传的所有文件"""
        return self.client.files.list().data

    def find_file_by_name(self, filename):
        """根据文件名查找已上传文件"""
        return [f for f in self.list_files() if f.filename == filename]

    def delete_file_by_id(self, file_id):
        """删除指定文件"""
        self.client.files.delete(file_id)
        print(f"文件已删除：{file_id}")

    def upload_file(self, filepath, purpose="assistants"):
        """上传文件"""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"找不到文件：{filepath}")

        with open(filepath, "rb") as f:
            uploaded_file = self.client.files.create(
                file=f,
                purpose=purpose
            )
        print(f"文件已上传：{uploaded_file.id} ({filepath})")
        return uploaded_file

    def ensure_file_uploaded(self, filepath, replace=True):
        """
        如果文件存在则删除（replace=True），然后重新上传。
        返回上传后的文件对象。
        """
        filename = os.path.basename(filepath)
        existing = self.find_file_by_name(filename)

        if existing:
            if replace:
                for f in existing:
                    self.delete_file_by_id(f.id)
            else:
                print(f"文件已存在，未替换：{filename}")
                return existing[0]  # 返回第一个匹配的文件

        return self.upload_file(filepath)
    

    def create_vector(self,filepath, vector_store_name):
        """
        文件检索工具 vector只能支持 .txt、.json、.pdf、.md、.html格式,csv会报错
        Error code: 400 - {'error': {'message': 'Files with extensions [.csv] are not supported for retrieval. See https://platform.openai.com/docs/assistants/tools/file-search/supported-files', 'type': 'invalid_request_error', 'param': 'file_ids', 'code': 'unsupported_file'}}
        费用：$0.1 / GB per day
        """
        expires_at = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat().replace('+00:00', 'Z')
        stores = self.client.vector_stores.list()
        for store in stores.data:
            if store.name == vector_store_name:
                self.client.vector_stores.delete(vector_store_id=store.id)



        vector_store = self.client.vector_stores.create(
            name=vector_store_name,
            metadata={
                "expires_at": expires_at
            }
        )
        print(f"向量库已创建: {vector_store.id}")
        uploaded_file = self.ensure_file_uploaded(filepath, replace=True)

        file_store_id=uploaded_file.id
        vector_store_id=vector_store.id
        print(f"文件已上传到向量库: {file_store_id} -> {vector_store_id}")
        # print(dir(self.client.vector_stores.file_batches))
        # help(self.client.vector_stores.file_batches.upload_and_poll)
        # print(inspect.signature(self.client.vector_stores.file_batches.upload_and_poll))
        self.client.vector_stores.file_batches.upload_and_poll(
            vector_store_id=vector_store_id,
            files=[],                      # 传空列表，表示不用再上传新文件
            file_ids=[file_store_id],  # 用已上传文件 ID
        )

        return {
            "file_store_id": file_store_id,
            "vector_store_id": vector_store_id,
        }

    def delete_vector(self,vector_store_id):
        self.client.vector_stores.delete(vector_store_id=vector_store_id)

