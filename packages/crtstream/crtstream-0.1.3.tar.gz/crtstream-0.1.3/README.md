# Certificate Transparency Log Streamer

**crtstream** is a lightweight Certificate Transparency (CT) log streamer written in Python.  
It continuously monitors CT logs and outputs newly issued certificates in real time.

It supports multiple output modes:
- Domain names only
- Human-readable summaries
- Full structured JSON suitable for pipelines and data analysis

---

## ✨ Features

- 📡 Real-time streaming from multiple CT logs  
- 📜 Supports X.509 and precert entries (RFC 6962)  
- 🧵 Multi-threaded (one thread per log)  
- 📦 Installable via `pip`  
- 🔌 Clean CLI interface  
- 🧾 JSON output suitable for SIEM, analytics, or storage  
- ⚙️ Default bundled `logs.json`, no setup required  
- 🛠 Custom CT log configuration supported via `--logs`  

---

## 📦 Installation

### From PyPI (recommended)

```bash
pip install crtstream
````

Or with `pipx`:

```bash
pipx install crtstream
```

### From source (development)

```bash
git clone https://github.com/glaubermagal/crtstream.git
cd crtstream
pip install -e .
```

---

## ⚙️ Configuration

`crtstream` uses a **default `logs.json`** bundled with the package.
You do **not** need to create a file manually.

### Use default logs (no setup required)

```bash
crtstream
```

### Use a custom CT logs file

```bash
crtstream --logs /path/to/logs.json
```

#### Example `logs.json` format

```json
{
  "google_us": "https://ct.googleapis.com/logs/us1/argon2025h2",
  "google_eu": "https://ct.googleapis.com/logs/eu1/xenon2025h2",
  "cloudflare_nimbus": "https://ct.cloudflare.com/logs/nimbus2025",
  "digicert_yeti": "https://yeti2025.ct.digicert.com/log",
  "digicert_nessie": "https://nessie2025.ct.digicert.com/log"
}
```

---

## 🚀 Usage

### Basic usage

```bash
crtstream
```

### Print only domains

```bash
crtstream --domains-only
```

### Output full JSON (one object per line)

```bash
crtstream --json
```

### Custom logs file + JSON output

```bash
crtstream --logs /path/to/logs.json --json
```

---

## 🧾 JSON Output Format

Each line is a JSON object when using `--json`:

```json
{
  "log_name": "google_us",
  "log_url": "https://ct.googleapis.com/logs/us1/argon2025h2",
  "entry_index": 123456,
  "timestamp": "2025-01-01T12:00:00Z",
  "certificate": {
    "domains": ["example.com", "www.example.com"],
    "subject": { "commonName": "example.com" },
    "issuer": { "commonName": "Google Trust Services" },
    "validity": {
      "not_before": "2025-01-01T00:00:00",
      "not_after": "2025-04-01T23:59:59"
    },
    "serial_number": "0x123abc",
    "public_key": {
      "type": "RSAPublicKey",
      "key_size": 2048
    },
    "version": "v3"
  },
  "raw_entry": { "...": "..." }
}
```

Ideal for:

* Log ingestion pipelines
* Data analysis
* Security monitoring
* Threat intelligence

---

## 🧠 How it works

* Polls each CT log every few seconds
* Fetches new entries using `/ct/v1/get-entries`
* Parses X.509 or precert entries
* Extracts SAN domains and certificate metadata
* Streams output continuously to stdout

---

## ⚠️ Notes & Limitations

* **No persistent state** (restarts from near-tip by default)
* CT logs may rate-limit or temporarily fail
* No filtering is applied by default

---

## 🤝 Contributing

Contributions are welcome!

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

Please keep changes focused and well-documented.

---

## 📜 License

This project is licensed under the **MIT License**.
See the [LICENSE](LICENSE) file for details.
