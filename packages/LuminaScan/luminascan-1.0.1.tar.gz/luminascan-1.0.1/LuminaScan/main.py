#!/usr/bin/env python3
import requests
import pyfiglet
import colorama
from colorama import Fore, Style
import json
import argparse
import time
from requests.exceptions import (
    MissingSchema,
    InvalidSchema,
    InvalidURL,
    ConnectionError,
    Timeout,
    RequestException
)
parser = argparse.ArgumentParser(
    description="LuminaScan - Simple HTTP Analyzer"
)
alien = pyfiglet.figlet_format("LuminaScan", font="smslant")
print(Fore.GREEN + alien + Style.RESET_ALL)

parser.add_argument("url", help="Target URL")
parser.add_argument("--cookies", action="store_true", help="Show cookies")
parser.add_argument("--headers", action="store_true", help="Show headers")
parser.add_argument("--fingerprint", action="store_true", help="Detect CDN/Fingerprint")
parser.add_argument("--security", action="store_true", help="Analyze security headers")
parser.add_argument("--json", action="store_true", help="Show JSON response")
parser.add_argument("--redirects", action="store_true", help="Show redirects info")
parser.add_argument("--status", action="store_true", help="Show status code")
parser.add_argument("--content", action="store_true", help="Determine if API or Website")
parser.add_argument("--all", action="store_true", help="Show all information")
parser.add_argument("--method", choices=["get", "post", "put", "delete"], default="get", help="HTTP method to use (default: get)")
parser.add_argument("--timeout", default="easy", help="Set delay between requests: easy (1s), medium (3s), hard (5s)")
parser.add_argument(
    "--data",
    help="JSON payload for POST/PUT requests"
)
args = parser.parse_args()

#tempo
val = args.timeout.lower()
try:
    if val == "easy":
        delay = 1
    elif val == "medium":
        delay = 3
    elif val == "hard":
        delay = 5
    else:
        delay = 1
except:
    print("Invalid timeout value, using default of 1 second.")
    delay = 1
# Banner

url = args.url
if not url.startswith(("http://", "https://")):
    url = "http://" + url

# Fingerprint function
def detectar_fingerprint(headers):
    h = {k.lower(): v.lower() for k, v in headers.items()}
    resultado = []

    fingerprints = {
        "Cloudflare": ["cf-ray", "cf-cache-status", ("server", "cloudflare"), "cf-connecting-ip"],
        "AWS (CloudFront / S3)": ["x-amz-cf-id", "x-amz-cf-pop", ("via", "amazon"), ("server", "amazons3")],
        "Google Cloud": ["x-cloud-trace-context", ("server", "google"), ("via", "google")],
        "Azure": ["x-azure-ref", "arr-cookie", ("server", "microsoft-iis")],
        "Fastly": ["x-served-by", ("via", "fastly"), ("x-cache", "hit")],
        "Vercel": ["x-vercel-id", ("server", "vercel")],
        "Netlify": ["x-nf-request-id", ("server", "netlify")]
    }

    for nome, sinais in fingerprints.items():
        score = 0
        for sinal in sinais:
            if isinstance(sinal, tuple):
                chave, valor = sinal
                if chave in h and valor in h[chave]:
                    score += 1
            else:
                if sinal in h:
                    score += 1
        if score >= 2:
            confianca = "High"
        elif score == 1:
            confianca = "Average"
        else:
            continue
        resultado.append(f"{nome} (Trust {confianca})")

    return resultado if resultado else ["Unidentified"]

# Security headers function
def analisar_security_headers(headers):
    security_headers = {
        "content-security-policy", "strict-transport-security", "x-content-type-options",
        "x-frame-options", "x-xss-protection", "referrer-policy", "permissions-policy",
        "cross-origin-resource-policy", "cross-origin-opener-policy", "cross-origin-embedder-policy"
    }
    encontrados = []
    headers_lower = {k.lower(): v for k, v in headers.items()}
    for sec in security_headers:
        if sec in headers_lower:
            encontrados.append(sec)
    total = len(encontrados)
    if total <= 1:
        nivel = "Low"
    elif total <= 3:
        nivel = "Medium"
    else:
        nivel = "High"
    return {"Found": encontrados, "Total": total, "Security Level": nivel}

# User-Agent
ninja = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive"
}

# All flags
if args.all:
    args.cookies = args.headers = args.fingerprint = args.json = args.redirects = args.status = args.security = args.content = True

# HTTP Method with payload input
payload = {}

if args.method.lower() in ["post", "put"]:
    if args.data:
        try:
            payload = json.loads(args.data)
        except json.JSONDecodeError:
            print("Invalid JSON in --data, using empty payload {}")
            payload = {}
    else:
        user_input = input('Enter JSON payload (e.g. {"key":"value"}): ').strip()
        if user_input:
            try:
                payload = json.loads(user_input)
            except json.JSONDecodeError:
                print("Invalid JSON, using empty payload {}")
                payload = {}

# Requests
try:
    time.sleep(delay)

    if args.method.lower() == "get":
        response = requests.get(url, headers=ninja, timeout=4)

    elif args.method.lower() == "post":
        response = requests.post(url, json=payload, headers=ninja, timeout=4)

    elif args.method.lower() == "put":
        response = requests.put(url, json=payload, headers=ninja, timeout=4)

    elif args.method.lower() == "delete":
        response = requests.delete(url, headers=ninja, timeout=4)

except MissingSchema:
    print("[ERROR] Invalid URL format. Please include http:// or https://")
    exit(1)

except InvalidURL:
    print("[ERROR] Malformed URL. Check the target address.")
    exit(1)

except ConnectionError:
    print("[ERROR] Connection failed. Host unreachable or offline.")
    exit(1)

except Timeout:
    print("[ERROR] Request timeout. The server did not respond in time.")
    exit(1)

except RequestException as e:
    print(f"[ERROR] Unexpected request error: {e}")
    exit(1)

print(f"\n-------HTTP METHOD: {args.method.upper()}-------")
print(f"Status: {response.status_code}")
print(f"Response Time: {response.elapsed.total_seconds()}s\n")

# Cookies
if args.cookies:
    time.sleep(delay)
    print(f"\n---------COOKIES---------")
    for c in response.cookies:
        print(f"{c.name} = {c.value}")
    print("\nAll cookies:", response.cookies)
    print(f"[*] Number of cookies: {len(response.cookies)}")
    print(f"[!] Time to receive cookies: {response.elapsed.total_seconds()} seconds")

# Status
if args.status:
    time.sleep(delay)
    print("\n---------STATUS---------")
    try:
        if response.status_code == 200:
            print("[+] Active site/API - 200")
        elif response.status_code == 404:
            print("[!] Site/API Not Found - 404")
        elif response.status_code == 429:
            print("[-] Too Many Requests - 429")
        elif response.status_code == 403:
            print("[$] Site Blocked - 403")
        else:
            print("Unknown status error!!")
    except Exception as e:
        print(f"Error checking status: {e}")
    print(f"[-] Time to receive response: {response.elapsed.total_seconds()} seconds")

# Headers
if args.headers:
    time.sleep(delay)
    print("\n------------HEADERS------------")
    for chave, valor in response.headers.items():
        print(f"[*] Key: {chave}")
        print(f"[!] Value: {valor}")
    print(f"[#] Number of Headers: {len(response.headers)}")

# Fingerprint
if args.fingerprint:
    time.sleep(delay)
    print("\n---------FINGERPRINT---------")
    print(f"Possible CDN/Fingerprint: {', '.join(detectar_fingerprint(response.headers))}")

# JSON
if args.json:
    time.sleep(delay)
    print("\n--------------JSON-----------------")
    try:
        print(json.dumps(response.json(), indent=4))
    except ValueError:
        print("No JSON response found.")

# Redirects
if args.redirects:
    time.sleep(delay)
    print("\n-----------REDIRECT---------------")
    print(f"Final URL after redirects: {response.url}")
    print(f"Number of redirects: {len(response.history)}")
    for resp in response.history:
        print(f"Redirected from {resp.url} with status {resp.status_code}")

# Content type
if args.content:
    time.sleep(delay)
    print("\n----------API OR SITE---------------")
    content_type = response.headers.get("Content-Type", "").lower()
    if "application/json" in content_type:
        print("[+] API detected (JSON response)")
    elif "text/html" in content_type:
        print("[+] Website detected (HTML)")
    else:
        print("[?] Unknown content type")

# Security headers
if args.security:
    time.sleep(delay)
    print("\n-------SECURITY HEADERS-------")
    time.sleep(delay)
    print(analisar_security_headers(response.headers))

print(f"\n[~] Avg response time: {response.elapsed.total_seconds()}s")
print("-----------------------------------")