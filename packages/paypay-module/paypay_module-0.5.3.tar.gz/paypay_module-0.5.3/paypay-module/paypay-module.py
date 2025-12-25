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
import pkce
import base64
from typing import Union, Callable, Any, NamedTuple
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class Crypto:
    
    key = bytes.fromhex("6f71a512b1e035eaab53d8be73120d3fb68a0ca346b9560aab3e5cdf753d5e98")
    aes_gcm = AESGCM(key)
    
    @staticmethod
    def encrypt(string: bytes) -> str:
        """AES-GCMで暗号化"""
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
            "metrics": {
                "fp2": 1, "browser": 0, "capabilities": 1, "gpu": 7,
                "dnt": 0, "math": 0, "screen": 0, "navigator": 0,
                "auto": 1, "stealth": 0, "subtle": 0, "canvas": 5,
                "formdetector": 1, "be": 0
            },
            "start": start,
            "flashVersion": None,
            "plugins": [
                {"name": "PDF Viewer", "str": "PDF Viewer "},
                {"name": "Chrome PDF Viewer", "str": "Chrome PDF Viewer "},
                {"name": "Chromium PDF Viewer", "str": "Chromium PDF Viewer "},
                {"name": "Microsoft Edge PDF Viewer", "str": "Microsoft Edge PDF Viewer "},
                {"name": "WebKit built-in PDF", "str": "WebKit built-in PDF "}
            ],
            "dupedPlugins": "PDF Viewer Chrome PDF Viewer Chromium PDF Viewer Microsoft Edge PDF Viewer WebKit built-in PDF ||1920-1080-1032-24-*-*-*",
            "screenInfo": "1920-1080-1032-24-*-*-*",
            "referrer": "",
            "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
            "location": "",
            "webDriver": False,
            "capabilities": {
                "css": {
                    "textShadow": 1, "WebkitTextStroke": 1, "boxShadow": 1,
                    "borderRadius": 1, "borderImage": 1, "opacity": 1,
                    "transform": 1, "transition": 1
                },
                "js": {
                    "audio": True,
                    "geolocation": random.choice([True, False]),
                    "localStorage": "supported",
                    "touch": False,
                    "video": True,
                    "webWorker": random.choice([True, False]),
                },
                "elapsed": 1
            },
            "gpu": {
                "vendor": webgl_data["webgl"][0]["webgl_unmasked_vendor"],
                "model": webgl_data["webgl_unmasked_renderer"],
                "extensions": webgl_data["webgl"][0]["webgl_extensions"].split(";")
            },
            "dnt": None,
            "math": {
                "tan": "-1.4214488238747245",
                "sin": "0.8178819121159085",
                "cos": "-0.5753861119575491"
            },
            "automation": {
                "wd": {"properties": {"document": [], "window": [], "navigator": []}},
                "phantom": {"properties": {"window": []}}
            },
            "stealth": {"t1": 0, "t2": 0, "i": 1, "mte": 0, "mtd": False},
            "crypto": {
                "crypto": 1, "subtle": 1, "encrypt": True, "decrypt": True,
                "wrapKey": True, "unwrapKey": True, "sign": True, "verify": True,
                "digest": True, "deriveBits": True, "deriveKey": True,
                "getRandomValues": True, "randomUUID": True
            },
            "canvas": {
                "hash": random.randrange(645172295, 735192295),
                "emailHash": None,
                "histogramBins": bins
            },
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
        """SHA256 PoW"""
        combined_bytes = (input + checksum).encode("utf-8")
        
        for nonce in itertools.count(0):
            data = combined_bytes + str(nonce).encode()
            digest = hashlib.sha256(data).digest()
            if Verify._check(digest, difficulty):
                return str(nonce)
        return None
    
    @staticmethod
    def compute_scrypt_nonce(input: str, checksum: str, difficulty: int) -> str:
        """Scrypt PoW"""
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
        "h7b0c470f0cfe3a80a9e26526ad185f484f6817d0832712a4a37a908786a6a67f": pow,
        "ha9faaffd31b4d5ede2a2e19d2d7fd525f66fee61911511960dcbb52d3c48ce25": "mp_verify"
    }


class AwsWafSolver:
    
    def __init__(self, proxy: str = None):
        self.session = tls_client.Session(
            client_identifier="chrome_132",
            random_tls_extension_order=True
        )
        
        if proxy:
            proxies = {
                "http": f"http://{proxy}",
                "https": f"http://{proxy}"
            }
            self.session.proxies.update(proxies)
        
        self.session.headers = {
            "Connection": "keep-alive",
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "en-US,en;q=0.9",
            "Origin": "https://www.paypay.ne.jp",
            "Sec-Ch-Ua": '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Site": "cross-site",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"
        }
    
    def get_goku_props(self) -> dict:
        response = self.session.get(
            "https://www.paypay.ne.jp/portal/api/v2/oauth2/authorize",
            headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
            }
        ).text
        
        goku_props = json.loads(response.split("window.gokuProps = ")[1].split(";")[0])
        return goku_props
    
    def get_inputs(self) -> dict:
        response = self.session.get(
            "https://02dad1968f9c.81b5a82a.ap-northeast-1.token.awswaf.com/02dad1968f9c/a61454b1ee5d/2748e176355d/inputs",
            params={"client": "browser"}
        ).json()
        return response
    
    def build_payload(self) -> dict:
        inputs = self.get_inputs()
        goku_props = self.get_goku_props()
        checksum, fp = Fingerprint.fingerprint()
        
        verify_func = Verify.CHALLENGE_TYPES[inputs["challenge_type"]]
        solution = verify_func(inputs["challenge"]["input"], checksum, inputs["difficulty"])
        
        payload = {
            "challenge": inputs["challenge"],
            "checksum": checksum,
            "solution": solution,
            "signals": [{"name": "Zoey", "value": {"Present": fp}}],
            "existing_token": None,
            "client": "Browser",
            "domain": "www.paypay.ne.jp",
            "metrics": [
                {"name": "2", "value": random.uniform(0, 1), "unit": "2"},
                {"name": "100", "value": 0, "unit": "2"},
                {"name": "103", "value": 8, "unit": "2"},
                {"name": "108", "value": 1, "unit": "2"},
                {"name": "111", "value": 2, "unit": "2"},
                {"name": "3", "value": 4, "unit": "2"},
                {"name": "1", "value": random.uniform(10, 20), "unit": "2"},
                {"name": "4", "value": 36.5, "unit": "2"},
                {"name": "5", "value": random.uniform(0, 1), "unit": "2"},
                {"name": "6", "value": random.uniform(50, 60), "unit": "2"},
                {"name": "0", "value": random.uniform(130, 140), "unit": "2"},
                {"name": "8", "value": 1, "unit": "4"}
            ],
            "goku_props": goku_props
        }
        return payload
    
    def get_token(self) -> str:
        try:
            payload = self.build_payload()
            response = self.session.post(
                "https://02dad1968f9c.81b5a82a.ap-northeast-1.token.awswaf.com/02dad1968f9c/a61454b1ee5d/2748e176355d/verify",
                json=payload
            )
            
            if response.status_code == 200:
                return response.json()["token"]
        except Exception as e:
            print(f"WAF Solver Error: {e}")
        return None


class PayPayUtils:
    
    @staticmethod
    def generate_vector(r1: tuple, r2: tuple, r3: tuple, precision: int = 8) -> str:
        v1 = f"{random.uniform(*r1):.{precision}f}"
        v2 = f"{random.uniform(*r2):.{precision}f}"
        v3 = f"{random.uniform(*r3):.{precision}f}"
        return f"{v1}_{v2}_{v3}"
    
    @staticmethod
    def generate_device_state():
        class DeviceHeaders(NamedTuple):
            device_orientation: str
            device_orientation_2: str
            device_rotation: str
            device_rotation_2: str
            device_acceleration: str
            device_acceleration_2: str
        
        return DeviceHeaders(
            PayPayUtils.generate_vector((2.2, 2.6), (-0.2, -0.05), (-0.05, 0.1)),
            PayPayUtils.generate_vector((2.0, 2.6), (-0.2, -0.05), (-0.05, 0.2)),
            PayPayUtils.generate_vector((-0.8, -0.6), (0.65, 0.8), (-0.12, -0.04)),
            PayPayUtils.generate_vector((-0.85, -0.4), (0.53, 0.9), (-0.15, -0.03)),
            PayPayUtils.generate_vector((-0.35, 0.0), (-0.01, 0.3), (-0.1, 0.1)),
            PayPayUtils.generate_vector((0.01, 0.04), (-0.04, 0.09), (-0.03, 0.1))
        )
    
    @staticmethod
    def update_device_headers(headers: dict) -> dict:

        state = PayPayUtils.generate_device_state()
        headers.update({
            "Device-Orientation": state.device_orientation,
            "Device-Orientation-2": state.device_orientation_2,
            "Device-Rotation": state.device_rotation,
            "Device-Rotation-2": state.device_rotation_2,
            "Device-Acceleration": state.device_acceleration,
            "Device-Acceleration-2": state.device_acceleration_2
        })
        return headers


# ==================== Exceptions ====================
class PayPayException(Exception):
    pass

class PayPayLoginError(Exception):
    pass

class PayPayNetworkError(Exception):
    pass

class AwsWafException(Exception):
    pass


# ==================== Enhanced PayPay Class ====================
class EnhancedPayPay:

    
    def __init__(self, 
                 access_token: str = None,
                 device_uuid: str = None,
                 client_uuid: str = None,
                 proxy: str = None,
                 enable_waf_bypass: bool = True):
                     
        self.access_token = access_token
        self.device_uuid = device_uuid or str(uuid.uuid4())
        self.client_uuid = client_uuid or str(uuid.uuid4())
        self.proxy = proxy
        self.version = "5.11.1"
        
        self.session = requests.Session()
        self.webview_session = tls_client.Session(
            client_identifier="chrome_132",
            random_tls_extension_order=True
        )
        
        if self.proxy:
            proxies = {
                "http": f"http://{proxy}",
                "https": f"http://{proxy}"
            }
            self.session.proxies.update(proxies)
            self.webview_session.proxies.update(proxies)
        
        self.waf_token = None
        if enable_waf_bypass:
            try:
                solver = AwsWafSolver(proxy=proxy)
                self.waf_token = solver.get_token()
                if self.waf_token:
                    self.webview_session.cookies.set(
                        name="aws-waf-token",
                        value=self.waf_token,
                        domain="www.paypay.ne.jp"
                    )
                else:
                    raise AwsWafException("AWS WAF トークン取得失敗")
            except Exception as e:
                print(f"警告: AWS WAF バイパス失敗 - {e}")
        
        device_state = PayPayUtils.generate_device_state()
        self.params = {"payPayLang": "ja"}
        
        self.headers = {
            "Accept": "*/*",
            "Accept-Charset": "UTF-8",
            "Accept-Encoding": "gzip",
            "Client-Mode": "NORMAL",
            "Client-OS-Release-Version": "10",
            "Client-OS-Type": "ANDROID",
            "Client-OS-Version": "29.0.0",
            "Client-Type": "PAYPAYAPP",
            "Client-UUID": self.client_uuid,
            "Client-Version": self.version,
            "Connection": "Keep-Alive",
            "Content-Type": "application/x-www-form-urlencoded",
            "Device-Acceleration": device_state.device_acceleration,
            "Device-Acceleration-2": device_state.device_acceleration_2,
            "Device-Brand-Name": "KDDI",
            "Device-Hardware-Name": "qcom",
            "Device-In-Call": "false",
            "Device-Lock-App-Setting": "false",
            "Device-Lock-Type": "NONE",
            "Device-Manufacturer-Name": "samsung",
            "Device-Name": "SCV38",
            "Device-Orientation": device_state.device_orientation,
            "Device-Orientation-2": device_state.device_orientation_2,
            "Device-Rotation": device_state.device_rotation,
            "Device-Rotation-2": device_state.device_rotation_2,
            "Device-UUID": self.device_uuid,
            "Host": "app4.paypay.ne.jp",
            "Is-Emulator": "false",
            "Network-Status": "WIFI",
            "System-Locale": "ja",
            "Timezone": "Asia/Tokyo",
            "User-Agent": f"PaypayApp/{self.version} Android10"
        }
        
        if self.access_token:
            self.headers["Authorization"] = f"Bearer {self.access_token}"
            self.headers["Content-Type"] = "application/json"
    
    
    def login_start(self, phone: str, password: str):
        
        if self.access_token:
            raise PayPayException("既にログイン済みです")
        
        if "-" in phone:
            phone = phone.replace("-", "")
        
        self.verifier, self.challenge = pkce.generate_pkce_pair(43)
        
        response = self.session.post(
            "https://app4.paypay.ne.jp/bff/v2/oauth2/par",
            params=self.params,
            headers=self.headers,
            data={
                "clientId": "pay2-mobile-app-client",
                "clientAppVersion": self.version,
                "clientOsVersion": "29.0.0",
                "clientOsType": "ANDROID",
                "redirectUri": "paypay://oauth2/callback",
                "responseType": "code",
                "state": pkce.generate_code_verifier(43),
                "codeChallenge": self.challenge,
                "codeChallengeMethod": "S256",
                "scope": "REGULAR",
                "tokenVersion": "v2",
                "prompt": "",
                "uiLocales": "ja"
            }
        )
        
        try:
            data = response.json()
            if data["header"]["resultCode"] != "S0000":
                raise PayPayLoginError(data)
        except:
            raise PayPayNetworkError("日本以外からは接続できません")
        
        request_uri = data["payload"]["requestUri"]
        
        self._webview_authorize(request_uri)
        self._webview_signin_page()
        self._webview_par_check()
        
        response = self.webview_session.post(
            "https://www.paypay.ne.jp/portal/api/v2/oauth2/sign-in/password",
            headers=self._get_webview_headers(
                "https://www.paypay.ne.jp/portal/oauth2/sign-in?client_id=pay2-mobile-app-client&mode=landing"
            ),
            json={
                "username": phone,
                "password": password,
                "signInAttemptCount": 1
            }
        )
        
        try:
            data = response.json()
            if data["header"]["resultCode"] != "S0000":
                raise PayPayLoginError(data)
        except:
            raise PayPayNetworkError("日本以外からは接続できません")
        
        try:
            uri = data["payload"]["redirectUrl"].replace("paypay://oauth2/callback?", "").split("&")
            return self._complete_token_exchange(uri[0].replace("code=", ""))
        except:
            self._start_2fa_flow()
    
    def login_confirm(self, accept_url: str):
        
        if "https://" in accept_url:
            accept_url = accept_url.replace("https://www.paypay.ne.jp/portal/oauth2/l?id=", "")
        
        response = self.webview_session.post(
            "https://www.paypay.ne.jp/portal/api/v2/oauth2/extension/sign-in/2fa/otl/verify",
            headers=self._get_webview_headers(
                f"https://www.paypay.ne.jp/portal/oauth2/l?id={accept_url}&client_id=pay2-mobile-app-client"
            ),
            json={
                "params": {
                    "extension_id": "user-main-2fa-v1",
                    "data": {
                        "type": "COMPLETE_OTL",
                        "payload": None
                    }
                }
            }
        )
        
        try:
            data = response.json()
            if data["header"]["resultCode"] != "S0000":
                raise PayPayLoginError(data)
            
            uri = data["payload"]["redirect_uri"].replace("paypay://oauth2/callback?", "").split("&")
            self._complete_token_exchange(uri[0].replace("code=", ""))
        except:
            raise PayPayLoginError("認証コードの取得に失敗しました")
    
    def token_refresh(self, refresh_token: str):

        if not self.access_token:
            raise PayPayLoginError("まずはログインしてください")
        
        response = self.session.post(
            "https://app4.paypay.ne.jp/bff/v2/oauth2/refresh",
            headers=self.headers,
            data={
                "clientId": "pay2-mobile-app-client",
                "refreshToken": refresh_token,
                "tokenVersion": "v2"
            }
        ).json()
        
        if response["header"]["resultCode"] != "S0000":
            raise PayPayLoginError(response)
        
        self.access_token = response["payload"]["accessToken"]
        self.refresh_token = response["payload"]["refreshToken"]
        self.headers["Authorization"] = f"Bearer {self.access_token}"
        
        return response
    
    
    def get_profile(self):

        response = self.session.get(
            "https://app4.paypay.ne.jp/bff/v2/getProfileDisplayInfo",
            headers=self.headers,
            params={
                "includeExternalProfileSync": "true",
                "completedOptionalTasks": "ENABLED_NEARBY_DEALS",
                "payPayLang": "ja"
            }
        ).json()
        
        if response["header"]["resultCode"] != "S0000":
            return None
        
        class Profile(NamedTuple):
            name: str
            external_user_id: str
            icon: str
            raw: dict
        
        payload = response["payload"]["userProfile"]
        return Profile(
            payload["nickName"],
            payload["externalUserId"],
            payload["avatarImageUrl"],
            response
        )
    
    def get_balance(self):

        response = self.session.get(
            "https://app4.paypay.ne.jp/bff/v1/getBalanceInfo",
            headers=self.headers,
            params={
                "includePendingBonusLite": "false",
                "includePending": "true",
                "noCache": "true",
                "includeKycInfo": "true",
                "includePayPaySecuritiesInfo": "true",
                "includePointInvestmentInfo": "true",
                "includePayPayBankInfo": "true",
                "includeGiftVoucherInfo": "true",
                "payPayLang": "ja"
            }
        ).json()
        
        if response["header"]["resultCode"] != "S0000":
            return None
        
        class Balance(NamedTuple):
            money: int
            money_light: int
            all_balance: int
            useable_balance: int
            points: int
            raw: dict
        
        try:
            money = response["payload"]["walletDetail"]["emoneyBalanceInfo"]["balance"]
        except:
            money = 0
        
        return Balance(
            money,
            response["payload"]["walletDetail"]["prepaidBalanceInfo"]["balance"],
            response["payload"]["walletSummary"]["allTotalBalanceInfo"]["balance"],
            response["payload"]["walletSummary"]["usableBalanceInfoWithoutCashback"]["balance"],
            response["payload"]["walletDetail"]["cashBackBalanceInfo"]["balance"],
            response
        )
    
    def get_history(self, size: int = 20, cashback: bool = False):

        params = {
            "pageSize": str(size),
            "orderTypes": "CASHBACK" if cashback else "",
            "paymentMethodTypes": "",
            "signUpCompletedAt": "2021-01-02T10:16:24Z",
            "isOverdraftOnly": "false",
            "payPayLang": "ja"
        }
        
        response = self.session.get(
            "https://app4.paypay.ne.jp/bff/v3/getPaymentHistory",
            params=params,
            headers=self.headers
        ).json()
        
        if response["header"]["resultCode"] != "S0000":
            return None
        
        return response
    
    
    def check_link(self, url: str):

        if "https://" in url:
            url = url.replace("https://pay.paypay.ne.jp/", "")
        
        response = self.session.get(
            "https://app4.paypay.ne.jp/bff/v2/getP2PLinkInfo",
            params={"verificationCode": url, "payPayLang": "ja"},
            headers=self.headers
        ).json()
        
        if response["header"]["resultCode"] != "S0000":
            return None
        
        class LinkInfo(NamedTuple):
            sender_name: str
            sender_external_user_id: str
            sender_icon: str
            order_id: str
            order_status: str
            chat_room_id: str
            amount: int
            status: str
            has_password: bool
            money: int
            money_light: int
            raw: dict
        
        p = response["payload"]
        return LinkInfo(
            p["sender"]["displayName"],
            p["sender"]["externalId"],
            p["sender"]["photoUrl"],
            p["pendingP2PInfo"]["orderId"],
            p["orderStatus"],
            p["message"]["chatRoomId"],
            p["pendingP2PInfo"]["amount"],
            p["message"]["data"]["status"],
            p["pendingP2PInfo"]["isSetPasscode"],
            p["message"]["data"]["subWalletSplit"]["senderEmoneyAmount"],
            p["message"]["data"]["subWalletSplit"]["senderPrepaidAmount"],
            response
        )
    
    def accept_link(self, url: str, passcode: str = None):

        if "https://" in url:
            url = url.replace("https://pay.paypay.ne.jp/", "")
        
        info = self.check_link(url)
        if not info or info.order_status != "PENDING":
            return False
        
        payload = {
            "requestId": str(uuid.uuid4()),
            "orderId": info.order_id,
            "verificationCode": url,
            "passcode": passcode,
            "senderMessageId": info.raw["payload"]["message"]["messageId"],
            "senderChannelUrl": info.chat_room_id
        }
        
        response = self.session.post(
            "https://app4.paypay.ne.jp/bff/v2/acceptP2PSendMoneyLink",
            params=self.params,
            headers=self.headers,
            json=payload
        ).json()
        
        return response["header"]["resultCode"] == "S0000"
    
    def reject_link(self, url: str):

        if "https://" in url:
            url = url.replace("https://pay.paypay.ne.jp/", "")
        
        info = self.check_link(url)
        if not info or info.order_status != "PENDING":
            return False
        
        payload = {
            "requestId": str(uuid.uuid4()),
            "orderId": info.order_id,
            "verificationCode": url,
            "senderMessageId": info.raw["payload"]["message"]["messageId"],
            "senderChannelUrl": info.chat_room_id
        }
        
        response = self.session.post(
            "https://app4.paypay.ne.jp/bff/v2/rejectP2PSendMoneyLink",
            params=self.params,
            headers=self.headers,
            json=payload
        ).json()
        
        return response["header"]["resultCode"] == "S0000"
    
    def create_link(self, amount: int, passcode: str = None):

        payload = {
            "requestId": str(uuid.uuid4()),
            "amount": amount,
            "socketConnection": "P2P",
            "theme": "default-sendmoney",
            "source": "sendmoney_home_sns"
        }
        if passcode:
            payload["passcode"] = passcode
        
        response = self.session.post(
            "https://app4.paypay.ne.jp/bff/v2/executeP2PSendMoneyLink",
            params=self.params,
            headers=self.headers,
            json=payload
        ).json()
        
        if response["header"]["resultCode"] != "S0000":
            return None
        
        class CreateLink(NamedTuple):
            link: str
            order_id: str
            chat_room_id: str
            raw: dict
        
        return CreateLink(
            response["payload"]["link"],
            response["payload"]["orderId"],
            response["payload"]["chatRoomId"],
            response
        )
    
    def create_p2pcode(self, amount: int = None):

        payload = {
            "amount": amount,
            "sessionId": str(uuid.uuid4()) if amount else None
        }
        
        response = self.session.post(
            "https://app4.paypay.ne.jp/bff/v1/createP2PCode",
            params=self.params,
            headers=self.headers,
            json=payload
        ).json()
        
        if response["header"]["resultCode"] != "S0000":
            return None
        
        class P2PCode(NamedTuple):
            p2pcode: str
            raw: dict
        
        return P2PCode(response["payload"]["p2pCode"], response)
    
    
    def _webview_authorize(self, request_uri: str):

        self.webview_session.get(
            "https://www.paypay.ne.jp/portal/api/v2/oauth2/authorize",
            params={
                "client_id": "pay2-mobile-app-client",
                "request_uri": request_uri
            },
            headers=self._get_webview_headers()
        )
    
    def _webview_signin_page(self):

        self.webview_session.get(
            "https://www.paypay.ne.jp/portal/oauth2/sign-in",
            params={"client_id": "pay2-mobile-app-client", "mode": "landing"},
            headers=self._get_webview_headers()
        )
    
    def _webview_par_check(self):

        response = self.webview_session.get(
            "https://www.paypay.ne.jp/portal/api/v2/oauth2/par/check",
            headers=self._get_webview_headers(
                "https://www.paypay.ne.jp/portal/oauth2/sign-in?client_id=pay2-mobile-app-client&mode=landing"
            )
        ).json()
        
        if response["header"]["resultCode"] != "S0000":
            raise PayPayLoginError(response)
    
    def _start_2fa_flow(self):

        self.webview_session.post(
            "https://www.paypay.ne.jp/portal/api/v2/oauth2/extension/code-grant/update",
            headers=self._get_webview_headers(
                "https://www.paypay.ne.jp/portal/oauth2/sign-in?client_id=pay2-mobile-app-client&mode=landing"
            ),
            json={}
        )
        
        self.webview_session.post(
            "https://www.paypay.ne.jp/portal/api/v2/oauth2/extension/code-grant/update",
            headers=self._get_webview_headers(
                "https://www.paypay.ne.jp/portal/oauth2/verification-method?client_id=pay2-mobile-app-client&mode=navigation-2fa"
            ),
            json={
                "params": {
                    "extension_id": "user-main-2fa-v1",
                    "data": {
                        "type": "SELECT_FLOW",
                        "payload": {
                            "flow": "OTL",
                            "sign_in_method": "MOBILE",
                            "base_url": "https://www.paypay.ne.jp/portal/oauth2/l"
                        }
                    }
                }
            }
        )
        
        self.webview_session.post(
            "https://www.paypay.ne.jp/portal/api/v2/oauth2/extension/code-grant/side-channel/next-action-polling",
            headers=self._get_webview_headers(
                "https://www.paypay.ne.jp/portal/oauth2/otl-request?client_id=pay2-mobile-app-client&mode=navigation-2fa"
            ),
            json={"waitUntil": "PT5S"}
        )
    
    def _complete_token_exchange(self, code: str):

        headers = self.headers.copy()
        headers.pop("Device-Lock-Type", None)
        headers.pop("Device-Lock-App-Setting", None)
        
        response = self.session.post(
            "https://app4.paypay.ne.jp/bff/v2/oauth2/token",
            params=self.params,
            headers=headers,
            data={
                "clientId": "pay2-mobile-app-client",
                "redirectUri": "paypay://oauth2/callback",
                "code": code,
                "codeVerifier": self.verifier
            }
        ).json()
        
        if response["header"]["resultCode"] != "S0000":
            raise PayPayLoginError(response)
        
        self.access_token = response["payload"]["accessToken"]
        self.refresh_token = response["payload"]["refreshToken"]
        self.headers["Authorization"] = f"Bearer {self.access_token}"
        self.headers["Content-Type"] = "application/json"
        self.headers = PayPayUtils.update_device_headers(self.headers)
        
        return True
    
    def _get_webview_headers(self, referer: str = None) -> dict:

        headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "ja-JP,ja;q=0.9",
            "Cache-Control": "no-cache",
            "Client-Id": "pay2-mobile-app-client",
            "Client-OS-Type": "ANDROID",
            "Client-OS-Version": "29.0.0",
            "Client-Type": "PAYPAYAPP",
            "Client-Version": self.version,
            "Connection": "keep-alive",
            "Content-Type": "application/json",
            "Host": "www.paypay.ne.jp",
            "Origin": "https://www.paypay.ne.jp",
            "Pragma": "no-cache",
            "sec-ch-ua": '"Not A(Brand";v="8", "Chromium";v="132", "Android WebView";v="132")',
            "sec-ch-ua-mobile": "?1",
            "sec-ch-ua-platform": '"Android"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": f"Mozilla/5.0 (Linux; Android 10; SCV38 Build/QP1A.190711.020; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/132.0.6834.163 Mobile Safari/537.36 jp.pay2.app.android/{self.version}",
            "X-Requested-With": "jp.ne.paypay.android.app"
        }
        if referer:
            headers["Referer"] = referer
        return headers
    
    def bypass(self):

        try:
            response = self.session.get(
                "https://app4.paypay.ne.jp/bff/v1/getGlobalServiceStatus",
                params={"payPayLang": "en"},
                headers=self.headers
            ).json()
            
            if response["header"]["resultCode"] != "S0000":
                return False
            
            self.session.post(
                "https://app4.paypay.ne.jp/bff/v3/getHomeDisplayInfo",
                params={"payPayLang": "ja"},
                headers=self.headers,
                json={
                    "excludeMissionBannerInfoFlag": False,
                    "includeBeginnerFlag": False,
                    "includeSkinInfoFlag": False,
                    "networkStatus": "WIFI"
                }
            )
            
            self.session.get(
                "https://app4.paypay.ne.jp/bff/v1/getSearchBar",
                params={"payPayLang": "ja"},
                headers=self.headers
            )
            
            return True
        except:
            return False


if __name__ == "__main__":

    paypay = EnhancedPayPay(access_token="your_access_token_here")
    
    paypay = EnhancedPayPay()
    paypay.login_start("080-1234-5678", "your_password")

    paypay.login_confirm("TK4602")
    
    profile = paypay.get_profile()
    if profile:
        print(f"名前: {profile.name}")
        print(f"ID: {profile.external_user_id}")
    
    balance = paypay.get_balance()
    if balance:
        print(f"残高: {balance.useable_balance}円")
        print(f"マネー: {balance.money}円")
        print(f"マネーライト: {balance.money_light}円")
    
    link = paypay.create_link(amount=100, passcode="1234")
    if link:
        print(f"リンク: {link.link}")-client"
            ),
            json={"code": accept_url}
        )
        
        try:
            data = response.json()
            if data["header"]["resultCode"] != "S0000":
                raise PayPayLoginError(data)
        except:
            raise PayPayNetworkError("日本以外からは接続できません")
        
        response = self.webview_session.post(
            "https://www.paypay.ne.jp/portal/api/v2/oauth2/extension/code-grant/update",
            headers=self._get_webview_headers(
                f"https://www.paypay.ne.jp/portal/oauth2/l?id={accept_url}&client_id=pay2-mobile-app
