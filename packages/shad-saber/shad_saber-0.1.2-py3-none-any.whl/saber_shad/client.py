import json, random, string, requests
from .network import Network
from .crypto import Saber

WEB_HOST = "https://shadmessenger36.iranlms.ir/"  # همان هاستی که برای وب استفاده می‌شود

class Client(Network):
    def __init__(self, auth: str | None = None):
        super().__init__(auth)
        self.net = Network(self.auth)
        self.phone = None

    def __str__(self):
        return self.auth or ""

    # ارسال کد (وب): اگر پسورد دومرحله‌ای بدهی، سرور برای همان شماره phone_code_hash جدید می‌دهد
    def send_sms(self, phone: str, pass_key: str | None = None):
        phone = self.number_formatter(phone)
        if not phone:
            return {"error": "invalid phone"}
        payload = {"phone_number": phone, "send_type": "SMS"}
        if pass_key:
            payload["pass_key"] = pass_key
        self.phone = phone
        return self.net.init("sendCode", payload, web=True)

    # لاگین ساده (API قدیمی): بدون رمز وب. برای سازگاری نگه داشته شده.
    def sign_in(self, code: str, hash_: str, phone: str | None = None):
        phone = self.number_formatter(phone) if phone else self.phone
        if not phone:
            return {"error": "invalid phone"}
        if not hash_:
            return {"error": "invalid hash"}
        payload = {"phone_code": code, "phone_code_hash": hash_, "phone_number": phone}
        resp = self.net.init("signIn", payload, web=True)
        if isinstance(resp, dict) and resp.get("status") == "OK" and resp.get("auth"):
            self.auth = resp["auth"]
            self.net.auth = self.auth
        return resp

    # لاگین وب (مطابق مثال جاوا): رمز کردن ورودی با tmp_session و ارسال به وب‌سرویس
    def sign_in_web(self, code: str, hash_: str, phone: str, tmp_session: str):
        phone = self.number_formatter(phone)
        if not phone:
            return {"error": "invalid phone"}
        if not hash_:
            return {"error": "invalid hash"}
        if not tmp_session or len(tmp_session) < 16:
            return {"error": "invalid tmp_session"}

        # همان ساختار مثال جاوا: method + input + client
        inner = {
            "method": "signIn",
            "input": {
                "phone_number": phone,
                "phone_code_hash": hash_,
                "phone_code": code
            },
            "client": {
                "app_name": "Main",
                "app_version": "3.2.3",
                "platform": "Web",
                "package": "web.shad.ir",
                "lang_code": "fa"
            }
        }
        inner_str = json.dumps(inner, ensure_ascii=False)

        # رمزکردن با کلید tmp_session (مثل Saber().d(sendRiply, txt) در جاوا)
        data_enc = Saber.encrypt_with_raw_key(inner_str, tmp_session)

        outer = {
            "api_version": "5",
            "tmp_session": tmp_session,
            "data_enc": data_enc
        }

        try:
            resp = requests.post(
                WEB_HOST,
                headers={"Content-Type": "application/json"},
                data=json.dumps(outer, ensure_ascii=False)
            )
            out = resp.json()
            # اگر سرور auth را مستقیم برگرداند، ذخیره کن
            if isinstance(out, dict) and out.get("status") == "OK" and out.get("auth"):
                self.auth = out["auth"]
                self.net.auth = self.auth
            return out
        except Exception as e:
            return {"status": False, "message": str(e)}

    def register_device(self, log_name="rub:coder95"):
        payload = {
            "app_version": "MA_3.6.5",
            "device_hash": "90EC014117A2848CC45DEC2B90BD0C4A",
            "device_model": log_name,
            "lang_code": "fa",
            "system_version": "SDK 23",
            "token": "",
            "token_type": "Firebase"
        }
        return self.net.init("registerDevice", payload)

    def get_chats(self):
        return self.net.init("getChats")

    def get_user_info(self):
        return self.net.init("getUserInfo")

    def send_message(self, guid: str, text: str):
        rnd = str(random.randint(0, 999999999)).zfill(9)
        payload = {"object_guid": guid, "rnd": rnd, "file_inline": None, "text": text}
        data_enc = Saber.encrypt_with_raw_key(json.dumps(payload, ensure_ascii=False), self.auth)
        request_body = {
            "api_version": "4",
            "auth": self.auth,
            "client": {
                "app_name": "Main",
                "app_version": "3.1.0",
                "lang_code": "fa",
                "package": "ir.medu.shad",
                "platform": "Android"
            },
            "data_enc": data_enc,
            "method": "sendMessage"
        }
        try:
            resp = requests.post(
                WEB_HOST,
                headers={"Content-Type": "application/json"},
                data=json.dumps(request_body, ensure_ascii=False)
            )
            return resp.json()
        except Exception as e:
            return {"status": False, "message": str(e)}

    def number_formatter(self, number: str):
        number = "".join(ch for ch in number if ch.isdigit())
        if number.startswith("0098"):
            number = number[2:]
        if number.startswith("0"):
            number = "98" + number[1:]
        if len(number) == 10 and number.startswith("9"):
            number = "98" + number
        if number.startswith("98") and len(number) == 12:
            return number
        return False

    def generate_auth(self, length=32):
        return "".join(random.choice(string.ascii_lowercase) for _ in range(length))