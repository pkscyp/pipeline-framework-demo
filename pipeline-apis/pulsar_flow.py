import pulsar
import uuid
from datetime import datetime
import json 
from fastapi import WebSocket
import asyncio

client=None 
producer=None 
consumer=None 
logger = None 
init_done=False

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        try:
            await websocket.accept()
            self.active_connections.append(websocket)
        except Exception as ex:
            logger.error("Error ",ex)
    

    def disconnect(self, websocket: WebSocket):
        try:
            self.active_connections.remove(websocket)
        except Exception as ex:
            logger.error("Error ",ex)
            pass

    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except Exception as ex:
            logger.error("Error ",ex)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as ex:
                logger.error("Error ",ex)

manager = ConnectionManager()

def handle_message(consumer, message):
    asyncio.run(handle_message_async(consumer,message))

async def handle_message_async(consumer, message):
    try:
        await manager.broadcast(message.value())
        consumer.acknowledge(message)
    except Exception as ex:
        logger.error("Error",ex)

def init(_logger):
    global logger 
    global producer
    global consumer 
    global client 
    global init_done
    if not init_done:
        logger = _logger
        client = pulsar.Client('pulsar://localhost:6650')
        consumer = client.subscribe(topic='persistent://public/default/finalout', 
                                    subscription_name='py-backend',
                                    message_listener=handle_message,
                                    initial_position=pulsar.InitialPosition.Earliest,
                                    schema=pulsar.schema.StringSchema())
        
        producer = client.create_producer('persistent://public/default/receiveLatLng',schema=pulsar.schema.StringSchema()) 
        init_done=True

def close():
    global logger 
    global producer
    global consumer 
    global client 
    global init_done
    if init_done:
        if producer:
            producer.close()
        if client:
            client.close()
        if consumer:
            consumer.close()
        init_done=False

async def handle_webrecv(websocket:WebSocket,data:str):
    # send data to pulsar
    id = str(uuid.uuid4())
    jstr = json.loads(data)
    jstr['id'] = id 
    props = {'id':id}
    payload = json.dumps(jstr)
    msg  = producer.send(payload,
              properties = props,
              partition_key=id,
              event_timestamp=int(datetime.now().timestamp()*1000)
              )
    resp = f"Send For Processing payload={payload} pulsar_msg_id={msg}"
    await manager.send_personal_message(resp,websocket)
    logger.info(resp)

