import requests
import asyncio
from typing import Dict,List
import json


def escape_special_characters(input_data):
    # Convert the input data to a JSON string
    return json.dumps(input_data)
    # Escape special characters
    # escaped_str = json_str.replace('\\', '\\\\').replace('\'', '\\\'').replace('\"', '\\"')

class LarkRelated:
    def __init__(self,chat_id="", url="",api_name="",pre_text="",msg_type="",title='',is_async=False,**kwargs):
        self.is_async = is_async
        self.chat_id = chat_id
        self.url = url
        self.api_name = api_name
        self.pre_text = pre_text
        self.msg_type = msg_type
        self.title = title

    def get_params(self,**kwargs):
        ''''''
        output={}
        for key,val in kwargs.items():
            if val or val == 0:
                output[key] = val
                continue
            output[key] = getattr(self,key)
        return output

    def get_msg_format(self,message,msg_type="text",pre_text="",more_content:List[Dict[str,str]]=None,**kwargs):
        '''
        more content format
        https://open.larksuite.com/document/server-docs/im-v1/message-content-description/create_json?lang=en-US
        [
            {
                "tag": "at",
                "user_id": "ou_1avnmsbv3k45jnk34j5",
                "style": ["lineThrough"]
            },
        ]
        '''
        if msg_type=="text":
            if pre_text:
                message=pre_text+"\n"+message
            return {
                "msg_type": "text",
                "content":{
                    "text":message
                }
        }

        if msg_type == "post":
            language = kwargs.get("language","en_us")
            title = kwargs.get("title","")

            # get the rtf content
            rtf_content = self.get_rtf_content(message,pre_text=pre_text,more_content=more_content,title=title,language=language)
            rtf_content = escape_special_characters(rtf_content)

            # setting up the json for rtf
            rtf_json = self.get_rtf_json(rtf_content)

            return rtf_json

    def get_rtf_content(self,message,pre_text="",more_content:List[Dict[str,str]]=None,title="",language="en_us"):
        '''create the rtf content for the message'''
        msg = pre_text + message
        rtf_content = [[{"tag": "text", "text": msg}]] if msg else []
        if more_content:
            rtf_content += more_content

        rtf_content =  {
                "post": {
                    f"{language}" : {
                        "content": rtf_content
                        }
                }
            }
        if title:
            rtf_content["post"][f"{language}"]["title"] = title
        return rtf_content

    def get_rtf_json(self,rtf_content):
        '''get the rtf json for the message
        {
            "msg_type": "post",
            "content": {
                "post": {
                    "en_us": {
                        "title": "test title",
                        "content": [
                            [
                                {
                                    "tag": "text",
                                    "text": "TEST MESSEGE"
                                }
                            ],
                            [
                                {
                                    "tag": "at",
                                    "user_id": "all"
                                }
                            ]
                        ]
                    }
                }
            }
        }
        '''
        rtf_json = {
            "msg_type": "post",
            "content" : rtf_content
        }
        return rtf_json

    def _send_msg(self,message,chat_id="", url="",api_name="",pre_text="",msg_type="",**kwargs):
        input_params = self.get_params(chat_id=chat_id,msg_type=msg_type,
                                       url=url,api_name=api_name,pre_text=pre_text)
        # headers = {"Content-Tpye": "application/json"}
        headers = {"Content-Type": "application/json"}
        url = f"{input_params['url']}/{input_params['api_name']}/{input_params['chat_id']}"
        params = self.get_msg_format(message,input_params['msg_type'],input_params['pre_text'],**kwargs)
        response = requests.post(url=url, json=params, headers=headers,timeout=5)
        return response.json()

    # TODO: change to a decorator
    def send_msg(self,message="",chat_id="", url="",api_name="",pre_text="",msg_type="",title="",**kwargs):
        chat_id = self.chat_id if not chat_id else chat_id
        url = self.url if not url else url
        api_name = self.api_name if not api_name else api_name
        msg_type = self.msg_type if not msg_type else msg_type

        if kwargs:
            try:
                pre_text = (self.pre_text if not pre_text else pre_text or "").format(**kwargs)
            except KeyError:
                pre_text = (self.pre_text if not pre_text else pre_text or "")
            try:
                title = (self.title if not title else title or "").format(**kwargs)
            except KeyError:
                title = (self.title if not title else title or "")
        
        
        is_async = kwargs.get("is_async", self.is_async)
        if not is_async:
            return self._send_msg(message,chat_id=chat_id, url=url,api_name=api_name,pre_text=pre_text,msg_type=msg_type,title=title,**kwargs)
        asyncio.create_task(self._send_msg(message, chat_id=chat_id, url=url, api_name=api_name, pre_text=pre_text, msg_type=msg_type,title=title,**kwargs))

if __name__=="__main__":
    alert_chat_id: str = "333a6d49-8c8d-443d-b856-e1ac8fb6dbef"  # chat id to post msg in
    alert_api_name: str = "bot/v2/hook/"  # api function to use, remotebot for autoreply
    alert_url: str = "https://open.larksuite.com/open-apis/"  # url for the worktile api
    alert_pretext: str = "自动平仓机制"  # the title
    alert_msg_type: str = "post"  # msg format, text or
    alert_msg_bot = LarkRelated(chat_id=alert_chat_id, url=alert_url,api_name=alert_api_name,msg_type=alert_msg_type,title="test title")
    alert_msg_bot.send_msg(more_content = [[{'tag':"text",'text':"Start running auto_flatten for fundingrate strategy ...\n"}],[{'tag':"at",'user_id':'all'}]  ])