import datetime as dt
import hashlib
import base64
import hmac
import json


class Logger:
    PURPLE = '\033[95m'
    ORANGE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

    def __init__(self, name, enabled):
        self.name = name
        self.enabled = enabled

    @staticmethod
    def _time():
        return dt.datetime.now().strftime('%m/%d/%Y - %I:%M:%S %p')


    def info(self, s):
        self._log(Logger.YELLOW, f'[-] {s}')

    def success(self, s):
        self._log(Logger.GREEN, f'[+] {s}')

    def error(self, s):
        self._log(Logger.RED, f'[!] {s}')


    def _log(self, clr, s):
        if self.enabled: 
            print(f"[{Logger._time()}] - {self.name} - {clr}{s}{Logger.ENDC}")



def verify_sig(signed_payload, client_secret):
    if not signed_payload: return {}

    encoded_json, encoded_hmac = signed_payload.split('.')

    dc_json = base64.b64decode(encoded_json)
    signature = base64.b64decode(encoded_hmac)

    expected_sig = hmac.new(client_secret.encode(), base64.b64decode(encoded_json), hashlib.sha256).hexdigest()
    authorized = hmac.compare_digest(signature, expected_sig.encode())

    return json.loads(dc_json.decode()) if authorized else {}
