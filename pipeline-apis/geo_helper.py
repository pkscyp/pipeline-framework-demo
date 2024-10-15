import requests 
from models import GeoRecord

headers ={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
        "Accept-Encoding":"gzip, deflate, br",
        "Accept-Language":"en-US,en;q=0.9",
        "Priority":"u=0, i",
        "Sec-Ch-Ua":'"Not)A;Brand";v="99", "Brave";v="127", "Chromium";v="127"',
        "Sec-Ch-Ua-Mobile":"?0",
        "Sec-Ch-Ua-Platform":"Windows",
        "Upgrade-Insecure-Requests":"1",
        "Sec-Fetch-Dest":"document",
        "Sec-Fetch-Mode":"navigate",
        "Sec-Fetch-Site":"none",
        "Sec-Fetch-User":"?1",
        "Cookie":"_osm_totp_token=775220",
        "Dnt": "1",
        "sec-gpc":"1"
        }

def reverse(lat,lng):
    u = f"https://nominatim.openstreetmap.org/reverse.php"
    print(u)
    params = {
        "format":"jsonv2",
        "lat": lat ,
        "lon": lng ,
        "zoom": 18
    }
    headers['Referer']=f"https://nominatim.openstreetmap.org/ui/reverse.html?lat={lat}&lon={lng}&zoom=18"
    resp =  requests.get(url=u,params=params,headers=headers)
    if resp.ok :
        resp_j = resp.json()
       # print(f" address = {resp_j['display_name']}")
        return GeoRecord({'address':resp_j['display_name']})
    else:
        return None


location = reverse(40.0556793,-88.24241235)
if location:
    print(location.address)