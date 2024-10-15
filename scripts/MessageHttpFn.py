from typing import List
import pulsar 
from synergypy import FunctionBase
from datetime import datetime, timedelta, timezone
import json 
import synergypy as req_resp
import base64
import urllib.parse
import uuid

class HandleMessageByHttp(FunctionBase):

    def __init__(self):
        self.next_base_url_check = None
        FunctionBase.__init__(self)
        self.remote_function_url=None
        self.REMOTE_FUNCTION_BASE_URL="REMOTE_FUNCTION_BASE_URL"
        pass 

    

    
    def process(self,input,context):
        context.get_logger().info("Message Received")
        
        
        if not self.init_ctx(context):

            self.function_name =  self.context.get_function_name()
            

            self.output_topic = context.get_output_topic()
            if not self.output_topic:
                raise Exception("output topic for function is not configured")
            

        
        logger = self.logger = context.get_logger()

        # if not message ack and completed
        if  context.message is None or input is None :
            logger.warn("context current record message is not present.")
            self.ack(context)
            return None
        
        msg_id = context.get_message_id()
        mesg = context.message
        logger.info("Processing msgid={}".format(msg_id))
        message_key = context.get_partition_key()
        message_key = None if message_key == "" else message_key
        props = context.get_message_properties()
        self.handle_config(context)
        post_url = f"{self.remote_function_url}/{self.function_name}"
        logger.info("post_url={} data={}".format(post_url,mesg.value()))
        request_message = req_resp.RequestMessage(properties=props,
                                                  topic_name=mesg.topic_name(),
                                                  payload=mesg.value(),
                                                  partition_key=message_key)
        
        request_message.message_id = str(msg_id) 
        request_message.event_timestamp = mesg.event_timestamp()
        request_message.redelivery_count = mesg.redelivery_count()

        httpsession = self.getHttpRequests()
        try:
            logger.info(f" payload is {request_message.model_dump()}")
            response = httpsession.post(post_url,json=request_message.model_dump())
            response.raise_for_status()
            if response.status_code != 201:  
                response_json = response.json()
                response_messages:req_resp.ResponseMessageList = req_resp.ResponseMessageList(**response_json)
               
            for message in response_messages.messages:
                output_topic = message.topic_name or self.output_topic
                out_payload = message.payload
                out_mesg_key = message.partition_key if message.partition_key else None  

                producer = self.getStringTopicProducer(output_topic,context)
                out_msg_id = producer.send(out_payload,
                            properties=message.properties,
                            partition_key=out_mesg_key,
                            event_timestamp=int(datetime.now(timezone.utc).timestamp()*1000),
                            deliver_at = message.deliver_at if not message.deliver_at else None ,
                            deliver_after =  timedelta(seconds=message.deliver_after) 
                                                    if message.deliver_at is None and message.deliver_after is not None else None 
                            ) 
                self.logger.info(f"send record {out_msg_id} {output_topic}")
            
            self.ack(context)
        except Exception as ex:
            logger.error(ex)
            self.failOrPass(context)
        
        return None 
    

class HandleStrMessageByHttp(FunctionBase):
    def __init__(self):
        super().__init__()
        self.next_base_url_check = None
        FunctionBase.__init__(self)

    def process(self,input,context):
        logger = context.get_logger()

        logger.info(f"Message Received {input} ")
        logger.info(f"Message Received {context.get_current_message_topic_name()} ")
        logger.info(f"Message class type is {type(input)}")
        self.ack(context)