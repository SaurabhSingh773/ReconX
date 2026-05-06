import requests
from urllib.parse import urlparse, parse_qs, unquote
import sys
import re
import time

INTERESTING_KEYWORDS = [
    "admin", "login", "upload", "debug",
    "api", "internal", "test", "backup", "old"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
}


def clean_domain(domain):
    if domain.startswith("http"):
        domain = urlparse(domain).netloc
    return domain.strip("/")


def get_historical_data(domain):
    domain = clean_domain(domain)

    print(f"[+] Fetching historical data for {domain}...\n")

    api_url = "https://web.archive.org/cdx/search/cdx"

    params = {
        "url": f"{domain}/*",
        "output": "json",
        "fl": "original",
        "collapse": "urlkey",
        "limit": "1000"
    }

    urls = set()
    paths = set()
    parameters = set()
    interesting_paths = set()

    for attempt in range(3):
        try:
            response = requests.get(
                api_url,
                params=params,
                headers=HEADERS,
                timeout=(5, 20)
            )

            if response.status_code != 200:
                print(f"[!] Attempt {attempt+1}: Server returned {response.status_code}")
                time.sleep(3)
                continue

            data = response.json()

            for entry in data[1:]:
                full_url = entry[0]

                parsed = urlparse(full_url)
                path = unquote(parsed.path)

                # ---------- FILTERS ----------
                if not path.startswith("/"):
                    continue

                if any(path.endswith(ext) for ext in [
                    ".png", ".jpg", ".jpeg", ".svg", ".gif",
                    ".css", ".js", ".woff", ".woff2", ".ttf", ".ico"
                ]):
                    continue

                if len(path) > 120:
                    continue

                if re.search(r"[<>\"\'\s]", path):
                    continue
                # -----------------------------

                urls.add(full_url)
                paths.add(path)

                # parameters
                query_params = parse_qs(parsed.query)
                for p in query_params:
                    parameters.add(p)

                # interesting endpoints
                for keyword in INTERESTING_KEYWORDS:
                    if keyword in path.lower():
                        interesting_paths.add(path)

            return urls, paths, parameters, interesting_paths

        except KeyboardInterrupt:
            print("\n\n[!] Scan interrupted by user")
            print(f"[+] Collected so far: {len(urls)} URLs")
            return urls, paths, parameters, interesting_paths

        except Exception as e:
            print(f"[!] Attempt {attempt+1} failed: {e}")
            time.sleep(3)

    print("[-] Wayback API unavailable. Try again later.\n")
    return urls, paths, parameters, interesting_paths


if __name__ == "__main__":
    try:
        if len(sys.argv) != 2:
            print("Usage: python hist_recon.py example.com")
            sys.exit(1)

        domain = sys.argv[1]

        urls, paths, params, interesting = get_historical_data(domain)

        print("\n[+] Sample Historical URLs:")
        for u in list(urls)[:10]:
            print(" ", u)

        print("\n[+] Historical Paths:")
        for p in list(paths)[:10]:
            print(" ", p)

        print("\n[+] Parameters Found:")
        for param in params:
            print(" ", param)

        print("\n[!] Interesting Historical Endpoints:")
        for ip in interesting:
            print(" ", ip)

    except KeyboardInterrupt:
        print("\n[!] Program stopped by user")
