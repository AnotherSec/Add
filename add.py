#!/usr/bin/env python3

import requests
import urllib3
import sys
import time
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

INPUT_FILE  = "input.txt"    
OUTPUT_FILE = "hasil.txt"    
TIMEOUT     = 10             
THREADS     = 20             


def strip_scheme(line):
    line = line.strip()
    for scheme in ("https://", "http://", "HTTPS://", "HTTP://"):
        while line.lower().startswith(scheme.lower()):
            line = line[len(scheme):]
    
    line = line.split("/")[0].strip()
    return line


def load_domains():
    
    try:
        with open(INPUT_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"[-] File '{INPUT_FILE}' tidak ditemukan!")
        print("    Buat file input.txt isi daftar domain, 1 domain per baris.")
        sys.exit(1)

    domains = []
    for line in lines:
        clean = strip_scheme(line)
        if clean and clean not in domains:
            domains.append(clean)
    return domains


def ping_url(url):
    
    start = time.time()
    try:
        headers = {"User-Agent": "Mozilla/5.0 MassChecker/1.0"}
        r = requests.get(url, headers=headers, timeout=TIMEOUT,
                         verify=False, allow_redirects=True)
        elapsed = time.time() - start
        return url, r.status_code, elapsed, None
    except requests.exceptions.SSLError:
      
        try:
            host = url.split("//")[1].split("/")[0].split(":")[0]
            socket.create_connection((host, 443), timeout=5).close()
            return url, "SSL-ERR(host hidup)", time.time() - start, None
        except Exception as e:
            return url, None, time.time() - start, str(e)
    except requests.exceptions.ConnectionError as e:
        return url, None, time.time() - start, "connection refused/DNS gagal"
    except requests.exceptions.Timeout:
        return url, None, time.time() - start, "timeout"
    except Exception as e:
        return url, None, time.time() - start, str(e)[:80]


def main():
    print("=" * 55)
    print("   Mass HTTP/HTTPS Checker (strip & re-add scheme)")
    print("=" * 55)

    domains = load_domains()
    if not domains:
        print("[-] File input kosong. Keluar.")
        sys.exit(1)

    print(f"[+] {len(domains)} domain unik dimuat dari {INPUT_FILE}")

    urls = []
    for d in domains:
        urls.append(f"https://{d}")
        urls.append(f"http://{d}")

    print(f"[+] Total {len(urls)} URL akan dicek "
          f"({len(domains)} https + {len(domains)} http)\n")

    ok_list, fail_list = [], []
    done = 0

    with ThreadPoolExecutor(max_workers=THREADS) as pool:
        futures = {pool.submit(ping_url, u): u for u in urls}
        for fut in as_completed(futures):
            url, status, elapsed, err = fut.result()
            done += 1
            if status is not None:
