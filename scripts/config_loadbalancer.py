import state_context
from pydantic import BaseModel 
from typing import List
import json 



class SessionParams(BaseModel):
    connect_timeout:int = 3
    read_timeout:int = 60
    retry_count:int = 5
    backoff_factor: int = 10
    status_forcelist:List[int] = [429, 500, 502, 503, 504]


xcontext = state_context.create_state_context("bk://localhost:5191","synergy_system","loadbalancers")

lburl =  xcontext.get_value("BUSINESS_API_BASE_URL")

print(f"Found LB URL {lburl}")

new_lb_url = "http://192.168.55.20:9000/fns"
#new_lb_url = "http://api01:8080/fw/handle-message"

if lburl is None or lburl.decode() != new_lb_url:
   print(f"Updating the LB {new_lb_url}")
   xcontext.put("BUSINESS_API_BASE_URL",new_lb_url)

lburl =  xcontext.get_value("BUSINESS_API_BASE_URL")

print(f"Found LB URL {lburl.decode()}")

scfg = SessionParams()
print(scfg.model_dump_json())

if xcontext.get_value("session_config") is None:
    xcontext.put("session_config",scfg.model_dump_json())

sessconfig = xcontext.get_value("session_config")

print(SessionParams(**json.loads(sessconfig.decode())).model_dump())



