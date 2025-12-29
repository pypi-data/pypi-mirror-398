import os
import json
import time
import uuid
import zlib
import random
import hashlib
import binascii
import pyscrypt
import itertools
import tls_client
import requests
import secrets
import base64
from typing import Union, Callable, Any, NamedTuple
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

class pkce:
    @staticmethod
    def generate_code_verifier(length=43):
        return base64.urlsafe_b64encode(
            secrets.token_bytes(length)
        ).decode('utf-8').rstrip('=')
    
    @staticmethod
    def generate_code_challenge(verifier):
        digest = hashlib.sha256(verifier.encode('utf-8')).digest()
        return base64.urlsafe_b64encode(digest).decode('utf-8').rstrip('=')
    
    @staticmethod
    def generate_pkce_pair(length=43):
        verifier = pkce.generate_code_verifier(length)
        challenge = pkce.generate_code_challenge(verifier)
        return verifier, challenge

class Crypto:
    key = bytes.fromhex("6f71a512b1e035eaab53d8be73120d3fb68a0ca346b9560aab3e5cdf753d5e98")
    aes_gcm = AESGCM(key)
    
    @staticmethod
    def encrypt(string: bytes) -> str:
        iv = os.urandom(12)
        encrypted = Crypto.aes_gcm.encrypt(iv, string, None)
        tag = encrypted[-16:]
        text = encrypted[:-16]
        iv_base64 = base64.b64encode(iv).decode("utf-8")
        return f"{iv_base64}::{tag.hex()}::{text.hex()}"
    
    @staticmethod
    def decrypt(string: str) -> bytes:
        parts = string.split("::")
        iv = base64.b64decode(parts[0])
        tag = bytes.fromhex(parts[1])
        text = bytes.fromhex(parts[2])
        return Crypto.aes_gcm.decrypt(iv, text + tag, None)

class Fingerprint:
    @staticmethod
    def encode(obj: dict) -> tuple:
        payload = json.dumps(obj, separators=(",", ":")).encode()
        crc = zlib.crc32(payload) & 0xFFFFFFFF
        crc_hex = f"{crc:08x}"
        checksum = crc_hex.encode("ascii").upper()
        return checksum, checksum + b"#" + payload
    
    @staticmethod
    def fingerprint() -> tuple:
        start = int(time.time() * 1000)
        webgl_data = {
            "webgl_unmasked_renderer": "ANGLE (Apple, ANGLE Metal Renderer: Apple M2 Pro, Unspecified Version)",
            "webgl": [{
                "webgl_extensions": "ANGLE_instanced_arrays;EXT_blend_minmax;EXT_clip_control;EXT_color_buffer_half_float;EXT_depth_clamp;EXT_disjoint_timer_query;EXT_float_blend;EXT_frag_depth;EXT_polygon_offset_clamp;EXT_shader_texture_lod;EXT_texture_compression_bptc;EXT_texture_compression_rgtc;EXT_texture_filter_anisotropic;EXT_texture_mirror_clamp_to_edge;EXT_sRGB;KHR_parallel_shader_compile;OES_element_index_uint;OES_fbo_render_mipmap;OES_standard_derivatives;OES_texture_float;OES_texture_float_linear;OES_texture_half_float;OES_texture_half_float_linear;OES_vertex_array_object;WEBGL_blend_func_extended;WEBGL_color_buffer_float;WEBGL_compressed_texture_astc;WEBGL_compressed_texture_etc;WEBGL_compressed_texture_etc1;WEBGL_compressed_texture_pvrtc;WEBGL_compressed_texture_s3tc;WEBGL_compressed_texture_s3tc_srgb;WEBGL_debug_renderer_info;WEBGL_debug_shaders;WEBGL_depth_texture;WEBGL_draw_buffers;WEBGL_lose_context;WEBGL_multi_draw;WEBGL_polygon_mode",
                "webgl_extensions_hash": "9cbeeda2b4ce5415b07e1d1e43783a58",
                "webgl_renderer": "WebKit WebGL",
                "webgl_vendor": "WebKit",
                "webgl_version": "WebGL 1.0 (OpenGL ES 2.0 Chromium)",
                "webgl_shading_language_version": "WebGL GLSL ES 1.0 (OpenGL ES GLSL ES 1.0 Chromium)",
                "webgl_unmasked_vendor": "Google Inc. (Apple)",
                "webgl_unmasked_renderer": "ANGLE (Apple, ANGLE Metal Renderer: Apple M2 Pro, Unspecified Version)",
            }]
        }
        bins = [random.randrange(0, 40) for _ in range(256)]
        bins[0] = random.randrange(14473, 16573)
        bins[-1] = random.randrange(14473, 16573)
        fp = {
            "metrics": {"fp2": 1, "browser": 0, "capabilities": 1, "gpu": 7, "dnt": 0, "math": 0, "screen": 0, "navigator": 0, "auto": 1, "stealth": 0, "subtle": 0, "canvas": 5, "formdetector": 1, "be": 0},
            "start": start,
            " flashVersion": None,
            "plugins": [{"name": "PDF Viewer", "str": "PDF Viewer "}, {"name": "Chrome PDF Viewer", "str": "Chrome PDF Viewer "}, {"name": "Chromium PDF Viewer", "str": "Chromium PDF Viewer "}, {"name": "Microsoft Edge PDF Viewer", "str": "Microsoft Edge PDF Viewer "}, {"name": "WebKit built-in PDF", "str": "WebKit built-in PDF "}],
            "dupedPlugins": "PDF Viewer Chrome PDF Viewer Chromium PDF Viewer Microsoft Edge PDF Viewer WebKit built-in PDF ||1920-1080-1032-24-*-*-*",
            "screenInfo": "1920-1080-1032-24-*-*-*",
            "referrer": "",
            "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
            "location": "",
            "webDriver": False,
            "capabilities": {"css": {"textShadow": 1, "WebkitTextStroke": 1, "boxShadow": 1, "borderRadius": 1, "borderImage": 1, "opacity": 1, "transform": 1, "transition": 1}, "js": {"audio": True, "geolocation": True, "localStorage": "supported", "touch": False, "video": True, "webWorker": True}, "elapsed": 1},
            "gpu": {"vendor": webgl_data["webgl"][0]["webgl_unmasked_vendor"], "model": webgl_data["webgl_unmasked_renderer"], "extensions": webgl_data["webgl"][0]["webgl_extensions"].split(";")},
            "dnt": None,
            "math": {"tan": "-1.4214488238747245", "sin": "0.8178819121159085", "cos": "-0.5753861119575491"},
            "automation": {"wd": {"properties": {"document": [], "window": [], "navigator": []}}, "phantom": {"properties": {"window": []}}},
            "stealth": {"t1": 0, "t2": 0, "i": 1, "mte": 0, "mtd": False},
            "crypto": {"crypto": 1, "subtle": 1, "encrypt": True, "decrypt": True, "wrapKey": True, "unwrapKey": True, "sign": True, "verify": True, "digest": True, "deriveBits": True, "deriveKey": True, "getRandomValues": True, "randomUUID": True},
            "canvas": {"hash": random.randrange(645172295, 735192295), "emailHash": None, "histogramBins": bins},
            "formDetected": False,
            "numForms": 0,
            "numFormElements": 0,
            "be": {"si": False},
            "end": start + 1,
            "errors": [],
            "version": "2.4.0",
            "id": str(uuid.uuid4()),
        }
        checksum, data = Fingerprint.encode(fp)
        return checksum.decode(), Crypto.encrypt(data)

class Verify:
    @staticmethod
    def _check(digest: bytes, difficulty: int) -> bool:
        full, rem = divmod(difficulty, 8)
        if digest[:full] != b"\x00" * full:
            return False
        if rem and (digest[full] >> (8 - rem)):
            return False
        return True
    
    @staticmethod
    def _scrypt(input: str, salt: str, memory_cost: int) -> str:
        return binascii.hexlify(
            pyscrypt.hash(
                password=input.encode(),
                salt=salt.encode(),
                N=memory_cost,
                r=8, p=1, dkLen=16
            )
        ).decode()
    
    @staticmethod
    def pow(input: str, checksum: str, difficulty: int) -> str:
        combined_bytes = (input + checksum).encode("utf-8")
        for nonce in itertools.count(0):
            data = combined_bytes + str(nonce).encode()
            digest = hashlib.sha256(data).digest()
            if Verify._check(digest, difficulty):
                return str(nonce)
        return None
    
    @staticmethod
    def compute_scrypt_nonce(input: str, checksum: str, difficulty: int) -> str:
        combined = input + checksum
        salt = checksum
        memory = 128
        for nonce in itertools.count(0):
            result = Verify._scrypt(f"{combined}{nonce}", salt, memory)
            if Verify._check(binascii.unhexlify(result), difficulty):
                return str(nonce)
        return None
    
    CHALLENGE_TYPES = {
        "h72f957df656e80ba55f5d8ce2e8c7ccb59687dba3bfb273d54b08a261b2f3002": compute_scrypt_nonce,
        "h7b0c470f0cfe3a80a9e26526ad185f484f6817d0832712a4a37a908786a6a67f": pow
    }

class AwsWafSolver:
    def __init__(self, proxy: str = None):
        self.session = tls_client.Session(client_identifier="chrome_132", random_tls_extension_order=True)
        if proxy:
            self.session.proxies = {"http": f"http://{proxy}", "https": f"http://{proxy}"}
        self.session.headers = {
            "Connection": "keep-alive", "Accept": "*/*", "Origin": "https://www.paypay.ne.jp",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"
        }
    
    def get_goku_props(self) -> dict:
        response = self.session.get("https://www.paypay.ne.jp/portal/api/v2/oauth2/authorize").text
        return json.loads(response.split("window.gokuProps = ")[1].split(";")[0])
    
    def get_inputs(self) -> dict:
        return self.session.get("https://02dad1968f9c.81b5a82a.ap-northeast-1.token.awswaf.com/02dad1968f9c/a61454b1ee5d/2748e176355d/inputs", params={"client": "browser"}).json()
    
    def get_token(self) -> str:
        try:
            inputs = self.get_inputs()
            goku_props = self.get_goku_props()
            checksum, fp = Fingerprint.fingerprint()
            verify_func = Verify.CHALLENGE_TYPES[inputs["challenge_type"]]
            solution = verify_func(inputs["challenge"]["input"], checksum, inputs["difficulty"])
            payload = {
                "challenge": inputs["challenge"], "checksum": checksum, "solution": solution,
                "signals": [{"name": "Zoey", "value": {"Present": fp}}], "client": "Browser",
                "domain": "www.paypay.ne.jp", "goku_props": goku_props
            }
            response = self.session.post("https://02dad1968f9c.81b5a82a.ap-northeast-1.token.awswaf.com/02dad1968f9c/a61454b1ee5d/2748e176355d/verify", json=payload)
            if response.status_code == 200:
                return response.json()["token"]
        except:
            return None
        return None

class PayPayUtils:
    @staticmethod
    def generate_vector(r1: tuple, r2: tuple, r3: tuple) -> str:
        return f"{random.uniform(*r1):.8f}_{random.uniform(*r2):.8f}_{random.uniform(*r3):.8f}"
    
    @staticmethod
    def generate_device_state():
        class DeviceHeaders(NamedTuple):
            orientation: str; orientation2: str; rotation: str; rotation2: str; acceleration: str; acceleration2: str
        return DeviceHeaders(
            PayPayUtils.generate_vector((2.2, 2.6), (-0.2, -0.05), (-0.05, 0.1)),
            PayPayUtils.generate_vector((2.0, 2.6), (-0.2, -0.05), (-0.05, 0.2)),
            PayPayUtils.generate_vector((-0.8, -0.6), (0.65, 0.8), (-0.12, -0.04)),
            PayPayUtils.generate_vector((-0.85, -0.4), (0.53, 0.9), (-0.15, -0.03)),
            PayPayUtils.generate_vector((-0.35, 0.0), (-0.01, 0.3), (-0.1, 0.1)),
            PayPayUtils.generate_vector((0.01, 0.04), (-0.04, 0.09), (-0.03, 0.1))
        )

class PayPay:
    def __init__(self, phone: str = None, password: str = None, device_uuid: str = None, access_token: str = None, proxy: str = None):
        self.access_token = access_token
        self.device_uuid = device_uuid or str(uuid.uuid4())
        self.client_uuid = str(uuid.uuid4())
        self.version = "5.11.1"
        self.session = requests.Session()
        self.webview_session = tls_client.Session(client_identifier="chrome_132", random_tls_extension_order=True)
        if proxy:
            self.session.proxies = {"http": proxy, "https": proxy}
            self.webview_session.proxies = {"http": proxy, "https": proxy}
        
        state = PayPayUtils.generate_device_state()
        self.headers = {
            "Client-OS-Type": "ANDROID", "Client-Type": "PAYPAYAPP", "Client-UUID": self.client_uuid,
            "Client-Version": self.version, "Device-UUID": self.device_uuid, "Timezone": "Asia/Tokyo",
            "User-Agent": f"PaypayApp/{self.version} Android10",
            "Device-Orientation": state.orientation, "Device-Orientation-2": state.orientation2,
            "Device-Rotation": state.rotation, "Device-Rotation-2": state.rotation2,
            "Device-Acceleration": state.acceleration, "Device-Acceleration-2": state.acceleration2
        }
        if self.access_token:
            self.headers["Authorization"] = f"Bearer {self.access_token}"
            self.headers["Content-Type"] = "application/json"
        
        if phone and password and not self.access_token:
            self.login_start(phone, password)

    def login_start(self, phone: str, password: str):
        phone = phone.replace("-", "")
        self.verifier, self.challenge = pkce.generate_pkce_pair()
        resp = self.session.post(
            "https://app4.paypay.ne.jp/bff/v2/oauth2/par",
            headers=self.headers,
            data={
                "clientId": "pay2-mobile-app-client", "redirectUri": "paypay://oauth2/callback",
                "responseType": "code", "codeChallenge": self.challenge, "codeChallengeMethod": "S256"
            }
        ).json()
        
        request_uri = resp["payload"]["requestUri"]
        self.webview_session.get("https://www.paypay.ne.jp/portal/api/v2/oauth2/authorize", params={"client_id": "pay2-mobile-app-client", "request_uri": request_uri})
        
        login_resp = self.webview_session.post(
            "https://www.paypay.ne.jp/portal/api/v2/oauth2/sign-in/password",
            json={"username": phone, "password": password, "signInAttemptCount": 1}
        ).json()
        
        if "redirectUrl" in login_resp["payload"]:
            code = login_resp["payload"]["redirectUrl"].split("code=")[1].split("&")[0]
            self.complete_login(code)

    def login(self, url_or_id: str):
        code_id = url_or_id.split("id=")[1] if "id=" in url_or_id else url_or_id
        resp = self.webview_session.post(
            "https://www.paypay.ne.jp/portal/api/v2/oauth2/extension/sign-in/2fa/otl/verify",
            json={"params": {"extension_id": "user-main-2fa-v1", "data": {"type": "COMPLETE_OTL"}}}
        ).json()
        code = resp["payload"]["redirect_uri"].split("code=")[1].split("&")[0]
        self.complete_login(code)

    def complete_login(self, code: str):
        resp = self.session.post(
            "https://app4.paypay.ne.jp/bff/v2/oauth2/token",
            headers=self.headers,
            data={"clientId": "pay2-mobile-app-client", "code": code, "codeVerifier": self.verifier}
        ).json()
        self.access_token = resp["payload"]["accessToken"]
        self.refresh_token = resp["payload"]["refreshToken"]
        self.headers["Authorization"] = f"Bearer {self.access_token}"

    def token_refresh(self, refresh_token: str):
        resp = self.session.post(
            "https://app4.paypay.ne.jp/bff/v2/oauth2/refresh",
            headers=self.headers,
            data={"clientId": "pay2-mobile-app-client", "refreshToken": refresh_token}
        ).json()
        self.access_token = resp["payload"]["accessToken"]
        self.refresh_token = resp["payload"]["refreshToken"]
        return resp

    def get_profile(self):
        resp = self.session.get("https://app4.paypay.ne.jp/bff/v2/getProfileDisplayInfo", headers=self.headers).json()
        class Profile(NamedTuple):
            name: str; external_user_id: str; icon: str
        p = resp["payload"]["userProfile"]
        return Profile(p["nickName"], p["externalUserId"], p["avatarImageUrl"])

    def get_balance(self):
        resp = self.session.get("https://app4.paypay.ne.jp/bff/v1/getBalanceInfo", headers=self.headers).json()
        class Balance(NamedTuple):
            all_balance: int; useable_balance: int; money_light: int; money: int; points: int
        p = resp["payload"]
        return Balance(
            p["allTotalBalanceInfo"]["balance"],
            p["usableBalanceInfoWithoutCashback"]["balance"],
            p["prepaidBalanceInfo"]["balance"],
            p["emoneyBalanceInfo"]["balance"],
            p["cashBackBalanceInfo"]["balance"]
        )

    def get_history(self, size: int = 20):
        return self.session.get("https://app4.paypay.ne.jp/bff/v3/getPaymentHistory", params={"pageSize": size}, headers=self.headers).json()

    def link_check(self, url_or_code: str):
        code = url_or_code.split("/")[-1]
        resp = self.session.get("https://app4.paypay.ne.jp/bff/v2/getP2PLinkInfo", params={"verificationCode": code}, headers=self.headers).json()
        class LinkInfo(NamedTuple):
            amount: int; money_light: int; money: int; has_password: bool; chat_room_id: str; status: str; order_id: str
        p = resp["payload"]
        return LinkInfo(
            p["pendingP2PInfo"]["amount"],
            p["message"]["data"]["subWalletSplit"]["senderPrepaidAmount"],
            p["message"]["data"]["subWalletSplit"]["senderEmoneyAmount"],
            p["pendingP2PInfo"]["isSetPasscode"],
            p["message"]["chatRoomId"],
            p["message"]["data"]["status"],
            p["pendingP2PInfo"]["orderId"]
        )

    def link_receive(self, url_or_code: str, passcode: str = None, link_info=None):
        code = url_or_code.split("/")[-1]
        info = link_info or self.link_check(code)
        payload = {"requestId": str(uuid.uuid4()), "orderId": info.order_id, "verificationCode": code, "passcode": passcode}
        return self.session.post("https://app4.paypay.ne.jp/bff/v2/acceptP2PSendMoneyLink", headers=self.headers, json=payload).json()

    def create_link(self, amount: int, passcode: str = None):
        payload = {"requestId": str(uuid.uuid4()), "amount": amount}
        if passcode: payload["passcode"] = passcode
        resp = self.session.post("https://app4.paypay.ne.jp/bff/v2/executeP2PSendMoneyLink", headers=self.headers, json=payload).json()
        class CreatedLink(NamedTuple):
            link: str; chat_room_id: str
        return CreatedLink(resp["payload"]["link"], resp["payload"]["chatRoomId"])

    def create_p2pcode(self, amount: int = None):
        payload = {"amount": amount}
        resp = self.session.post("https://app4.paypay.ne.jp/bff/v1/createP2PCode", headers=self.headers, json=payload).json()
        class P2PCode(NamedTuple):
            p2pcode: str
        return P2PCode(resp["payload"]["p2pCode"])
