## yahoomail

⚡ A fast and stealthy Python login checker for Yahoo Mail accounts bypasses multi-step login flow, device fingerprint challenges, and delivers accurate status in milliseconds.

---

## 🚀 Features

- 🔁 Fully asynchronous (via `httpx.AsyncClient`)
- 🔍 Fast-path + fallback HTML form parsing
- 🔐 Bypasses Yahoo's anti-bot login system
- 🎯 Precise detection: `SUCCESS`, `INVALID`, `2FA`, `ERROR`, `UNKNOWN`
- 🧠 Regex-based turbo form extraction (1-pass)
- 🌐 Proxy support: `http`, `socks5`, with multiple formats
- 📡 Optimized headers & fingerprint handling
- 🧪 Debug-ready (optional HTML dumps at every step)
- 📦 Includes batch checker with configurable concurrency

---

## 📦 Installation

pip install yahoomail
Or clone locally:

```bash
git clone https://github.com/youruser/yahoomail.git
cd yahoomail-checker
pip install -r requirements.txt
```

## ⚙️ Usage
## ✅ Basic login check

```python
from yahoomail import login

status, message, duration_ms = login("user@yahoo.com", "password123")
print(f"[{status}] {message} ({duration_ms}ms)")
```

## 🌍 Set a proxy
```python
from yahoomail import set_proxies
set_proxies("user:pass@host:port")  # or "host:port"
```
<p2>Supports formats </p2>:
``` 
```

*  user:pass@host:port
* host:port
* host,port,user,pass
* host:port:user:pass

🚀 Batch checking (async)

```python
import asyncio
from yahoomail import run_batch

creds = [
    ("email1@yahoo.com", "pass1"),
    ("email2@yahoo.com", "pass2"),
]

results = asyncio.run(run_batch(creds, concurrency=10))
for email, status, message in results:
    print(f"{email} → {status}: {message}")
```

| Code  | Meaning      |  
|-----------|-----------
| SUCCESS  | Valid login detected (your accounts is mostly valid!) | 
| Invalid  | Bad account  |
| 2FA | 2-Factor Authentification (or means other errors)
| Error | Proxy / network / internal error (Or just Yahoo maybe implemented another level cap of security (ya need to check).   
| Unkown | I fucked up... | 
 

## 🧰 Advanced
> Enable debug HTML saves:
> Uncomment or modify the global flag in your script:

```python
ENABLE_DEBUG_FILES = True
```
It will save HTML dumps per stage for inspection (eg: new security...)

## 🧠 How it works
This module emulates Yahoo Mail login behavior by reproducing:

* Initial tokenized form loads
*	Username + password flow separation
*	Dynamic fingerprinting step
*	Cookie-based login validation
*	Full proxy routing with timeout handling
*   No Selenium. No headless browser. Just pure, clean HTTP emulation.

## 📜 License

Creative Commons Attribution-NonCommercial-ShareAlike 4.0 (CC BY-NC-SA 4.0)

- ✅ You can **use**, **study**, **modify**, and **share** this project.
- ❌ **Commercial use** (resale, SaaS integration, paid API, etc.) is **strictly prohibited**.
- 🧠 You **must give credit** to the original author.
- 🔁 If you modify it, you must release your version under the same license.

🔗 [Read the full license terms here](https://creativecommons.org/licenses/by-nc-sa/4.0/)

## ☕ A note
This project was born from one simple idea:
"If there's no public API... then I become the API."
I have enough of these restrictions of stupid developer mode restriction
Built for speed. Tuned for accuracy.
Tested against reality.


Enjoy.