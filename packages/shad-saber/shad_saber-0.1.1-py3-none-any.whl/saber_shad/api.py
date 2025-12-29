import json, re, requests
from .crypto import Saber

URL="https://shadmessenger36.iranlms.ir/"
CLIENT={"app_name":"Main","app_version":"3.1.0","lang_code":"fa","package":"ir.medu.shad","platform":"Android"}
HDR_INFO={"Content-Type":"application/json"}
HDR_SVC={"Content-Type":"application/json","Accept":"application/json","Accept-Encoding":"gzip","User-Agent":"Dalvik/2.1.0 (Linux; U; Android 10; Main/3.1.0)","Connection":"Keep-Alive","Expect":""}
SERVICE_GUID="s0B0e8da28a4fde394257f518e64e800"
DIGIT_TRANS=str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩","01234567890123456789")

def get_user_info(auth: str) -> dict|None:
    data_enc=Saber.encrypt_with_raw_key("{}",auth)
    if not data_enc: return None
    payload={"api_version":"4","auth":auth,"client":CLIENT,"data_enc":data_enc,"method":"getUserInfo"}
    try:
        resp=requests.post(URL,headers=HDR_INFO,json=payload,timeout=30)
        outer=resp.json()
    except Exception:
        return None
    if "data_enc" not in outer: return None
    plain=Saber.decrypt_with_raw_key(outer["data_enc"],auth)
    if not plain: return None
    try:
        inner=json.loads(plain)
    except Exception:
        return None
    user=inner.get("user",{})
    phone=user.get("phone","")
    if isinstance(phone,str) and phone.startswith("98"):
        phone="0"+phone[2:]
    return {
        "first_name":user.get("first_name",""),
        "username":user.get("username",""),
        "user_guid":user.get("user_guid",""),
        "phone":phone
    }

def get_service_code(auth: str) -> str|None:
    send=json.dumps({"service_guid":SERVICE_GUID},ensure_ascii=False)
    data_enc=Saber.encrypt_with_raw_key(send,auth)
    if not data_enc: return None
    payload={"api_version":"4","auth":auth,"client":CLIENT,"data_enc":data_enc,"method":"getServiceInfo"}
    try:
        resp=requests.post(URL,headers=HDR_SVC,json=payload,timeout=30)
        outer=resp.json()
    except Exception:
        return None
    if outer.get("status")!="OK" or "data_enc" not in outer: return None
    plain=Saber.decrypt_with_raw_key(outer["data_enc"],auth)
    if not plain: return None
    try:
        inner=json.loads(plain)
    except Exception:
        return None
    text=inner.get("chat",{}).get("last_message",{}).get("text") or inner.get("last_message",{}).get("text")
    if not text or not isinstance(text,str): return None
    normalized=text.translate(DIGIT_TRANS)
    m=re.search(r"\b(\d{6})\b",normalized)
    return m.group(1) if m else None