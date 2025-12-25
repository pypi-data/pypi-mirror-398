from json import dump
from pathlib import Path
from platformdirs import user_config_dir

CONFIG_DIR = Path(user_config_dir("free_grok"))
TXID_FILE = CONFIG_DIR / "txid.json"
GROK_FILE = CONFIG_DIR / "grok.json"
CONFIG_DIR.mkdir(exist_ok=True)
dump({
    "https://grok.com/_next/static/chunks/29589.8ec1f2947a0e205d.js": [
        6,
        14,
        12,
        16
    ],
    "https://grok.com/_next/static/chunks/e628011fd4d67558.js": [
        0,
        2,
        8,
        9
    ],
    "https://grok.com/_next/static/chunks/77ffaef786c38d59.js": [
        13,
        33,
        11,
        36
    ],
    "https://grok.com/_next/static/chunks/444a4d2e0656ce52.js": [
        14,
        10,
        25,
        24
    ],
    "https://grok.com/_next/static/chunks/9e496d2be7115b4d.js": [
        11,
        24,
        38,
        38
    ],
    "https://grok.com/_next/static/chunks/069cbd766e2e100e.js": [
        0,
        37,
        0,
        45
    ],
    "https://grok.com/_next/static/chunks/c1c11f0dd2cadabf.js": [
        25,
        10,
        30,
        26
    ],
    "https://grok.com/_next/static/chunks/720ab0732a942089.js": [
        41,
        6,
        33,
        12
    ],
    "https://grok.com/_next/static/chunks/68f6ef173efbeb67.js": [
        31,
        26,
        18,
        35
    ],
    "https://grok.com/_next/static/chunks/87d576c60e76a1e9.js": [
        18,
        23,
        44,
        33
    ]
}
,TXID_FILE.open('w'))
dump([
  {
    "xsid_script": "static/chunks/444a4d2e0656ce52.js",
    "action_script": "/_next/static/chunks/07efa55314110fbd.js",
    "actions": [
      "7f7a9e476198643fb30f17ab0e0c41f8f2edc18ae7",
      "7f0a06a29ceb599ed2d3901e16b2a1e088d2372deb",
      "7f38fb97af610ff9d28ae27294dc41bd9eca880852"
    ]
  },
  {
    "xsid_script": "static/chunks/9e496d2be7115b4d.js",
    "action_script": "/_next/static/chunks/fcbe5d6b4ae286fe.js",
    "actions": [
      "7fd00a18c007ec926f1136cb558f9ef9f903dcc1f4",
      "7f795a3c3829bb45c6e2d2ad0587c7e039f513a509",
      "7fa94a2c9b7ebcf8874e824d3365d9b9735a7afe34"
    ]
  },
  {
    "xsid_script": "static/chunks/069cbd766e2e100e.js",
    "action_script": "/_next/static/chunks/cb52eeab0fd0e58c.js",
    "actions": [
      "7fffbbcd70e50341926589c4f0ed7ab475afad3321",
      "7fdf5ae16dee580d89683963be28bc62f1603ffea1",
      "7f37fea17b375870e80133012d199e6cdee6201091"
    ]
  },
  {
    "xsid_script": "static/chunks/c1c11f0dd2cadabf.js",
    "action_script": "/_next/static/chunks/bdf3abb63890a18e.js",
    "actions": [
      "7f71f42b11fe0a773c18539575170eb3cda2720fff",
      "7f8159187cdb2e21e48a06256220a8bbf7b1088b34",
      "7fb14bed5522696e9d5cbec5fd92ea7cebee752db0"
    ]
  },
  {
    "xsid_script": "static/chunks/720ab0732a942089.js",
    "action_script": "/_next/static/chunks/dcf3a6315f86c917.js",
    "actions": [
      "7f8b78848a6f7726b96bec61b199a7bdc02e392621",
      "7f1e31eb362d2be64d0ab258d72fc770ecbb261237",
      "7f0c6140a77d46f5696f9b5d4fec00e3165e9bf678"
    ]
  },
  {
    "xsid_script": "static/chunks/68f6ef173efbeb67.js",
    "action_script": "/_next/static/chunks/4114b4b6e0483e8c.js",
    "actions": [
      "7f3749b0c81bd826ca8cc02ccf8009a911410e49f7",
      "7f5e48bfe2a1588dc86c1fe1bf3eac0e2676f55532",
      "7f5341512f3793d10791b2ca628b300aac6ba34b98"
    ]
  },
  {
    "xsid_script": "static/chunks/87d576c60e76a1e9.js",
    "action_script": "/_next/static/chunks/843010bb02f13cde.js",
    "actions": [
      "7fb4349e44719d28ba8da9344e11ab7e5e3b1c474f",
      "7f9a9b0c62c7c8775525be38003aa09725ea709115",
      "7f82eca570c9532c4193e3784a3a017ef7229a3edf"
    ]
  }
],GROK_FILE.open('w'))

LOAD = {'upgrade-insecure-requests': '1',
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
 'priority': 'u=0, i'}
C_REQUEST = {'sec-ch-ua-platform': '"Windows"',
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
 'priority': 'u=1, i'}
CONVERSATION = {'x-xai-request-id': '',
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
 'priority': 'u=1, i'}
