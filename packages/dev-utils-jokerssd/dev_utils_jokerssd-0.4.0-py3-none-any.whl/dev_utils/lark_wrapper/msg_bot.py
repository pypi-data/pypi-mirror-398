from .messege_lark import LarkRelated
from typing import Dict

class MsgBot:    
    '''
    A class for sending messages using different messaging platforms.
    Currently support Lark. from message_lark.py in LarkRelated

    Attributes:
        chat_id (str or dict): The chat ID or a dictionary of chat IDs for different platforms.
        url (str): The base URL for the messaging API.
        api_name (str): The name of the API endpoint.
        pre_text (str): Text to be prepended to the message.
        msg_type (str): The type of message to be sent (e.g., "text", "post").
        json_fp (str): File path for JSON data, if applicable.
        title (str): The title of the message, if applicable.
        msg_bot_dict (dict): A dictionary of messaging bot instances for different platforms.

    '''
    def __init__(self,chat_id="", url="",api_name="",pre_text="",msg_type="",json_fp="",title="",**kwargs):
        self.chat_id_dict = chat_id
        self.url = url
        self.api_name = api_name
        self.pre_text = pre_text
        self.msg_type = msg_type
        self.json_fp = json_fp
        self.title = title
        self.msg_bot_dict = {
            "lark" : LarkRelated(chat_id=self.chat_id_dict, url=self.url,api_name=self.api_name,
                                        pre_text=self.pre_text,msg_type=self.msg_type,title=self.title,**kwargs)
        }

    def send_msg(self,message="",chat_id="", url="",api_name="",pre_text="",msg_type="",msg_bot="lark",title="",**kwargs)->Dict:
        try:
            self.msg_bot_dict[msg_bot].send_msg(message=message,chat_id=chat_id, url=url,api_name=api_name, pre_text=pre_text,msg_type=msg_type,title=title,**kwargs)
        except Exception as err:
            print(f"Failed to send message: {err}")
            return {"success":False, "err":err}

        return {"success":True, "err":""}
    
    async def async_send_msg(self,message="",chat_id="", url="",api_name="",pre_text="",msg_type="",msg_bot="lark",title="",**kwargs)->Dict:
        try:
            self.msg_bot_dict[msg_bot].send_msg(message=message,chat_id=chat_id, url=url,api_name=api_name, pre_text=pre_text,msg_type=msg_type,title=title,is_async=True,**kwargs)
        except Exception as err:
            print(f"Failed to send message: {err}")
            return {"success":False, "err":err}

        return {"success":True, "err":""}