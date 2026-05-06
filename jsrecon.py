import requests
import sys
import re
import urllib3
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
}
endpoint_regex = r'''(?:"|')((?:\/|https?:\/\/)[^"']+)(?:"|')'''


# Normalize URL
def normalize_url(url):
    if not url.startswith("http"):
        return "https://" + url
    return url


# Crawl site (multi-depth)
def crawl_site(url, max_depth=2):
    visited = set()
    to_visit = [url]

    urls = set()
    js_files = set()
    inline_scripts = []

    for _ in range(max_depth):
        next_round = []

        for link in to_visit:
            if link in visited:
                continue

            visited.add(link)

            try:
                r = requests.get(link, headers=HEADERS, timeout=10)
                soup = BeautifulSoup(r.text, "html.parser")

                # Extract links
                for a in soup.find_all("a", href=True):
                    full = urljoin(url, a["href"])
                    if urlparse(full).netloc == urlparse(url).netloc:
                        urls.add(full)
                        next_round.append(full)

                # Extract JS files
                for script in soup.find_all("script", src=True):
                    js_url = urljoin(url, script["src"])
                    js_files.add(js_url)

                # Extract inline JS
                for script in soup.find_all("script"):
                    if script.string:
                        inline_scripts.append(script.string)

            except:
                continue

        to_visit = next_round

    return urls, js_files, inline_scripts


# Extract endpoints from any text (JS/HTML)
def extract_endpoints_from_text(text, domain):
    endpoints = set()

    matches = re.findall(endpoint_regex, text)

    for m in matches:

        if m.startswith("//"):
            continue

        if any(m.endswith(ext) for ext in [
            ".css", ".js", ".png", ".jpg", ".jpeg", ".svg", ".woff", ".ttf"
        ]):
            continue

        if len(m) < 3:
            continue

        if m.startswith("/"):
            endpoints.add(m)

        elif domain in m:
            endpoints.add(m)

    return endpoints


# 🔥 Compatibility wrapper (OLD NAME kept)
def extract_endpoints(js_url, domain):
    endpoints = set()

    try:
        r = requests.get(js_url, headers=HEADERS, timeout=10, verify=False)
        endpoints.update(extract_endpoints_from_text(r.text, domain))
    except:
        pass

    return endpoints


# CLI execution
def main():

    if len(sys.argv) != 2:
        print("Usage: python3 jsrecon.py https://example.com")
        sys.exit(1)

    target = normalize_url(sys.argv[1])
    domain = urlparse(target).netloc

    print(f"\n[+] Crawling: {target}\n")

    urls, js_files, inline_scripts = crawl_site(target)

    print("[+] JS Files Found:")
    for j in js_files:
        print(" ", j)

    print("\n[+] Extracting Endpoints...\n")

    all_endpoints = set()

    # JS files
    for js in js_files:
        all_endpoints.update(extract_endpoints(js, domain))

    # Inline JS
    for script in inline_scripts:
        all_endpoints.update(extract_endpoints_from_text(script, domain))

    # HTML links
    for u in urls:
        all_endpoints.update(extract_endpoints_from_text(u, domain))

    print("\n[+] Endpoints Found:")
    for ep in sorted(all_endpoints):
        print(" ", ep)


if __name__ == "__main__":
    main()
