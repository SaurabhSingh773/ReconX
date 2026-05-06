import socket

def check(domain):
    dangerous_methods = ['PUT', 'DELETE', 'TRACE', 'CONNECT']

    # 🔹 HTTP Methods Check
    try:
        c = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        c.connect((domain, 80))

        request = f"OPTIONS / HTTP/1.1\r\nHost: {domain}\r\nConnection: close\r\n\r\n"
        c.send(request.encode())

        response = c.recv(2048).decode(errors="ignore")
        c.close()

        if 'Allow:' in response:
            allowed_methods = response.split('Allow: ')[1].split('\r\n')[0].split(', ')

            print("\n---------- HTTP METHODS CHECK ----------")
            print(f"Allowed methods: {', '.join(allowed_methods)}")

            for method in dangerous_methods:
                if method in allowed_methods:
                    print(f"[ALERT] Dangerous Method Enabled: {method}")
        else:
            print("\n[!] No Allow header found")

    except Exception as e:
        print(f"[!] HTTP methods check failed: {e}")

    # 🔹 HEAD Request (Headers)
    try:
        c = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        c.connect((domain, 80))

        request = f"HEAD / HTTP/1.1\r\nHost: {domain}\r\nConnection: close\r\n\r\n"
        c.send(request.encode())

        response = c.recv(4096)
        response_text = response.decode(errors="ignore")

        print("\n--------- Response Headers ---------")
        print(response_text)

        headers = {}
        for line in response_text.split("\r\n")[1:]:
            if ": " in line:
                key, value = line.split(": ", 1)
                headers[key.strip().lower()] = value.strip()

        security_headers = [
            "strict-transport-security",
            "x-content-type-options",
            "x-frame-options",
            "content-security-policy",
            "referrer-policy",
            "x-xss-protection",
            "permissions-policy",
            "cross-origin-embedder-policy",
            "cross-origin-opener-policy",
            "cross-origin-resource-policy",
            "x-permitted-cross-domain-policies"
        ]

        print("\n---------- Security Header Check ----------")
        for header in security_headers:
            if header not in headers:
                print(f"[ALERT] Missing: {header}")
            else:
                print(f"[OK] Found: {header} -> {headers[header]}")

        c.close()

    except Exception as e:
        print(f"[!] Header check failed: {e}")

if __name__ == "__main__":
    domain = input("Enter a domain: ").strip()
    check(domain)
