import pulsar 
import re
import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry
from .state_context import create_state_context
from datetime import datetime,timezone ,timedelta
import os 
from .models import SessionParams
import json 


class TimeoutHTTPAdapter(HTTPAdapter):
    def __init__(self, *args, **kwargs):
        if "timeout" in kwargs:
            self.timeout = kwargs["timeout"]
            del kwargs["timeout"]
        else:
            self.timeout = (5,10)  # or whatever default you want
        super().__init__(*args, **kwargs)
    
    def send(self, request, **kwargs):
        kwargs["timeout"] = self.timeout
        return super().send(request, **kwargs)
    

class FunctionBase(pulsar.Function):
        
        def __init__(self):
            pulsar.Function.__init__(self)
            self.max_redelivery_count=5
            self.next_base_url_check = None
            self.ctxinit=False
            self.session=None
            state_storage_url = os.getenv("BK_STORAGE_URL",None)
            self.config_store = create_state_context(state_storage_url,"synergy_system","loadbalancers")
             
            
        def init_session(self,context):
            self.session_config = SessionParams()
            session_config = self.config_store.get_value("session_config")
            if session_config is not None:
                self.session_config = SessionParams(**json.loads(session_config.decode()))
            context.get_logger().info("Session Config={}".format(self.session_config.model_dump()))

        def handle_config(self,context):
            if self.next_base_url_check is None or datetime.now(timezone.utc) > self.next_base_url_check:
                base_url = self.get_synsys_config(self.function_name+"_BASE_URL") 
                if base_url is None:
                    base_url = self.get_synsys_config("BUSINESS_API_BASE_URL")
                if base_url is None and self.remote_function_url is None:
                    raise Exception("Function name BUSINESS_API_BASE_URL not configured in synergy system.")
                self.next_base_url_check = datetime.now(timezone.utc) + timedelta(minutes=5)
                if base_url is not None:
                    self.remote_function_url = base_url.decode() 

        def get_synsys_config(self,key:str) -> str:
            val = self.config_store.get_value(key)
            return val 
 
        def init_ctx(self,context) -> bool:
            was_init=self.ctxinit
            if not self.ctxinit:
                self.ctxinit=True
                self.init_session(context)

            self.context = context
            return was_init
        
        def ack(self,context):
            mytopic = context.get_current_message_topic_name()
            context.ack(context.get_message_id(),mytopic)

        def canReprocess(self,context):
            mesg = context.message
            redelcnt = mesg.redelivery_count() 
            
            context.get_logger().info(f"failing message {redelcnt}")
            if mesg.redelivery_count() >= self.max_redelivery_count:
                context.get_logger().error(f"Max Redelivery Failures Exceed {redelcnt} >= {self.max_redelivery_count}")
                return False 
            return True  
        
        def failOrPass(self,context):
            if self.canReprocess(context):
                self.fail(context)
            else :
                self.ack(context)  

        def fail(self,context):
            mesg = context.message
            
            topic_consumer = None
            topic = context.get_current_message_topic_name()
            if topic in context.consumers:
                topic_consumer = context.consumers[topic]
            else:
                # if this topic is a partitioned topic
                m = re.search('(.+)-partition-(\\d+)', topic)
                if not m:
                    raise ValueError('Invalid topicname %s' % topic)
                elif m.group(1) in context.consumers:
                    topic_consumer = context.consumers[m.group(1)]
                else:
                    raise ValueError('Invalid topicname %s' % topic)
            topic_consumer.negative_acknowledge(mesg)                

        def getTopicProducer(self,topic_name,context):

            if topic_name not in context.publish_producers:
                fullyQualifiedName= "%s/%s/%s" % (context.get_function_tenant(), 
                                    context.get_function_namespace(), 
                                    context.get_function_name())
                context.get_logger().info("FQFN={}".format(fullyQualifiedName))
                producer_props={"application": "pulsar-function",
                            "id": str(fullyQualifiedName),
                            "instance_id": str(context.get_instance_id())}
                
                context.get_logger().info("properties={}".format(producer_props))
                context.publish_producers[topic_name] = context.pulsar_client.create_producer(
                                topic_name,
                                block_if_queue_full=True,
                                batching_enabled=False,
                                batching_max_publish_delay_ms=1000,
                                properties=producer_props,
                                schema=pulsar.schema.BytesSchema()
                            ) 

            return context.publish_producers[topic_name]
        
        def getStringTopicProducer(self,topic_name,context):

            if topic_name not in context.publish_producers:
                fullyQualifiedName= "%s/%s/%s" % (context.get_function_tenant(), 
                                    context.get_function_namespace(), 
                                    context.get_function_name())
                context.get_logger().info("FQFN={}".format(fullyQualifiedName))
                producer_props={"application": "pulsar-function",
                            "id": str(fullyQualifiedName),
                            "instance_id": str(context.get_instance_id())}
                
                context.get_logger().info("properties={}".format(producer_props))
                context.publish_producers[topic_name] = context.pulsar_client.create_producer(
                                topic_name,
                                block_if_queue_full=True,
                                batching_enabled=False,
                                batching_max_publish_delay_ms=1000,
                                properties=producer_props,
                                schema=pulsar.schema.StringSchema()
                            ) 

            return context.publish_producers[topic_name]
        
        def getHttpRequests(self):

            if self.session:
                return self.session
            self.session = requests.Session()
            max_retries=Retry(total=self.session_config.retry_count, 
                              backoff_factor=self.session_config.backoff_factor, allowed_methods=False,
                                status_forcelist=self.session_config.status_forcelist)
            adapter=TimeoutHTTPAdapter(timeout=(self.session_config.connect_timeout,self.session_config.read_timeout),
                                       max_retries=max_retries)
            self.session.mount("http://",adapter)
            self.session.mount("https://",adapter)
            return self.session
        
