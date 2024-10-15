from typing import List,Optional
from pydantic import BaseModel,field_serializer, field_validator

from datetime import datetime


class SessionParams(BaseModel):
    connect_timeout:int = 3
    read_timeout:int = 60
    retry_count:int = 5
    backoff_factor: int = 10
    status_forcelist:List[str] = [429, 500, 502, 503, 504]


    
class RequestMessage(BaseModel):
  
    properties: dict[str,str]
    payload: str = None
    event_timestamp: Optional[int] = None 
    message_id: Optional[str] = None 
    partition_key:Optional[str] = None 
    redelivery_count: Optional[int] = 0
    topic_name: str

    

class ResponseMessage(BaseModel):
  
    properties: dict[str,str] = None
    payload: str
    topic_name: Optional[str] = None 
    partition_key: Optional[str] = None 
    deliver_at: Optional[int] = None 
    deliver_after: Optional[float] = None ### float selconds timedelta

    

class ResponseMessageList(BaseModel):
    messages: list[ResponseMessage] = []


class GeoRecord(dict):
    def __init__(self, *a, **k): 
        super(GeoRecord, self).__init__(*a, **k)
        self.__dict__ = self
        for k in self.__dict__:
            if isinstance(self.__dict__[k], dict):
                self.__dict__[k] = GeoRecord(self.__dict__[k])
            elif isinstance(self.__dict__[k], list):
                for i in range(len(self.__dict__[k])):
                    if isinstance(self.__dict__[k][i], dict):
                        self.__dict__[k][i] = GeoRecord(self.__dict__[k][i])
    
    

