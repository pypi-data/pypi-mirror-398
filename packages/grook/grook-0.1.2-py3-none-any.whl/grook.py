#!/usr/bin/env python3
"""
Grook - Simple Python client for free Grok access via public endpoint
"""

# =====================
# Imports
# =====================

from curl_cffi import requests, CurlMime
from bs4 import BeautifulSoup
from coincurve import PrivateKey
from base64 import b64encode, b64decode
from hashlib import sha256
from secrets import token_hex, token_bytes
from uuid import uuid4
from math import floor, copysign, pi, cos, sin
from json import dumps, loads, load, dump
from re import findall, sub, search
from random import random
from struct import pack
from time import time, sleep
from pathlib import Path
from platformdirs import user_config_dir
import sys
import argparse


# =====================
# Configuration
# =====================

CONFIG_DIR = Path(user_config_dir("grook"))
TXID_FILE = CONFIG_DIR / "txid.json"
GROK_FILE = CONFIG_DIR / "grok.json"
CONFIG_DIR.mkdir(exist_ok=True)

# Initialize config files if they don't exist
if not TXID_FILE.exists():
    dump({
        "https://grok.com/_next/static/chunks/29589.8ec1f2947a0e205d.js": [6, 14, 12, 16],
        "https://grok.com/_next/static/chunks/e628011fd4d67558.js": [0, 2, 8, 9],
        "https://grok.com/_next/static/chunks/77ffaef786c38d59.js": [13, 33, 11, 36],
        "https://grok.com/_next/static/chunks/444a4d2e0656ce52.js": [14, 10, 25, 24],
        "https://grok.com/_next/static/chunks/9e496d2be7115b4d.js": [11, 24, 38, 38],
        "https://grok.com/_next/static/chunks/069cbd766e2e100e.js": [0, 37, 0, 45],
        "https://grok.com/_next/static/chunks/c1c11f0dd2cadabf.js": [25, 10, 30, 26],
        "https://grok.com/_next/static/chunks/720ab0732a942089.js": [41, 6, 33, 12],
        "https://grok.com/_next/static/chunks/68f6ef173efbeb67.js": [31, 26, 18, 35],
        "https://grok.com/_next/static/chunks/87d576c60e76a1e9.js": [18, 23, 44, 33]
    }, TXID_FILE.open('w'))

if not GROK_FILE.exists():
    dump([
        {
            "xsid_script": "static/chunks/444a4d2e0656ce52.js",
            "action_script": "/_next/static/chunks/07efa55314110fbd.js",
            "actions": ["7f7a9e476198643fb30f17ab0e0c41f8f2edc18ae7", "7f0a06a29ceb599ed2d3901e16b2a1e088d2372deb", "7f38fb97af610ff9d28ae27294dc41bd9eca880852"]
        },
        {
            "xsid_script": "static/chunks/9e496d2be7115b4d.js",
            "action_script": "/_next/static/chunks/fcbe5d6b4ae286fe.js",
            "actions": ["7fd00a18c007ec926f1136cb558f9ef9f903dcc1f4", "7f795a3c3829bb45c6e2d2ad0587c7e039f513a509", "7fa94a2c9b7ebcf8874e824d3365d9b9735a7afe34"]
        },
        {
            "xsid_script": "static/chunks/069cbd766e2e100e.js",
            "action_script": "/_next/static/chunks/cb52eeab0fd0e58c.js",
            "actions": ["7fffbbcd70e50341926589c4f0ed7ab475afad3321", "7fdf5ae16dee580d89683963be28bc62f1603ffea1", "7f37fea17b375870e80133012d199e6cdee201091"]
        },
        {
            "xsid_script": "static/chunks/c1c11f0dd2cadabf.js",
            "action_script": "/_next/static/chunks/bdf3abb63890a18e.js",
            "actions": ["7f71f42b11fe0a773c18539575170eb3cda2720fff", "7f8159187cdb2e21e48a06256220a8bbf7b1088b34", "7fb14bed5522696e9d5cbec5fd92ea7cebee752db0"]
        },
        {
            "xsid_script": "static/chunks/720ab0732a942089.js",
            "action_script": "/_next/static/chunks/dcf3a6315f86c917.js",
            "actions": ["7f8b78848a6f7726b96bec61b199a7bdc02e392621", "7f1e31eb362d2be64d0ab258d72fc770ecbb261237", "7f0c6140a77d46f5696f9b5d4fec00e3165e9bf678"]
        },
        {
            "xsid_script": "static/chunks/68f6ef173efbeb67.js",
            "action_script": "/_next/static/chunks/4114b4b6e0483e8c.js",
            "actions": ["7f3749b0c81bd826ca8cc02ccf8009a911410e49f7", "7f5e48bfe2a1588dc86c1fe1bf3eac0e2676f55532", "7f5341512f3793d10791b2ca628b300aac6ba34b98"]
        },
        {
            "xsid_script": "static/chunks/87d576c60e76a1e9.js",
            "action_script": "/_next/static/chunks/843010bb02f13cde.js",
            "actions": ["7fb4349e44719d28ba8da9344e11ab7e5e3b1c474f", "7f9a9b0c62c7c8775525be38003aa09725ea709115", "7f82eca570c9532c4193e3784a3a017ef7229a3edf"]
        }
    ], GROK_FILE.open('w'))

LOAD = {
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'sec-ch-ua': '"Google Chrome";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-site': 'none',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-user': '?1',
    'sec-fetch-dest': 'document',
    'accept-encoding': 'gzip, deflate, br, zstd',
    'accept-language': 'de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7',
    'priority': 'u=0, i'
}

C_REQUEST = {
    'sec-ch-ua-platform': '"Windows"',
    'next-action': '',
    'sec-ch-ua': '"Google Chrome";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'next-router-state-tree': '%5B%22%22%2C%7B%22children%22%3A%5B%22c%22%2C%7B%22children%22%3A%5B%5B%22slug%22%2C%22%22%2C%22oc%22%5D%2C%7B%22children%22%3A%5B%22__PAGE__%22%2C%7B%7D%2Cnull%2Cnull%5D%7D%2Cnull%2Cnull%5D%7D%2Cnull%2Cnull%5D%7D%2Cnull%2Cnull%2Ctrue%5D',
    'baggage': '',
    'sentry-trace': '',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
    'accept': 'text/x-component',
    'content-type': 'text/plain;charset=UTF-8',
    'origin': 'https://grok.com',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-mode': 'cors',
    'sec-fetch-dest': 'empty',
    'referer': 'https://grok.com/c',
    'accept-encoding': 'gzip, deflate, br, zstd',
    'accept-language': 'de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7',
    'priority': 'u=1, i'
}

CONVERSATION = {
    'x-xai-request-id': '',
    'sec-ch-ua-platform': '"Windows"',
    'sec-ch-ua': '"Google Chrome";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'baggage': '',
    'sentry-trace': '',
    'traceparent': '',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
    'content-type': 'application/json',
    'x-statsig-id': '',
    'accept': '*/*',
    'origin': 'https://grok.com',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-mode': 'cors',
    'sec-fetch-dest': 'empty',
    'referer': 'https://grok.com/',
    'accept-encoding': 'gzip, deflate, br, zstd',
    'accept-language': 'de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7',
    'priority': 'u=1, i'
}


# =====================
# Utils
# =====================

def between(text, a, b):
    return text.split(a)[1].split(b)[0]


def fix_order(headers, base):
    ordered = {}
    for k in base:
        if k in headers:
            ordered[k] = headers[k]
    for k, v in headers.items():
        if k not in ordered:
            ordered[k] = v
    return ordered


# =====================
# Anon crypto
# =====================

class Anon:

    @staticmethod
    def public_key(priv):
        return list(PrivateKey(priv).public_key.format(compressed=True))

    @staticmethod
    def generate_keys():
        priv = token_bytes(32)
        return {
            "privateKey": b64encode(priv).decode(),
            "userPublicKey": Anon.public_key(priv),
        }

    @staticmethod
    def sign_challenge(challenge, key):
        pk = PrivateKey(b64decode(key))
        sig = pk.sign_recoverable(
            sha256(challenge).digest(), hasher=None
        )[:64]
        return {
            "challenge": b64encode(challenge).decode(),
            "signature": b64encode(sig).decode(),
        }


# =====================
# Signature (AS-IS)
# =====================

class Signature:

    @staticmethod
    def _h(x, p, c, e):
        f = ((x * (c - p)) / 255.0) + p
        if e:
            return floor(f)
        r = round(float(f), 2)
        return 0.0 if r == 0.0 else r

    @staticmethod
    def cubicBezierEased(t, x1, y1, x2, y2):
        def bez(u):
            o = 1.0 - u
            return (
                3 * o * o * u * x1 + 3 * o * u * u * x2 + u * u * u,
                3 * o * o * u * y1 + 3 * o * u * u * y2 + u * u * u,
            )

        lo, hi = 0.0, 1.0
        for _ in range(80):
            m = (lo + hi) / 2
            if bez(m)[0] < t:
                lo = m
            else:
                hi = m
        return bez((lo + hi) / 2)[1]

    @staticmethod
    def xa(svg):
        out = []
        for p in svg[9:].split("C"):
            c = sub(r"[^\d]+", " ", p).strip()
            out.append([int(x) for x in c.split()] if c else [0])
        return out

    @staticmethod
    def tohex(num):
        r = round(float(num), 2)
        if r == 0.0:
            return "0"
        s = "-" if copysign(1.0, r) < 0 else ""
        a = abs(r)
        i = int(floor(a))
        f = a - i
        if f == 0.0:
            return s + format(i, "x")
        out = []
        for _ in range(20):
            f *= 16
            d = int(f)
            out.append(format(d, "x"))
            f -= d
            if abs(f) < 1e-12:
                break
        return s + format(i, "x") + "." + "".join(out).rstrip("0")

    @staticmethod
    def simulateStyle(v, c):
        t = round(c / 10) * 10 / 4096
        cp = [Signature._h(x, -1 if i % 2 else 0, 1, False)
              for i, x in enumerate(v[7:])]
        y = Signature.cubicBezierEased(t, *cp[:4])

        s, e = v[:3], v[3:6]
        r = round(s[0] + (e[0] - s[0]) * y)
        g = round(s[1] + (e[1] - s[1]) * y)
        b = round(s[2] + (e[2] - s[2]) * y)

        ang = Signature._h(v[6], 60, 360, True) * y * pi / 180
        return {
            "color": f"rgb({r}, {g}, {b})",
            "transform": f"matrix({cos(ang)}, {sin(ang)}, {-sin(ang)}, {cos(ang)}, 0, 0)",
        }

    @staticmethod
    def xs(b, svg, x):
        arr = list(b)
        idx = arr[x[0]] % 16
        c = (arr[x[1]] % 16) * (arr[x[2]] % 16) * (arr[x[3]] % 16)
        vals = Signature.xa(svg)[idx]
        k = Signature.simulateStyle(vals, c)
        s = k["color"] + k["transform"]
        h = "".join(Signature.tohex(float(n))
                    for n in findall(r"[\d\.\-]+", s))
        return h.replace(".", "").replace("-", "")

    @staticmethod
    def generate_sign(path, method, verif, svg, nums):
        n = int(time() - 1682924400)
        r = b64decode(verif)
        o = Signature.xs(r, svg, nums)

        msg = "!".join([method, path, str(n)]) + "obfiowerehiring" + o
        d = sha256(msg.encode()).digest()[:16]

        prefix = int(floor(random()))
        raw = bytes([prefix]) + r + pack("<I", n) + d + b"\x03"
        arr = bytearray(raw)
        for i in range(1, len(arr)):
            arr[i] ^= arr[0]
        return b64encode(bytes(arr)).decode().replace("=", "")


# =====================
# Parser
# =====================

class Parser:
    mapping = {}
    grok_mapping = []
    _map_loaded = False
    _grok_loaded = False

    @classmethod
    def _load_map(cls):
        if not cls._map_loaded and TXID_FILE.exists():
            cls.mapping = load(TXID_FILE.open())
            cls._map_loaded = True

    @classmethod
    def _load_grok(cls):
        if not cls._grok_loaded and GROK_FILE.exists():
            cls.grok_mapping = load(GROK_FILE.open())
            cls._grok_loaded = True

    @staticmethod
    def parse_values(html, loading, script_id):
        Parser._load_map()
        svg = findall(r'"d":"(M[^"]{200,})"', html)[int(loading[-1])]

        if script_id:
            if script_id == "ondemand.s":
                url = (
                    "https://abs.twimg.com/responsive-web/client-web/ondemand.s."
                    + between(html, f'"{script_id}":"', '"')
                    + "a.js"
                )
            else:
                url = f"https://grok.com/_next/{script_id}"

            if url not in Parser.mapping:
                js = requests.get(url, impersonate="chrome").text
                Parser.mapping[url] = [
                    int(x) for x in findall(r"x\[(\d+)\]\s*,\s*16", js)
                ]
                dump(Parser.mapping, TXID_FILE.open("w"))

            return svg, Parser.mapping[url]

        return svg

    @staticmethod
    def get_anim(html):
        v = between(html, '"name":"grok-site-verification","content":"', '"')
        arr = list(b64decode(v))
        return v, "loading-x-anim-" + str(arr[5] % 4)

    @staticmethod
    def parse_grok(scripts):
        Parser._load_grok()

        for g in Parser.grok_mapping:
            if g["action_script"] in scripts:
                return g["actions"], g["xsid_script"]

        s1 = s2 = a = None
        for s in scripts:
            c = requests.get(f"https://grok.com{s}", impersonate="chrome").text
            if "anonPrivateKey" in c:
                s1, a = c, s
            elif "880932)" in c:
                s2 = c

        acts = findall(r'createServerReference\)\("([a-f0-9]+)"', s1)
        xs = search(
            r'"(static/chunks/[^"]+\.js)"[^}]*?\(880932\)', s2
        ).group(1)

        Parser.grok_mapping.append({
            "action_script": a,
            "xsid_script": xs,
            "actions": acts,
        })
        dump(Parser.grok_mapping, GROK_FILE.open("w"), indent=2)
        return acts, xs


# =====================
# Internal Grok Engine
# =====================

MODEL_MAP = {
    "grok-3-auto": ("MODEL_MODE_AUTO", "auto"),
    "grok-3-fast": ("MODEL_MODE_FAST", "fast"),
    "grok-4": ("MODEL_MODE_EXPERT", "expert"),
    "grok-4-mini-thinking-tahoe": (
        "MODEL_MODE_GROK_4_MINI_THINKING",
        "grok-4-mini-thinking",
    ),
}


class _GrokEngine:
    """Internal engine for Grok communication"""

    def __init__(self, model="grok-3-auto", proxy=None):
        self.session = requests.Session(
            impersonate="chrome", default_headers=False
        )
        if proxy:
            self.session.proxies = {"all": proxy}

        self.model = model
        self.model_mode, self.mode = MODEL_MAP.get(
            model, MODEL_MAP["grok-3-auto"]
        )
        self.keys = Anon.generate_keys()
        self.c_run = 0

    def start_convo(self, message):
        self.session.headers = LOAD
        r = self.session.get("https://grok.com/c")
        self.session.cookies.update(r.cookies)

        scripts = [
            s["src"]
            for s in BeautifulSoup(r.text, "html.parser")
            .find_all("script", src=True)
            if s["src"].startswith("/_next/static/chunks/")
        ]

        self.actions, self.xsid = Parser.parse_grok(scripts)
        self.baggage = between(r.text, '<meta name="baggage" content="', '"')
        self.trace = between(r.text, '<meta name="sentry-trace" content="', '-')

        for act in self.actions[:3]:
            self.session.headers = fix_order({
                **C_REQUEST,
                "baggage": self.baggage,
                "next-action": act,
                "sentry-trace": f"{self.trace}-{uuid4().hex[:16]}-0",
            }, C_REQUEST)

            if self.c_run == 0:
                self.session.headers.pop("content-type", None)
                m = CurlMime()
                m.addpart(
                    name="1",
                    data=bytes(self.keys["userPublicKey"]),
                    filename="blob",
                    content_type="application/octet-stream",
                )
                m.addpart(name="0", data='[{"userPublicKey":"$o1"}]')
                r = self.session.post("https://grok.com/c", multipart=m)
                self.anon = between(r.text, '{"anonUserId":"', '"')

            else:
                payload = (
                    [{"anonUserId": self.anon}]
                    if self.c_run == 1
                    else [{"anonUserId": self.anon, **self.challenge}]
                )
                r = self.session.post("https://grok.com/c", data=dumps(payload))

            if self.c_run == 1:
                h = r.content.hex()
                s = h.find("3a6f38362c")
                if s != -1:
                    chal = bytes.fromhex(h[s + 10:h.find("313a", s)])
                    self.challenge = Anon.sign_challenge(
                        chal, self.keys["privateKey"]
                    )

            if self.c_run == 2:
                self.verif, self.anim = Parser.get_anim(r.text)
                self.svg, self.nums = Parser.parse_values(
                    r.text, self.anim, self.xsid
                )

            self.c_run += 1

        xsid = Signature.generate_sign(
            "/rest/app-chat/conversations/new",
            "POST",
            self.verif,
            self.svg,
            self.nums,
        )

        self.session.headers = fix_order({
            **CONVERSATION,
            "baggage": self.baggage,
            "sentry-trace": f"{self.trace}-{uuid4().hex[:16]}-0",
            "x-statsig-id": xsid,
            "x-xai-request-id": str(uuid4()),
            "traceparent": f"00-{token_hex(16)}-{token_hex(8)}-00",
        }, CONVERSATION)

        r = self.session.post(
                "https://grok.com/rest/app-chat/conversations/new",
                json={
                    "message": message,
                    "modelName": self.model,
                    "modelMode": self.model_mode,
                },
                stream=True,
                timeout=9999,
            )

        for line in r.iter_lines():
            if not line:
                continue
            if isinstance(line, bytes):
                try:
                    line = line.decode("utf-8", errors="ignore")
                except Exception:
                    continue
            try:
                d = loads(line)
            except Exception:
                continue

            result = d.get("result", {})
            t = result.get("response", {}).get("token")
            cid = result.get("conversation", {}).get("conversationId")
            title = result.get("title", {}).get("newTitle")
            full_responce = result.get("response", {}).get("modelResponse")
            other_thing = result.get("response", {}).get("finalMetadata")
            if t:
                yield {"token": t}
            if cid:
                yield {"conversation_id": cid}
            if title:
                yield {"title": title}
            if full_responce:
                yield {"full_responce": full_responce}
            if other_thing:
                yield {"other_thing": other_thing}

        yield {
            "extra_data": {
                "anon_user": self.anon,
                "cookies": self.session.cookies.get_dict(),
                "privateKey": self.keys["privateKey"],
            },
        }


# =====================
# Public API: Grook Class
# =====================

class Grook:
    """
    Simple Python client for free Grok access via public endpoint
    
    Usage:
        # One-shot query (Grok-3 Auto by default)
        print(Grook().ask("Tell me a joke"))
        
        # Use different model
        print(Grook(model="grok-4").ask("Explain quantum computing"))
        
        # With streaming
        bot = Grook(stream=True)
        bot.ask("Write a story about AI")
    """
    
    def __init__(self, model="grok-3-auto", stream=False, proxy=None):
        """
        Initialize Grook client
        
        Args:
            model: Model to use - "grok-3-auto" (default), "grok-3-fast", 
                   "grok-4", "grok-4-mini-thinking-tahoe"
            stream: Enable token-by-token streaming output
            proxy: Optional proxy URL
        """
        self.model = model
        self.stream_mode = stream
        self.proxy = proxy
        
    def ask(self, message, max_retries=3):
        """
        Send a message and get response
        
        Args:
            message: Your question or prompt
            max_retries: Number of retry attempts on failure
            
        Returns:
            Complete response text, or None if failed
        """
        for attempt in range(1, max_retries + 1):
            full_response = ""
            success = False
            
            try:
                engine = _GrokEngine(model=self.model, proxy=self.proxy)
                
                for item in engine.start_convo(message):
                    if 'token' in item:
                        token = item['token']
                        if self.stream_mode:
                            print(token, end='', flush=True)
                        full_response += token
                    
                    if 'full_responce' in item:
                        success = True
            
            except Exception as e:
                if attempt == max_retries:
                    print(f"\nError: {e}", file=sys.stderr)
                continue
            
            if success and full_response.strip():
                if self.stream_mode:
                    print()  # New line after streaming
                return full_response
            
            if attempt < max_retries:
                sleep(1)
        
        return None


# =====================
# CLI Interface
# =====================

def main():
    parser = argparse.ArgumentParser(
        description='Grook - Free access to Grok AI models',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  grook                                    # Interactive chat (Grok-3 Auto)
  grook --model grok-4                     # Use Grok-4 model
  grook --stream                           # Token-by-token streaming
  grook "Hello, who are you?"              # One-shot message
  grook --model grok-4 --stream            # All features combined
        """
    )
    
    parser.add_argument(
        'message',
        nargs='?',
        help='Send a single message and exit'
    )
    
    parser.add_argument(
        '--model',
        choices=['grok-3-auto', 'grok-3-fast', 'grok-4', 'grok-4-mini-thinking-tahoe'],
        default='grok-3-auto',
        help='Model: grok-3-auto (default), grok-3-fast, grok-4, grok-4-mini-thinking-tahoe'
    )
    
    parser.add_argument(
        '--stream',
        action='store_true',
        help='Show response token-by-token (streaming)'
    )
    
    args = parser.parse_args()
    
    # One-shot mode
    if args.message:
        bot = Grook(model=args.model, stream=args.stream)
        response = bot.ask(args.message)
        if response and not args.stream:
            print(response)
        sys.exit(0 if response else 1)
    
    # Interactive mode
    print(f"Grook Interactive Chat - Model: {args.model}")
    print("Type 'exit' or 'quit' to end the conversation\n")
    
    bot = Grook(model=args.model, stream=args.stream)
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            if user_input.lower() in ['exit', 'quit']:
                print("Goodbye!")
                break
                
            if not user_input:
                continue
            
            print("Grook: ", end='', flush=True)
            response = bot.ask(user_input)
            
            if response and not args.stream:
                print(response)
            elif not response:
                print("Failed to get response. Please try again.")
            
            print()  # Extra newline for readability
            
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except EOFError:
            print("\nGoodbye!")
            break


if __name__ == "__main__":
    main()
