from typing import List,Optional
from pydantic import BaseModel,field_validator
import urllib.parse

class SessionParams(BaseModel):
    connect_timeout:int = 3
    read_timeout:int = 60
    retry_count:int = 5
    backoff_factor: int = 10
    status_forcelist:List[int] = [429, 500, 502, 503, 504]


class RequestMessage(BaseModel):
    properties: dict[str,str]
    payload: str 
    event_timestamp: Optional[int] = None 
    message_id: Optional[str] = None 
    partition_key:Optional[str] = None 
    redelivery_count: Optional[int] = 0
    topic_name: str



class ResponseMessage(BaseModel):
    properties: dict[str,str]
    payload: str
    topic_name: Optional[str] = None 
    partition_key: Optional[str] = None 
    deliver_at: Optional[int] = None 
    deliver_after: Optional[float] = None ### float selconds timedelta


class ResponseMessageList(BaseModel):
    messages: list[ResponseMessage] = []
