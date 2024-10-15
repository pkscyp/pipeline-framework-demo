import pulsar
import uuid
from datetime import datetime
import json 

client = pulsar.Client('pulsar://localhost:6650')

producer = client.create_producer('persistent://public/default/receiveLatLng')

msg = {"latitude":40.0556793,"longitude":-88.24241235} 
props = {'id':str(uuid.uuid4())}
msg = producer.send(json.dumps(msg).encode(),
                    properties = props,
              partition_key=str(uuid.uuid4()),
              event_timestamp=int(datetime.now().timestamp()*1000)
              )
print(msg)

producer.close()
client.close()

