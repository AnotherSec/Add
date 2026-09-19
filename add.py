#!/usr/bin/env python3

import requests
import urllib3
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

INPUT_FILE  = "input.txt"
OUTPUT_FILE = "hasil.txt"
TIMEOUT     = 20
THREADS     = 50


def strip_scheme(line):
    line = line.strip()
    while line.lower().startswith("https://"):
        line = line[8:]
    while line.lower().startswith("http://"):
        line = line[7:]
    line = line.split("/")[0].strip()
    return line


def load_domains():
    try:
        with open(INPUT_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"[-] File '{INPUT_FILE}' tidak ditemukan!")
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
        return url, r.status_code, time.time() - start, None
    except Exception as e:
        err = type(e).__name__
        if "Timeout" in err:
            err = "timeout"
        elif "Connection" in err or "NameResolution" in err:
            err = "connection/DNS gagal"
        elif "SSLError" in err:
            err = "ssl error (host mungkin hidup)"
        return url, None, time.time() - start, err


def main():
    print("=" * 55)
    print("   Mass HTTP/HTTPS Checker")
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

    print(f"[+] Total {len(urls)} URL akan dicek\n")

    ok_list, fail_list = [], []
    done = 0

    with ThreadPoolExecutor(max_workers=THREADS) as pool:
        futures = {pool.submit(ping_url, u): u for u in urls}
        for fut in as_completed(futures):
            url, status, elapsed, err = fut.result()
            done += 1
            if status is not None:
                ok_list.append(f"{url} [{status}]")
                print(f"[{done}/{len(urls)}] [+] OK   {url} -> {status} ({elapsed:.2f}s)")
            else:
                fail_list.append(f"{url} [FAIL] {err}")
                print(f"[{done}/{len(urls)}] [-] FAIL {url} -> {err}")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("# === OK ===\n")
        f.write("\n".join(ok_list))
        f.write("\n\n# === FAIL ===\n")
        f.write("\n".join(fail_list))

    print("\n=== SUMMARY ===")
    print(f"Hidup/OK : {len(ok_list)}")
    print(f"Mati/FAIL: {len(fail_list)}")
    print(f"Hasil disimpan di: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
