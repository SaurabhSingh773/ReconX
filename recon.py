import sys
from urllib.parse import urlparse
from colorama import Fore, Style, init

init(autoreset=True)

from subdomain_enum import subdomain_enum
from jsrecon import crawl_site, extract_endpoints, extract_endpoints_from_text
from hist_recon import get_historical_data
from http_scan import check


# Banner
def banner():
    print(Fore.CYAN + r"""
██████╗ ███████╗ ██████╗ ██████╗ ███╗   ██╗██╗  ██╗
██╔══██╗██╔════╝██╔════╝██╔═══██╗████╗  ██║╚██╗██╔╝
██████╔╝█████╗  ██║     ██║   ██║██╔██╗ ██║ ╚███╔╝ 
██╔══██╗██╔══╝  ██║     ██║   ██║██║╚██╗██║ ██╔██╗ 
██║  ██║███████╗╚██████╗╚██████╔╝██║ ╚████║██╔╝ ██╗
╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝╚═╝  ╚═╝

        ReconX v1.0 - Advanced Recon Toolkit
        Author: Team_AXE
""" + Style.RESET_ALL)


# Fix URL
def fix_url(target):
    if not target.startswith("http"):
        return "http://" + target
    return target


# Extract domain correctly (NO trimming)
def get_domain(target):
    parsed = urlparse(target)
    return parsed.netloc or target


# JS Recon
def js_recon(target):
    print(Fore.YELLOW + "\n[+] Running JS Recon...\n")

    target = fix_url(target)
    domain = get_domain(target)

    urls, js_files, inline_scripts = crawl_site(target)
    all_endpoints = set()

    for js in js_files:
        all_endpoints.update(extract_endpoints(js, domain))

    for script in inline_scripts:
        all_endpoints.update(extract_endpoints_from_text(script, domain))

    for u in urls:
        all_endpoints.update(extract_endpoints_from_text(u, domain))

    print(Fore.GREEN + "\n[+] JS Endpoints Found:")
    for ep in sorted(all_endpoints):
        print(ep)

    return all_endpoints


# Save output
def save_output(filename, data):
    with open(filename, "w") as f:
        for item in data:
            f.write(str(item) + "\n")
    print(Fore.GREEN + f"\n[+] Results saved to {filename}")


# Full Recon
def run_all(target, output_file=None):
    target = fix_url(target)
    domain = get_domain(target)

    print("\n========== FULL RECON ==========\n")

    from subdomain_enum import load_wordlist
    wordlist_size = len(load_wordlist())

    try:
        limit = int(input(f"Enter subdomain limit (0 = full, max {wordlist_size}, default 5000): ") or 5000)
    except:
        limit = 5000

    if limit == 0:
        limit = None

    subs = subdomain_enum(domain, limit=limit)
    js_eps = js_recon(target)

    urls, paths, params, interesting = get_historical_data(domain)

    print("\n[+] Historical Paths:")
    for p in paths:
        print(p)

    print("\n[+] Parameters:")
    for param in params:
        print(param)

    print("\n[+] HTTP Security Scan:")
    check(domain)

    if output_file:
        save_output(output_file, subs)


# CLI args
def parse_args():
    output = None

    if "--output" in sys.argv:
        try:
            idx = sys.argv.index("--output")
            output = sys.argv[idx + 1]
        except:
            print("Invalid output file")
            sys.exit()

    return output


def main():
    banner()
    output_file = parse_args()

    while True:
        print(Fore.CYAN + "\n" + "="*40)
        print("1. Subdomain Enumeration")
        print("2. JS Recon")
        print("3. Historical Recon")
        print("4. HTTP Analysis")
        print("5. Run Full Recon")
        print("0. Exit")

        # --- handle Ctrl+C on menu input ---
        try:
            choice = input(Fore.YELLOW + "\nEnter your choice: ").strip()
        except KeyboardInterrupt:
            print(Fore.RED + "\n[!] Interrupted by user")
            break

        if choice == "0":
            print(Fore.RED + "Exiting...")
            break

        if choice not in ["1", "2", "3", "4", "5"]:
            print(Fore.RED + "Invalid option")
            continue

        # --- handle Ctrl+C on target input ---
        try:
            target = input(Fore.YELLOW + "Enter target: ").strip()
        except KeyboardInterrupt:
            print(Fore.RED + "\n[!] Input cancelled")
            continue

        target = fix_url(target)
        domain = get_domain(target)

        # --- run selected module safely ---
        try:
            if choice == "1":
                from subdomain_enum import load_wordlist
                wordlist_size = len(load_wordlist())

                try:
                    limit = int(input(f"Enter limit (0 = full, max {wordlist_size}, default 5000): ") or 5000)
                except:
                    limit = 5000

                if limit == 0:
                    limit = None

                subs = subdomain_enum(domain, limit=limit)

                if output_file:
                    save_output(output_file, subs)

            elif choice == "2":
                js_recon(target)

            elif choice == "3":
                urls, paths, params, interesting = get_historical_data(domain)

                print(Fore.GREEN + "\n[+] Paths:")
                for p in paths:
                    print(p)

                print(Fore.GREEN + "\n[+] Parameters:")
                for param in params:
                    print(param)

            elif choice == "4":
                check(domain)

            elif choice == "5":
                run_all(target, output_file)

        except KeyboardInterrupt:
            print(Fore.RED + "\n[!] Operation interrupted")
            continue


if __name__ == "__main__":
    main()
