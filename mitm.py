import sys
sys.dont_write_bytecode = True
from mitmproxy import http
from mitmproxy.tools.main import mitmdump
from urllib.parse import parse_qs, urlparse
import re
import requests
from bs4 import BeautifulSoup
import threading
import os

# Thread-safe storage untuk ID
current_userid_lock = threading.Lock()
current_userid = ""

FILTER_PATH = "/data/handleMsg.do"
SIMPLE_LOG = True

# Callback server URL (default: localhost, bisa diubah untuk production)
CALLBACK_URL = os.getenv('CALLBACK_URL', 'http://localhost:5000/api/v1/callback')

# ANSI Color Codes
BLUE, GREEN, RED, RESET = "\033[94m", "\033[92m", "\033[91m", "\033[0m"

# Error messages dalam format hex
ERROR_MESSAGES = {
    "4B6174612073616E6469": "Security password error",
    "4A756D6C6168206B6573616C6168616E": "Security password error",
    "50656E6767756E6120696E6920746964616B20616461": "Account not found",
    "416B756E2074656C61682064696861707573": "Account deleted",
    "416B756E20416E64612074656C6168206469626C6F6B6972": "Account blocked",
    "4F746F726973617369": "Authorization expired",
    "7665726966696B617369": "Account verified",
    "5665727369207465726C616C752072656E646168": "Version to low",
    "416E6461207465726C616C7520736572696E67206C6F67696E": "To many login",
}


def _parse_little_endian_hex(hex_str: str, start_pos: int = 0) -> str:
    """Parse 8 karakter hex (4 bytes) dari posisi start_pos sebagai little endian integer."""
    try:
        if start_pos + 8 > len(hex_str):
            return ""
        userid_hex = hex_str[start_pos:start_pos+8]
        userid_bytes = bytes.fromhex(userid_hex)
        return str(int.from_bytes(userid_bytes, byteorder='little'))
    except (ValueError, TypeError):
        return ""


def _check_error_in_response(body: str) -> tuple[str, str] | None:
    body_upper = body.upper()
    for error_hex, error_name in ERROR_MESSAGES.items():
        if error_hex.upper() in body_upper:
            return (error_hex, error_name)
    return None


def _parse_token_from_80chars(body: str) -> tuple[str, str]:
    stripped = body.lstrip('0')
    userid = _parse_little_endian_hex(stripped, 0) if len(stripped) >= 8 else ""
    decoded = ""
    for i in range(0, len(body)-1, 2):
        try:
            byte_val = int(body[i:i+2], 16)
            decoded += chr(byte_val) if 32 <= byte_val <= 126 else '.'
        except (ValueError, IndexError):
            continue
    matches = re.findall(r'[a-zA-Z0-9]+', decoded)
    token = max(matches, key=len) if matches else ""
    return (token, userid)


def _format_chip(money_str: str) -> str:
    try:
        money = int(money_str)
        for unit, divisor in [("T", 1_000_000_000_000), ("B", 1_000_000_000), 
                              ("M", 1_000_000), ("K", 1_000)]:
            if money >= divisor:
                return f"{money / divisor:.2f}{unit}"
        return str(money)
    except (ValueError, TypeError):
        return money_str


def _fetch_money_from_exchange(userid: str, token: str) -> str:
    try:
        url = f"https://www.toptoplink.com/exchange/index?userId={userid}&userToken={token}"
        html = requests.get(url, timeout=5).text
        for script in BeautifulSoup(html, 'html.parser').find_all('script', type='text/javascript'):
            if script.string and 'ShopExchangeData' in script.string:
                match = re.search(r'money\s*:\s*(\d+)', script.string)
                if match:
                    return match.group(1)
    except Exception:
        pass
    return ""


def _send_callback_to_server(userid: str, status: str, chip: str = "", error: str = ""):
    """Mengirim callback ke server.py (non-blocking)"""
    def _send():
        try:
            callback_data = {
                'status': status,
                'userId': userid
            }
            if chip:
                callback_data['chip'] = chip
            if error:
                callback_data['error'] = error
            
            requests.post(CALLBACK_URL, json=callback_data, timeout=1)
        except Exception:
            pass  # Ignore errors jika server tidak tersedia
    
    # Jalankan di background thread agar tidak blocking
    threading.Thread(target=_send, daemon=True).start()


def _fetch_money_in_background(userid: str, token: str):
    if userid and token:
        money = _fetch_money_from_exchange(userid, token)
        if money:
            chip_formatted = _format_chip(money)
            print(f"{GREEN}[LOGIN SUCCESS] {userid} | {chip_formatted}{RESET}")
            _send_callback_to_server(userid, 'login_success', chip=chip_formatted)


class FilterPath:
    def request(self, flow: http.HTTPFlow):
        if FILTER_PATH in flow.request.path and not SIMPLE_LOG:
            query_params = parse_qs(urlparse(flow.request.pretty_url).query)
            v_length = len(query_params.get('v', [''])[0])
            print(f"{BLUE}[REQUEST] [{flow.request.method}] {flow.request.path} | v={v_length} chars{RESET}")

    def response(self, flow: http.HTTPFlow):
        global current_userid
        
        if FILTER_PATH not in flow.request.path:
            return
        
        parsed = urlparse(flow.request.pretty_url)
        query_params = parse_qs(parsed.query)
        v_value = query_params.get('v', [''])[0]
        v_length = len(v_value)
        
        # Extract userid dari v=616 di awal (posisi 216-223)
        if v_length == 616:
            userid_from_v = _parse_little_endian_hex(v_value, 216)
            if userid_from_v:
                with current_userid_lock:
                    current_userid = userid_from_v
                if not SIMPLE_LOG:
                    extracted_hex = v_value[216:224] if len(v_value) >= 224 else ""
                    print(f"{GREEN}[USERID EXTRACTED] v={v_length} chars | hex={extracted_hex} | userId={userid_from_v}{RESET}")
        
        body = flow.response.content.decode('utf-8', errors='ignore')
        body_length = len(body)
        
        # Cek error message
        error_result = _check_error_in_response(body)
        if error_result:
            _, error_name = error_result
            flow.response.content = b"00000000"
            with current_userid_lock:
                userid_to_display = current_userid
            print(f"{RED}[LOGIN FAILED] {userid_to_display} | {error_name}{RESET}" if userid_to_display 
                  else f"{RED}[LOGIN FAILED] {error_name}{RESET}")
            if userid_to_display:
                _send_callback_to_server(userid_to_display, 'login_failed', error=error_name)
            return
        
        # Login success (body 80 chars)
        if body_length == 80:
            token, userid = _parse_token_from_80chars(body)
            if token and userid:
                threading.Thread(target=_fetch_money_in_background, args=(userid, token), daemon=True).start()
                return
            elif not SIMPLE_LOG:
                print(f"{GREEN}[RESPONSE] [{flow.response.status_code}] | body={body_length} chars{RESET}")
                print(f"{GREEN}{body}{RESET}\n")
                return
        
        # Modify response untuk v=376
        if v_length == 376:
            flow.response.content = b"00000000"
            if not SIMPLE_LOG:
                print(f"{GREEN}[RESPONSE MODIFIED] v={v_length} chars -> Response changed to '00000000'{RESET}")
            return
        
        # Show response detail (jika tidak simple log)
        if not SIMPLE_LOG:
            display_body = body[:500] + "... (truncated)" if body_length > 500 else body
            print(f"{GREEN}[RESPONSE] [{flow.response.status_code}] | body={body_length} chars{RESET}")
            print(f"{GREEN}{display_body}{RESET}\n")


addons = [FilterPath()]

if __name__ == "__main__":
    mitmdump(["-p", "8113", "-q", "-s", __file__])
