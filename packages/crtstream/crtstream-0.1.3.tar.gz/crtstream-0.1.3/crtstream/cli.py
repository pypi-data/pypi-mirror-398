import os
import json
import argparse
import sys
import time
import base64
import struct
import requests
from threading import Thread
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from datetime import datetime
from importlib import resources


POLL_INTERVAL = 10
BATCH_SIZE = 256

HEADERS = {"User-Agent": "crtstream/0.1.3"}

# ---------- Helpers ----------

def load_logs(logs_file: str | None):
    """
    Load CT logs.
    Priority:
      1) --logs <file>
      2) packaged default logs.json
    """

    # 1️⃣ User-provided file
    if logs_file:
        path = os.path.abspath(logs_file)

        if not os.path.isfile(path):
            raise RuntimeError(f"CT logs file not found: {path}")

        try:
            with open(path, "r", encoding="utf-8") as f:
                logs = json.load(f)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Invalid JSON in {path}: {e}")
        except Exception as e:
            raise RuntimeError(f"Failed to read logs file '{path}': {e}")

    # Packaged default
    else:
        try:
            with resources.files("crtstream.data").joinpath("logs.json").open("r", encoding="utf-8") as f:
                logs = json.load(f)
        except Exception as e:
            raise RuntimeError(f"Failed to load bundled logs.json: {e}")

    if not isinstance(logs, dict) or not logs:
        raise RuntimeError("CT logs must be a non-empty JSON object")

    return logs



# ---------- CT parsing helpers ----------

def parse_x509_from_entry(entry):
    leaf = base64.b64decode(entry["leaf_input"])
    extra = base64.b64decode(entry["extra_data"])

    entry_type = struct.unpack(">H", leaf[10:12])[0]

    # X509_ENTRY
    if entry_type == 0:
        cert_len = int.from_bytes(leaf[12:15], "big")
        cert_bytes = leaf[15:15 + cert_len]

    # PRECERT_ENTRY
    elif entry_type == 1:
        cert_len = int.from_bytes(extra[0:3], "big")
        cert_bytes = extra[3:3 + cert_len]

    else:
        raise ValueError(f"Unknown LogEntryType: {entry_type}")

    return x509.load_der_x509_certificate(cert_bytes, default_backend())


def extract_domains(cert):
    try:
        return cert.extensions.get_extension_for_class(
            x509.SubjectAlternativeName
        ).value.get_values_for_type(x509.DNSName)
    except Exception:
        return []


def extract_certificate_info(cert):
    subject = {attr.oid._name: attr.value for attr in cert.subject}
    issuer = {attr.oid._name: attr.value for attr in cert.issuer}

    return {
        "domains": extract_domains(cert),
        "subject": subject,
        "issuer": issuer,
        "validity": {
            "not_before": cert.not_valid_before_utc.isoformat()
            if cert.not_valid_before_utc else None,
            "not_after": cert.not_valid_after_utc.isoformat()
            if cert.not_valid_after_utc else None,
        },
        "serial_number": hex(cert.serial_number),
        "public_key": {
            "type": type(cert.public_key()).__name__,
            "key_size": getattr(cert.public_key(), "key_size", None),
        },
        "version": cert.version.name,
    }


# ---------- CT API ----------

def get_tree_size(log_url):
    r = requests.get(f"{log_url}/ct/v1/get-sth", headers=HEADERS, timeout=10)
    r.raise_for_status()
    return r.json()["tree_size"]


def fetch_entries(log_url, start, end):
    r = requests.get(
        f"{log_url}/ct/v1/get-entries",
        params={"start": start, "end": end},
        headers=HEADERS,
        timeout=20,
    )
    r.raise_for_status()
    return r.json()["entries"]


# ---------- Streamer ----------

def stream_log(name, log_url, domains_only, json_output):
    last_index = max(0, get_tree_size(log_url) - 100)

    while True:
        try:
            tree_size = get_tree_size(log_url)

            while last_index < tree_size:
                end = min(last_index + BATCH_SIZE - 1, tree_size - 1)
                entries = fetch_entries(log_url, last_index, end)

                for i, entry in enumerate(entries):
                    idx = last_index + i
                    try:
                        cert = parse_x509_from_entry(entry)
                        domains = extract_domains(cert)

                        if json_output:
                            print(json.dumps({
                                "log_name": name,
                                "log_url": log_url,
                                "entry_index": idx,
                                "timestamp": datetime.utcnow().isoformat(),
                                "certificate": extract_certificate_info(cert),
                                "raw_entry": entry,
                            }, default=str))

                        elif domains_only:
                            for d in domains:
                                print(d)

                        else:
                            print(
                                f"[{name}] {domains} | "
                                f"{cert.issuer.rfc4514_string()}"
                            )

                    except Exception as exc:
                        if json_output:
                            print(json.dumps({
                                "log_name": name,
                                "entry_index": idx,
                                "timestamp": datetime.utcnow().isoformat(),
                                "error": str(exc),
                            }))
                        else:
                            print(
                                f"[{name}] error processing entry {idx}: {exc}",
                                file=sys.stderr
                            )

                last_index = end + 1

        except Exception as exc:
            if json_output:
                print(json.dumps({
                    "log_name": name,
                    "timestamp": datetime.utcnow().isoformat(),
                    "error": str(exc),
                }))
            else:
                print(f"[{name}] error: {exc}", file=sys.stderr)

        time.sleep(POLL_INTERVAL)


# ---------- CLI ----------

def parse_args():
    parser = argparse.ArgumentParser(description="Certificate Transparency log streamer")

    parser.add_argument(
        "--logs",
        help="Path to JSON file with CT log URLs"
    )

    parser.add_argument(
        "--domains-only",
        action="store_true",
        help="Print only domain names"
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Output full certificate info as JSON"
    )

    return parser.parse_args()


def main():
    args = parse_args()

    if args.domains_only and args.json:
        print(
            "Error: Only one of --domains-only or --json may be used",
            file=sys.stderr
        )
        sys.exit(1)

    try:
        logs = load_logs(args.logs)
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    for name, url in logs.items():
        Thread(
            target=stream_log,
            args=(name, url, args.domains_only, args.json),
            daemon=True,
        ).start()

    while True:
        time.sleep(60)


if __name__ == "__main__":
    main()
