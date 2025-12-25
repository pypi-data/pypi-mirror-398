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
from time import time
from free_grok.conf import C_REQUEST, LOAD, TXID_FILE, GROK_FILE, CONVERSATION


# =====================
# utils
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
                js = requests.get(url, impersonate="chrome136").text
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
            c = requests.get(f"https://grok.com{s}", impersonate="chrome136").text
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
# Grok client
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


class Grok:

    def __init__(self, model="grok-3-auto", proxy=None):
        self.session = requests.Session(
            impersonate="chrome136", default_headers=False
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
                yield {"token":t}
            if cid:
                yield {"conversation_id":cid}
            if title:
                yield {"title":title}
            if full_responce:
                yield {"full_responce":full_responce}
            if other_thing:
                yield {"other_thing":other_thing}

        yield {
            "extra_data": {
                "anon_user": self.anon,
                "cookies": self.session.cookies.get_dict(),
                "privateKey": self.keys["privateKey"],
            },
        }
