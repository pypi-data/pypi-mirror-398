
from openai import OpenAI
from pathlib import Path
import requests
import json
import time

class Kimi:
    def __init__(self,api_key) -> None:
        self.API_KEY = api_key
        self.URL = "https://api.moonshot.cn/v1"
        self.MODEL =  'moonshot-v1-8k'  #"moonshot-v1-32k"
        self.MODEL128 = 'moonshot-v1-128k'
    
    def getClient(self) -> OpenAI:
        clientInstance = OpenAI(
            api_key=self.API_KEY,
            base_url=self.URL,
        )
        return clientInstance
    
    def getModel(self):
        models = []
        client = self.getClient()
        model_list = client.models.list()
        model_data = model_list.data
        for i, model in enumerate(model_data):
            models.append(model.id)
        client.close()
        return models
       
    def sendSingleMenssage(self,message):
        client = self.getClient()
        completion = client.chat.completions.create(
                model= self.MODEL,
                messages=[
                    # {"role": "system", "content": "你是 Kimi，由 Moonshot AI 提供的人工智能助手，你更擅长中文和英文的对话。你会为用户提供安全，有帮助，准确的回答。同时，你会拒绝一切涉及恐怖主义，种族歧视，黄色暴力等问题的回答。Moonshot AI 为专有名词，不可翻译成其他语言。"},
                    {"role": "user", "content":message}
                            ],
                temperature=0.3,
            )
        returnMessage = completion.choices[0].message.content
        client.close()
        returnList = returnMessage.split('\n')
        return returnList
    
    def sendSingleMessageStream(self,message):
        client = self.getClient()
        response = client.chat.completions.create(
            model=self.MODEL,
            messages=[
                # {
                #     "role": "system", "content": "你是 Kimi，由 Moonshot AI 提供的人工智能助手，你更擅长中文和英文的对话。你会为用户提供安全，有帮助，准确的回答。同时，你会拒绝一切涉及恐怖主义，种族歧视，黄色暴力等问题的回答。Moonshot AI 为专有名词，不可翻译成其他语言。",
                # },
                {"role": "user", "content": message},
            ],
            temperature=0.3,
            stream=True,
        )
        collected_messages = []
        for idx, chunk in enumerate(response):
            # print("Chunk received, value: ", chunk)
            chunk_message = chunk.choices[0].delta
            if not chunk_message.content:
                continue
            collected_messages.append(chunk_message)  # save the message
        client.close()
        return collected_messages
        
    
    def putFile(self,fileName)->str:
        client = self.getClient()
        file_object = client.files.create(file=Path(fileName), purpose="file-extract")
        client.close()
        return file_object.id
        
    def getFile(self,fileId,fileName)->None:
        client = self.getClient()
        fileobject = client.files.content(file_id=fileId)
        # fileobject.write_to_file(fileName)
        contentsJsonString = fileobject.text
        contents = json.loads(contentsJsonString).get('content')
        print(contents)
        
        with open(fileName,'w',encoding='UTF-8') as f:
            f.write(contents)
        client.close()
        
    def delFile(self,fileId)->None:
        client = self.getClient()
        client.files.delete(file_id=fileId)
        client.close()
    
    def delFileAll(self)->None:
        flist = self.listFile()
        cnt = 0 
        client = self.getClient()
        for fil in flist:
            if cnt > 0:
                time.sleep(10)
            client.files.delete(file_id=fil.get('fileid'))
            cnt += 1
            
        client.close()
    
    
    def listFile(self)->list:
        resultList = []
        client = self.getClient()
        file_list = client.files.list()
        for file in file_list.data:
            result = {}
            result = {
                'fileid': file.id ,
                'filename':file.filename
            }
            resultList.append(result)
            print(file) # 查看每个文件的信息
        client.close()
        return resultList
            
    def sendFileAndMenssage(self,fileName,message):
        # "请简单介绍 xlnet.pdf 讲了啥"
        # file_list = client.files.list()
        # file in file_list.data:
        #     print(file) # 查看每个文件的信息
    
        client = self.getClient()
        # xlnet.pdf 是一个示例文件, 我们支持 pdf, doc 以及图片等格式, 对于图片和 pdf 文件，提供 ocr 相关能力
        file_object = client.files.create(file=Path(fileName), purpose="file-extract")
        
        # print(file_object)
        # id='co55jkalnl9coc940kp0'
        # 获取结果
        file_content = client.files.content(file_id=file_object.id).text
        
        
        # 把它放进请求中
        messages=[
            # {
            #     "role": "system",
            #     "content": "你是 Kimi，由 Moonshot AI 提供的人工智能助手，你更擅长中文和英文的对话。你会为用户提供安全，有帮助，准确的回答。同时，你会拒绝一切涉及恐怖主义，种族歧视，黄色暴力等问题的回答。Moonshot AI 为专有名词，不可翻译成其他语言。",
            # },
            {
                "role": "system",
                "content": file_content,
            },
            {"role": "user", "content": message},
        ]
        # 删除文件
        client.files.delete(file_id=file_object.id)
        
        
        # 然后调用 chat-completion, 获取 kimi 的回答
        completion = client.chat.completions.create(
            model= self.MODEL128,
            messages=messages,
            temperature=0.3,
        )
        returnMessage = completion.choices[0].message.content
        client.close()
        returnList = returnMessage.split('\n')
        return returnList

class WenXinYiYan:
    #直接进千帆控制台页面： https://console.bce.baidu.com/qianfan/overview  
    # 选择右侧边栏的应用接入，再点击创建应用就可以申请一个api了
    # 创建过程中只需要填写当前api的名称以及描述，默认所有服务都是勾选的（对api的使用没有任何影响）
    # 创建成功后会返回到应用接入的界面，记录下此时AppID、API Key、Secret Key
    # 点击控制台右上角的计费管理开通服务
    def __init__(self,api_key,secret_key) -> None:
            self.API_KEY = api_key
            self.SECRET_KEY = secret_key
            self.URL = "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/eb-instant?access_token=" + self.getAccessToken()
            
    def getAccessToken(self):
        """
        使用 AK，SK 生成鉴权签名（Access Token）
        :return: access_token，或是None(如果错误)
        """
        url = "https://aip.baidubce.com/oauth/2.0/token"
        params = {"grant_type": "client_credentials", "client_id": self.API_KEY, "client_secret": self.SECRET_KEY}
        return str(requests.post(url, params=params).json().get("access_token"))

    def sendSingleMenssage(self,message):
        payload = json.dumps({
        "messages": [
            {
                "role": "user",
                "content": message
            }
        ]
        })
        
        headers = {
            'Content-Type': 'application/json'
        }
        res = requests.request("POST", self.URL, headers=headers, data=payload).json()
        returnList =  res['result'].split('\n')
        return returnList
