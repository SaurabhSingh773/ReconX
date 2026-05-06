import os
import sys
import dns.resolver
import random
import string
from concurrent.futures import ThreadPoolExecutor, as_completed


# DNS resolver
resolver = dns.resolver.Resolver()
resolver.nameservers = ["1.1.1.1", "8.8.8.8", "9.9.9.9"]
resolver.timeout = 1
resolver.lifetime = 1


# Load wordlist
def load_wordlist():
    base_dir = os.path.dirname(__file__)
    file_path = os.path.join(base_dir, "wordlist.txt")

    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            return [line.strip() for line in f if line.strip()]

    return ["admin", "api", "dev", "test", "mail", "staging"]


# Wildcard detection
def detect_wildcard(domain):
    test = ''.join(random.choices(string.ascii_lowercase, k=12)) + "." + domain
    try:
        answers = resolver.resolve(test, "A")
        return answers[0].to_text()
    except:
        return None


# Check subdomain
def check_subdomain(subdomain, wildcard_ip):
    try:
        answers = resolver.resolve(subdomain, "A")
        ip = answers[0].to_text()

        if wildcard_ip and ip == wildcard_ip:
            return None

        return subdomain

    except:
        return None


# Main function
def subdomain_enum(domain, limit=None, threads=150):

    print(f"\n[+] Starting Subdomain Scan for {domain}\n")

    wordlist = load_wordlist()

    if limit is not None:
        if limit == 0:
            print("[+] Full scan selected\n")
        else:
            print(f"[+] Limiting to {limit} entries\n")
            wordlist = wordlist[:limit]

    wildcard_ip = detect_wildcard(domain)

    if wildcard_ip:
        print(f"[!] Wildcard DNS detected → {wildcard_ip}\n")
    else:
        print("[+] No wildcard DNS detected\n")

    total = len(wordlist)
    completed = 0
    found = set()

    try:
        with ThreadPoolExecutor(max_workers=threads) as executor:

            futures = [
                executor.submit(check_subdomain, f"{word}.{domain}", wildcard_ip)
                for word in wordlist
            ]

            for future in as_completed(futures):
                completed += 1
                percent = (completed / total) * 100

                # update progress every 100 requests
                if completed % 100 == 0 or completed == total:
                    sys.stdout.write(f"\rProgress: {completed}/{total} ({percent:.2f}%)")
                    sys.stdout.flush()

                result = future.result()
                if result:
                    found.add(result)

    except KeyboardInterrupt:
        print("\n\n[!] Scan interrupted by user")
        print(f"[+] Progress: {completed}/{total}")
        print(f"[+] Subdomains found: {len(found)}")
        return found

    print("\n")

    # print results at end (faster than live printing)
    if found:
        print("[+] Found Subdomains:")
        for sub in sorted(found):
            print(sub)

    return found


# CLI
if __name__ == "__main__":

    args = sys.argv[1:]
    limit = None

    if "--limit" in args:
        try:
            idx = args.index("--limit")
            limit = int(args[idx + 1])
        except:
            print("Invalid limit value")
            sys.exit()

    domain = input("Enter domain (example.com): ").strip()

    if domain.startswith("http"):
        from urllib.parse import urlparse
        domain = urlparse(domain).netloc

    if limit is None:
        try:
            limit = int(input("Enter limit (0 = full, default 5000): ") or 5000)
        except:
            limit = 5000

    if limit == 0:
        limit = None

    results = subdomain_enum(domain, limit=limit)

    print(f"\n[+] Total Found: {len(results)}")
