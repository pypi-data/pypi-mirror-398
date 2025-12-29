import json, requests
from .crypto import Saber

class Network(Saber):
    def __init__(self, auth: str|None=None):
        self.auth = auth or "inkexmexhgqtgtfaluvzpcvbzadnlsbm"
        self.enc = Saber()
        self.base_url = "https://shadmessenger38.iranlms.ir/"
        self.cli_web = {
            "app_name":"Main","app_version":"3.2.3","platform":"Web",
            "package":"web.shad.ir","lang_code":"fa"
        }
        self.cli_and = {
            "app_name":"Main","app_version":"3.6.5","lang_code":"fa",
            "package":"ir.medu.shad","platform":"Android"
        }
        self.headers = {
            "accept":"application/json, text/plain, */*",
            "accept-language":"en-US,en;q=0.9,fa;q=0.8",
            "content-type":"text/plain",
            "referer":"https://web.shad.ir/",
            "user-agent":"Mozilla/5.0"
        }

    def init(self, method: str, input_data: dict|None=None, web: bool=False):
        input_data = input_data or {}
        if web:
            config = {"method":method,"input":input_data,"client":self.cli_web}
        else:
            config = input_data
        data_enc = self.enc.encrypt_with_raw_key(json.dumps(config,ensure_ascii=False), self.auth)
        return self.post(data_enc, method, web)

    def post(self, data_enc: str, method: str, web: bool=False):
        auth_type = "tmp_session" if method in ["sendCode","signIn"] else "auth"
        if web:
            data = {"api_version":"5",auth_type:self.auth,"data_enc":data_enc}
        else:
            data = {"api_version":"4","auth":self.auth,"client":self.cli_and,
                    "data_enc":data_enc,"method":method}
        try:
            resp = requests.post(self.base_url, headers=self.headers, json=data, timeout=30)
            res = resp.json()
        except Exception as e:
            return {"error":str(e)}
        if not res or "data_enc" not in res:
            return res
        plain = self.enc.decrypt_with_raw_key(res["data_enc"], self.auth)
        try:
            return json.loads(plain)
        except Exception:
            return res