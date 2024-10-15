from contextlib import asynccontextmanager
from prometheus_fastapi_instrumentator import Instrumentator
import socket 
from datetime import datetime, timezone, timedelta,time
from typing import List, Any
import uvicorn
import  pathlib
import logging
import sys,os
import atexit
import json
import platform
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, HTTPException, APIRouter, Request, Response, Body, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi
from fastapi.staticfiles import StaticFiles
from fn_registry import BusinessFunctionRegistry
from models import RequestMessage, ResponseMessageList
import models as models
import geo_functions as geo_functions
import pulsar_flow as pf


API_BOOT_TIME= datetime.now(timezone.utc).isoformat()[0:22]

router = APIRouter(prefix="")

logger = logging.getLogger()

models.logger = logger
crud=None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global logger 
    logger.info("Application Starting .. attempting to connect to database")
    #dsn = os.environ.get("DATABASE_DSN","postgres://admin:synergy@localhost:5432/geofencing")
    #crud = CrudNoSQL(None,logger)
    #await crud.get_database().test_connection()
    yield
    logger.info("Application Shutdown .. attempting to disconnect from database")
    #await crud.close()
    

def init_filelogging():
    format = logging.Formatter('%(asctime)s | %(levelname)-8s | %(message)s')
    logger.setLevel(logging.INFO)
    # logdir = os.environ.get("LOG_DIR","logs")
    # logFileName="{}/geofence_backend_api_{}_pid_{}.log".format(logdir,socket.gethostname(),os.getpid())
    # fileHandler = logging.handlers.RotatingFileHandler(logFileName,mode='a',maxBytes=500000000,backupCount=10)
    # fileHandler.setFormatter(format)
    #logger.addHandler(fileHandler)
    stdout=logging.StreamHandler(sys.stdout)
    stdout.setFormatter(format)
    stdout.setLevel(logging.INFO)
    logger.addHandler(stdout)

    for _log in ["uvicorn", "uvicorn.error","uvicorn.access"]:
        logging.getLogger(_log).handlers.clear()
        logging.getLogger(_log).propagate = True

def CreateApp():
    init_filelogging()
    app = FastAPI(title="Synergy geo fence System",
            version="1.0.0",
            summary="This system provide Apis for Geo Fence",
            contact={
                "name": "Pankaj Srivastava",
                "email": "psrivastava@sentineladvantage.com",
                },
            license_info={
                    "name": "Sentinel Offender Service LLC"
                },
                lifespan=lifespan
            )
    Instrumentator().instrument(app).expose(app)
    app.include_router(router)
    logger.info("Running Api Server Now...")
    logger.info('API is starting up')  
    app.mount("/ui", StaticFiles(directory="ui"), name="ui") 
    
    return app

def onExiting():
    logger.error("Existing System")
    pf.close()

atexit.register(onExiting)

           

@router.websocket("/ws")
async def pulsar_integration(websocket: WebSocket):
     pf.init(logger)
     await pf.manager.connect(websocket)
     try:
          while True:
               data = await websocket.receive_text()
               await pf.handle_webrecv(websocket,data)
     except WebSocketDisconnect:
        pf.manager.disconnect(WebSocket)

@router.get("/health")
async def health():
    return {"message": "Geofence Backend Api Running fine since {} Server Name={}".format(API_BOOT_TIME,socket.gethostname())}

@router.post("/fns/{function_name}", response_model=ResponseMessageList,
             response_model_exclude_none=True,
             response_model_exclude_unset=True)
async def handle_message(function_name:str,requestMessage:RequestMessage = Body()) -> ResponseMessageList:
        
            logger.info(f"function_name={function_name}")
            register_method=BusinessFunctionRegistry.get_method(function_name.upper())
            if register_method is None:
                raise HTTPException(status_code=400,detail=f'Method Not Found {function_name}')
            logger.info(f" request {requestMessage.model_dump()}")
            resp = await register_method(requestMessage)
            logger.info(f" response {resp.model_dump()}")
            
            return resp
        
        


if __name__ == "__main__":
    uvicorn.run(app=CreateApp(), host="0.0.0.0", port=9000,log_config=None)

