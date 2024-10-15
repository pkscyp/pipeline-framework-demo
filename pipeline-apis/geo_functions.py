from fastapi import HTTPException
from fn_registry import BusinessFunctionRegistry
from models import GeoRecord, RequestMessage, ResponseMessage,ResponseMessageList
import json 
from datetime import datetime,timezone
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder 
from geopy.distance import geodesic
import geo_helper as gh

logger=None

GA_OFFICE=GeoRecord({'latitude':34.02380132352102,'longitude':-84.3280086040738})
SA_OFFICE = GeoRecord({'latitude':33.855072988066524,'longitude':-117.8612710040817})



USER_AGENT='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.3'

@BusinessFunctionRegistry.register()
async def receiveLatLng(request_message:RequestMessage) -> ResponseMessageList:
    gr = GeoRecord(json.loads(request_message.payload))
    if not ('latitude' in gr  or  'longitude' in gr ) :
         logger.info(" Invalid geo cordinates")
         return ResponseMessageList(messages=[])
    gr.geo_coord_valid = True
    props = request_message.properties
    props['function-name']='receiveLatLng'
    msg=ResponseMessage(properties=props,
                            payload=json.dumps(gr),
                            partition_key=request_message.partition_key
                        )
    return ResponseMessageList(messages=[msg])


@BusinessFunctionRegistry.register()
async def findAddress(request_message:RequestMessage) -> ResponseMessageList:
        gr = GeoRecord(json.loads(request_message.payload))
        geolocator = Nominatim(user_agent=USER_AGENT)
        location = gh.reverse(lat=gr.latitude,lng=gr.longitude)
        gr.address =  location.address if location else 'Address Not Found'
        props = request_message.properties
        props['function-name']='findAddress'
        msg = ResponseMessage(properties=props,
                              payload=json.dumps(gr),
                            partition_key=request_message.partition_key
                              )
       
        return ResponseMessageList(messages=[msg])

@BusinessFunctionRegistry.register()
async def findTimezone(request_message:RequestMessage) -> ResponseMessageList:
    gr = GeoRecord(json.loads(request_message.payload))
    tzfinder = TimezoneFinder() 
    tz = tzfinder.timezone_at(lng=gr.longitude, lat=gr.latitude)
    gr.timezone = tz if tz else 'Unknown'
    props = request_message.properties
    props['function-name']='findTimezone'
    msg=ResponseMessage(properties=props,
                            payload=json.dumps(gr),
                            partition_key=request_message.partition_key
                            )
    return ResponseMessageList(messages=[msg])


@BusinessFunctionRegistry.register()
async def findDistance(request_message:RequestMessage) -> ResponseMessageList:
    gr = GeoRecord(json.loads(request_message.payload))
    ga_dist = geodesic((GA_OFFICE.latitude,GA_OFFICE.longitude),(gr.latitude,gr.longitude)).miles 
    gr.distance_from_ga_office = ga_dist if ga_dist else -1
    sa_dist = geodesic((SA_OFFICE.latitude,SA_OFFICE.longitude),(gr.latitude,gr.longitude)).miles 
    gr.distance_from_aa_office = sa_dist if sa_dist else -1
    props = request_message.properties
    props['function-name']='findDistance'
    msg=ResponseMessage(properties=props,
                            payload=json.dumps(gr),
                            partition_key=request_message.partition_key
                            )
    return ResponseMessageList(messages=[msg])

