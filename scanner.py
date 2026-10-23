#!/usr/bin/env python3
"""
Simple Network Vulnerability Scanner
=====================================
A beginner/trainee-friendly cybersecurity project.

Features:
  - Multi-threaded TCP port scanning
  - Service banner grabbing on open ports
  - Basic vulnerability check against a small local
    database of known-vulnerable service/version strings
  - Console + CSV + HTML report output

IMPORTANT / LEGAL NOTICE:
  Only scan systems you OWN or have EXPLICIT WRITTEN PERMISSION
  to test (e.g. localhost, your own lab VM, or a machine your
  employer has authorized). Scanning systems without authorization
  is illegal in most countries. This tool is for educational /
  authorized security-assessment use only.

Usage:
  python scanner.py -t 127.0.0.1 -p 1-1024
  python scanner.py -t 192.168.1.10 -p 22,80,443,3306
  python scanner.py -t scanme.example.com -p 1-65535 --threads 200
"""

import argparse
import csv
import socket
import sys
import threading
import queue
import datetime
import html as html_lib

# ---------------------------------------------------------------------------
# A small local "vulnerability database".
# In a real tool this would query the NVD/CVE API, but for a trainee
# project a local lookup table demonstrates the concept clearly and
# works fully offline.
# ---------------------------------------------------------------------------
VULN_DB = [
    {
        "match": "OpenSSH 7.2",
        "cve": "CVE-2016-6210",
        "severity": "Medium",
        "description": "User enumeration via timing attack in OpenSSH 7.2",
    },
    {
        "match": "OpenSSH 6.6",
        "cve": "CVE-2015-5600",
        "severity": "Medium",
        "description": "Weakness in keyboard-interactive authentication (brute-force amplification)",
    },
    {
        "match": "vsftpd 2.3.4",
        "cve": "CVE-2011-2523",
        "severity": "Critical",
        "description": "Backdoor command execution vulnerability in vsftpd 2.3.4",
    },
    {
        "match": "Apache/2.2",
        "cve": "CVE-2011-3192",
        "severity": "High",
        "description": "Apache 2.2 Range header denial-of-service (Apache Killer)",
    },
    {
        "match": "Apache/2.4.49",
        "cve": "CVE-2021-41773",
        "severity": "Critical",
        "description": "Path traversal / RCE in Apache HTTP Server 2.4.49",
    },
    {
        "match": "ProFTPD 1.3.3",
        "cve": "CVE-2010-4221",
        "severity": "Critical",
        "description": "ProFTPD 1.3.3 backdoor / buffer overflow",
    },
    {
        "match": "Microsoft-IIS/6.0",
        "cve": "CVE-2017-7269",
        "severity": "Critical",
        "description": "IIS 6.0 WebDAV buffer overflow (remote code execution)",
    },
]

COMMON_PORTS_HINT = {
    21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP", 53: "DNS",
    80: "HTTP", 110: "POP3", 143: "IMAP", 443: "HTTPS",
    3306: "MySQL", 3389: "RDP", 8080: "HTTP-Alt",
}

print_lock = threading.Lock()
results = []  # each item: dict(port, state, service, banner, vulns)


def parse_ports(port_arg):
    """Parse '1-1024' or '22,80,443' into a sorted list of ints."""
    ports = set()
    for part in port_arg.split(","):
        part = part.strip()
        if "-" in part:
            start, end = part.split("-")
            ports.update(range(int(start), int(end) + 1))
        elif part:
            ports.add(int(part))
    return sorted(p for p in ports if 0 < p <= 65535)


def grab_banner(sock):
    """Try to read a service banner; return '' if nothing comes back quickly."""
    try:
        sock.settimeout(1.0)
        banner = sock.recv(1024)
        return banner.decode(errors="ignore").strip()
    except Exception:
        return ""


def check_vulnerabilities(banner):
    """Match the banner text against the local vuln DB."""
    found = []
    if not banner:
        return found
    for entry in VULN_DB:
        if entry["match"].lower() in banner.lower():
            found.append(entry)
    return found


def scan_port(target, port, timeout):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            result = sock.connect_ex((target, port))
            if result == 0:
                banner = grab_banner(sock)
                vulns = check_vulnerabilities(banner)
                service_hint = COMMON_PORTS_HINT.get(port, "unknown")
                entry = {
                    "port": port,
                    "state": "open",
                    "service": service_hint,
                    "banner": banner,
                    "vulns": vulns,
                }
                with print_lock:
                    results.append(entry)
                    tag = f" | banner: {banner}" if banner else ""
                    print(f"[OPEN]  {target}:{port:<6} ({service_hint}){tag}")
                    for v in vulns:
                        print(f"        !! POSSIBLE VULN: {v['cve']} "
                              f"[{v['severity']}] - {v['description']}")
    except Exception:
        pass


def worker(target, timeout, q):
    while True:
        try:
            port = q.get_nowait()
        except queue.Empty:
            return
        scan_port(target, port, timeout)
        q.task_done()


def run_scan(target, ports, threads, timeout):
    try:
        socket.gethostbyname(target)
    except socket.gaierror:
        print(f"[!] Could not resolve target: {target}")
        sys.exit(1)

    print(f"[*] Scanning {target} | {len(ports)} ports | {threads} threads")
    print(f"[*] Started: {datetime.datetime.now().isoformat(timespec='seconds')}")
    print("-" * 60)

    q = queue.Queue()
    for p in ports:
        q.put(p)

    thread_list = []
    for _ in range(min(threads, len(ports)) or 1):
        t = threading.Thread(target=worker, args=(target, timeout, q))
        t.daemon = True
        t.start()
        thread_list.append(t)

    q.join()

    print("-" * 60)
    print(f"[*] Finished: {datetime.datetime.now().isoformat(timespec='seconds')}")
    print(f"[*] Open ports found: {len(results)}")


def write_csv_report(path, target):
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Target", "Port", "State", "Service", "Banner", "CVE", "Severity", "Description"])
        for r in sorted(results, key=lambda x: x["port"]):
            if r["vulns"]:
                for v in r["vulns"]:
                    writer.writerow([target, r["port"], r["state"], r["service"],
                                      r["banner"], v["cve"], v["severity"], v["description"]])
            else:
                writer.writerow([target, r["port"], r["state"], r["service"],
                                  r["banner"], "", "", ""])
    print(f"[*] CSV report saved to: {path}")


def write_html_report(path, target):
    rows = ""
    for r in sorted(results, key=lambda x: x["port"]):
        banner_safe = html_lib.escape(r["banner"]) if r["banner"] else "-"
        if r["vulns"]:
            for v in r["vulns"]:
                rows += f"""
                <tr>
                  <td>{r['port']}</td><td>{r['service']}</td><td>{banner_safe}</td>
                  <td class="vuln">{v['cve']}</td><td class="sev-{v['severity'].lower()}">{v['severity']}</td>
                  <td>{html_lib.escape(v['description'])}</td>
                </tr>"""
        else:
            rows += f"""
                <tr>
                  <td>{r['port']}</td><td>{r['service']}</td><td>{banner_safe}</td>
                  <td>-</td><td>-</td><td>No known vulnerability matched</td>
                </tr>"""

    html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Vulnerability Scan Report - {html_lib.escape(target)}</title>
<style>
  body {{ font-family: Arial, sans-serif; margin: 2rem; background: #f7f7f9; color: #222; }}
  h1 {{ color: #1a1a2e; }}
  .meta {{ color: #555; margin-bottom: 1.5rem; }}
  table {{ border-collapse: collapse; width: 100%; background: white; }}
  th, td {{ border: 1px solid #ddd; padding: 8px 12px; text-align: left; font-size: 14px; }}
  th {{ background: #1a1a2e; color: white; }}
  tr:nth-child(even) {{ background: #f2f2f2; }}
  .vuln {{ font-weight: bold; }}
  .sev-critical {{ color: white; background: #b00020; font-weight: bold; }}
  .sev-high {{ color: white; background: #e65100; font-weight: bold; }}
  .sev-medium {{ color: #222; background: #ffca28; font-weight: bold; }}
  .sev-low {{ color: #222; background: #c8e6c9; }}
</style>
</head>
<body>
  <h1>Vulnerability Scan Report</h1>
  <p class="meta">
    Target: <strong>{html_lib.escape(target)}</strong><br>
    Generated: {datetime.datetime.now().isoformat(timespec='seconds')}<br>
    Open ports: {len(results)}
  </p>
  <table>
    <tr><th>Port</th><th>Service</th><th>Banner</th><th>CVE</th><th>Severity</th><th>Description</th></tr>
    {rows}
  </table>
</body>
</html>"""
    with open(path, "w") as f:
        f.write(html_doc)
    print(f"[*] HTML report saved to: {path}")


def main():
    parser = argparse.ArgumentParser(
        description="Simple Python Vulnerability/Port Scanner (trainee project)"
    )
    parser.add_argument("-t", "--target", required=True, help="Target IP or hostname")
    parser.add_argument("-p", "--ports", default="1-1024",
                         help="Port(s): '1-1024' or '22,80,443' (default: 1-1024)")
    parser.add_argument("--threads", type=int, default=100, help="Number of threads (default: 100)")
    parser.add_argument("--timeout", type=float, default=1.0, help="Socket timeout in seconds (default: 1.0)")
    parser.add_argument("--csv", help="Path to save CSV report, e.g. report.csv")
    parser.add_argument("--html", help="Path to save HTML report, e.g. report.html")
    args = parser.parse_args()

    print("=" * 60)
    print(" Simple Vulnerability Scanner - Educational Use Only")
    print(" Only scan systems you own or are authorized to test.")
    print("=" * 60)

    ports = parse_ports(args.ports)
    run_scan(args.target, ports, args.threads, args.timeout)

    if args.csv:
        write_csv_report(args.csv, args.target)
    if args.html:
        write_html_report(args.html, args.target)


if __name__ == "__main__":
    main()