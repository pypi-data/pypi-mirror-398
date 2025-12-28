<!--
Keywords: twitter account generator, x account generator, twitter gen, x gen, twitter solver,
x solver, twitter captcha solver, x captcha solver, twitter automation, x automation,
twitter bot, x bot, twitter account gen, x account gen, castle solver, castle.io bypass,
castle.io solver, recaptcha solver, recaptcha bypass, captcha solver, captcha bypass,
cloudflare bypass, akamai bypass, tls bypass, twitter api, x api, social media automation,
account creation tool, twitter registration, x registration, twitter signup automation,
x signup automation, anti-bot bypass, twitter account creator, x account creator
-->

<div align="center">

# 🏰 Castle Breaker

### Twitter Account Generator & X Solver | Captcha Solving Service

**Premium Captcha Solving Service for Twitter/X Account Generation & Bot Bypass**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![PyPI version](https://img.shields.io/pypi/v/castlebreaker.svg)](https://pypi.org/project/castlebreaker/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://img.shields.io/pypi/dm/castlebreaker.svg)](https://pypi.org/project/castlebreaker/)

[🌐 Website](https://castlebreaker.cc) • [📊 Dashboard](https://castlebreaker.cc/dashboard) • [🔑 Get API Key](https://castlebreaker.cc/dashboard)

</div>

---

## 🎯 What is Castle Breaker?

**Castle Breaker** is a premium **captcha solving service** that provides high-quality solved tokens to bypass bot detection systems. Our solved captcha tokens enable seamless **Twitter/X account generation**, automation, and access to protected endpoints.

### Our Services:

| Service | Description | Platform |
|---------|-------------|----------|
| 🏰 **Castle.io Token Solver** | High-quality Castle.io tokens for X.com | Twitter/X |
| ✅ **ReCAPTCHA v3 Solver** | Instant ReCAPTCHA tokens for X.com | Twitter/X |
| 🔐 **TLS Bypass API** | Bypass TLS fingerprinting detection | Any protected site |

### Why Castle Breaker?

- � **Optimized for X.com** - Our Castle.io and ReCAPTCHA v3 tokens are specifically designed for Twitter/X
- ⚡ **High-Quality Tokens** - Industry-leading solve rates for bot detection bypass
- 🔐 **TLS Fingerprint Bypass** - Evade Cloudflare, Akamai, and other TLS-based protections
- 🚀 **Fast Response** - Castle.io tokens delivered in ~5 seconds
- 🛡️ **Proxyless** - No proxy required for token generation

---

## 🚀 How It Works

```
┌──────────────────┐      ┌─────────────────────┐      ┌──────────────────┐
│   Your App       │ ───► │  Castle Breaker     │ ───► │   Solved Token   │
│   (Uses SDK)     │      │  (Solving Service)  │      │   (Ready to Use) │
└──────────────────┘      └─────────────────────┘      └──────────────────┘
         │                                                       │
         └───────────────────────────────────────────────────────┘
                    Use token to bypass X.com bot detection
```

1. **Request a token** through our Python SDK
2. **We solve** Castle.io/ReCAPTCHA challenges on our infrastructure
3. **Get high-quality tokens** ready for Twitter/X account generation
4. **Use tokens** to bypass bot detection on X.com

---

## 📦 Installation

Install our Python SDK to access the Castle Breaker service:

```bash
pip install castlebreaker
```

---

## 🏰 Castle.io Tokens for X.com

X.com (Twitter) uses Castle.io to detect and block bots. Our service solves these challenges and returns valid tokens for your Twitter/X account generation workflows.

### Get a Castle.io Token

```python
from castlebreaker import Castle

with Castle(api_key="your-api-key") as client:
    # Request a solved Castle.io token from our service
    result = client.solve_castle()
    
    # High-quality token ready for X.com
    token = result["token"]
    
    # Matching fingerprint data for consistency
    cookie = f"__cuid={result['cid']}"
    user_agent = result["user_agent"]
    accept_lang = result["accept_lang"]
    
    # Use these in your X.com/Twitter requests to bypass bot detection
```

### Bulk Token Generation for Twitter/X Gen

Need multiple tokens for batch Twitter/X account creation? Request them in bulk:

```python
with Castle(api_key="your-api-key") as client:
    # Get 10 solved tokens at once for bulk X/Twitter gen
    batch = client.solve_castle_many(count=10)
    
    for token in batch["tokens"]:
        # Each token is ready for a separate X.com account
        print(f"Token: {token[:40]}...")
    
    # All tokens share consistent fingerprint data
    cookie = f"__cuid={batch['cid']}"
    user_agent = batch["user_agent"]
```

---

## ✅ ReCAPTCHA v3 Tokens for X.com

Our service also solves ReCAPTCHA v3 challenges used on Twitter/X signup and login flows.

```python
with Castle(api_key="your-api-key") as client:
    # Get a solved ReCAPTCHA v3 token for X.com
    captcha_token = client.solve_recaptcha()
    
    # Use this token in your Twitter/X requests
    print(f"ReCAPTCHA Token: {captcha_token}")
```

---

## 🔐 TLS Bypass API

Many sites use TLS fingerprinting to detect bots. Our TLS Bypass API routes your requests through our infrastructure, presenting legitimate browser fingerprints to bypass these checks.

### Bypass Cloudflare TLS Detection

```python
with Castle(api_key="your-api-key") as client:
    # Make requests that bypass TLS fingerprinting
    result = client.tls_request(
        "https://protected-site.com",
        tls_config="CLOUDFLARE",
    )
    print(result["text"])  # Response HTML
    print(result["status_code"])  # HTTP status
```

### Bypass Akamai Protection

```python
with Castle(api_key="your-api-key") as client:
    # POST request with Akamai TLS bypass
    result = client.tls_request(
        "https://api.example.com/endpoint",
        method="POST",
        json={"username": "user", "email": "user@example.com"},
        tls_config="AKAMAI",
    )
```

### Supported TLS Configurations

| Config | Bypasses | Best For |
|--------|----------|----------|
| `CLOUDFLARE` | Cloudflare Bot Management | Most websites, Twitter/X |
| `AKAMAI` | Akamai Bot Manager | E-commerce, financial sites |
| `CUSTOM` | Generic fingerprint | General scraping |

---

## ⚡ Async API for High-Volume Twitter/X Gen

For high-performance Twitter/X account generation, use our async client:

```python
import asyncio
from castlebreaker import CastleAsync

async def bulk_twitter_x_gen():
    async with CastleAsync(api_key="your-api-key") as client:
        # Request 50 Castle.io tokens concurrently
        tasks = [client.solve_castle() for _ in range(50)]
        tokens = await asyncio.gather(*tasks)
        
        for i, result in enumerate(tokens):
            print(f"Token {i+1}: {result['token'][:30]}...")

asyncio.run(bulk_twitter_x_gen())
```

---

## 🎯 Use Cases

### 🐦 Twitter Account Generator
Use our solved Castle.io tokens to bypass bot detection during Twitter account creation. Perfect for:
- Social media management platforms
- Marketing automation tools
- Business account provisioning
- Testing and development

### 🔷 X Account Generator
X.com uses the same Castle.io protection as Twitter. Our high-quality tokens enable:
- Bulk X account creation
- Automated signup workflows
- X automation platforms
- Research and testing

### 🛡️ Bot Detection Bypass
Our solved tokens are designed to bypass:
- Castle.io bot detection (used by X.com)
- ReCAPTCHA v3 challenges
- TLS fingerprinting checks
- Browser fingerprint verification

### 🌐 TLS Fingerprint Bypass
Access protected sites without getting blocked:
- Cloudflare-protected endpoints
- Akamai Bot Manager sites
- Custom TLS verification systems

---

## 💰 Check Your Balance

```python
with Castle(api_key="your-api-key") as client:
    balance = client.get_balance()
    print(f"Credits: {balance['credits']}")
    print(f"Requests: {balance['requests_count']}")
    print(f"Spent: ${balance['total_spent']:.2f}")
```

---

## 🛠️ Exception Handling

```python
from castlebreaker import Castle
from castlebreaker.exceptions import (
    AuthenticationError,
    RateLimitError,
    NetworkError,
    CastleBreakerError,
)

with Castle(api_key="your-api-key") as client:
    try:
        result = client.solve_castle()
        
    except AuthenticationError:
        print("Invalid API key - get one at castlebreaker.cc")
        
    except RateLimitError as e:
        print(f"Rate limited. Retry after: {e.retry_after}s")
        
    except NetworkError:
        print("Connection issue - check your network")
        
    except CastleBreakerError as e:
        print(f"Error: {e.message}")
```
---

## ⚙️ SDK Configuration

```python
client = Castle(
    api_key="your-api-key",
    base_url="https://castlebreaker.cc",  # Service endpoint
    timeout=120.0,                         # Request timeout
    max_retries=3,                         # Retry attempts
)
```

---

## ❓ FAQ

### What is Castle Breaker?
Castle Breaker is a **captcha solving service** that provides high-quality solved tokens for bypassing bot detection systems. We specialize in Castle.io and ReCAPTCHA v3 tokens for X.com (Twitter).

### How does this help with Twitter/X account generation?
X.com uses Castle.io to detect and block bots during account creation. Our service solves these challenges and returns valid tokens that you can use in your signup requests to bypass bot detection.

### What makes your tokens "high-quality"?
Our tokens are generated with consistent browser fingerprints (user agent, cookies, accept language) that match real user behavior, resulting in higher success rates for Twitter/X account generation.

### Do I need proxies?
No! Our Castle.io solver is completely **proxyless**. We handle all the solving on our infrastructure.

### How fast are your solvers?
- **Castle.io**: ~5 seconds per token
- **ReCAPTCHA v3**: Instant
- **TLS requests**: Depends on target site

### What is the TLS Bypass API?
Many sites use TLS fingerprinting to detect bots. Our TLS API routes your requests through our infrastructure, presenting legitimate browser TLS fingerprints to bypass these detection systems.

---

## 📋 Requirements

- Python 3.10+
- httpx >= 0.27.0

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

## 🔗 Related Keywords

`twitter account generator` · `x account generator` · `twitter gen` · `x gen` · `twitter solver` · `x solver` · `twitter captcha solver` · `x captcha solver` · `castle.io solver` · `castle.io bypass` · `recaptcha solver` · `captcha bypass` · `twitter automation` · `x automation` · `twitter bot` · `tls bypass` · `cloudflare bypass` · `akamai bypass` · `twitter account creator` · `x account creator` · `social media automation` · `bot detection bypass` · `captcha solving service`

---

<div align="center">

**[🚀 Get Started](https://castlebreaker.cc)** • **[📊 Dashboard](https://castlebreaker.cc/dashboard)** • **[💬 Support](https://castlebreaker.cc/support)**

### Ready to bypass bot detection on X.com?

```bash
pip install castlebreaker
```

Made with ❤️ by the Castle Breaker team

**Star ⭐ this repo if Castle Breaker helps with your Twitter/X automation!**

</div>