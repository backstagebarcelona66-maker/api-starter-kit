# 🚀 API Starter Kit — 23+ Production-Ready API Endpoints

A complete REST API suite for developers, startups, and businesses. Deploy in minutes, scale to thousands of requests.

[![GitHub stars](https://img.shields.io/github/stars/backstagebarcelona66-maker/api-starter-kit)](https://github.com/backstagebarcelona66-maker/api-starter-kit/stargazers)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## ✨ What's Inside

**3 API Services · 23+ Endpoints · Zero External Dependencies**

| Service | Port | Endpoints | Description |
|---------|------|-----------|-------------|
| **api-optimized** | 5005 | 8 | AI text processing, translation, summarization, rewriting |
| **value-api** | 5006 | 5 | PDF generation, image processing, QR codes, SEO analysis, data cleaning |
| **dev-tools** | 5011 | 12 | Developer utilities for daily workflow |

---

## 🛠️ API Endpoints

### 📝 Text Processing (8 endpoints)
- `POST /clean` — Remove extra whitespace, fix encoding, clean messy text
- `POST /translate` — Translate text between 10+ languages
- `POST /summarize` — AI-powered text summarization (3 styles)
- `POST /rewrite` — Rephrase text in 5 different styles
- `POST /expand` — Expand short text into detailed content
- `POST /score` — Rate content quality, readability, engagement
- `POST /json-clean` — Fix malformed JSON automatically
- `POST /json-format` — Pretty-print or minify JSON

### 📄 Document Generation (2 endpoints)
- `POST /pdf` — Generate professional PDF documents from text/HTML
- `POST /word` — Create Word (.docx) documents programmatically

### 🖼️ Image & Media (3 endpoints)
- `POST /image/resize` — Resize, crop, thumbnails
- `POST /image/filter` — Apply filters, adjust brightness/contrast
- `POST /qrcode` — Generate QR codes (customizable size, color, logo)

### 🔗 URL & Web Tools (4 endpoints)
- `POST /url/shorten` — Create short URLs
- `POST /url/validate` — Validate URLs and emails
- `POST /url/preview` — Generate link previews (Open Graph cards)
- `POST /url/validate` — Full URL structure validation

### 📊 Data Tools (4 endpoints)
- `POST /fake-data` — Generate realistic fake data (names, emails, addresses)
- `POST /currency` — Real-time currency conversion
- `POST /color/convert` — HEX/RGB/HSL color conversion
- `POST /hash` — Generate MD5, SHA256, bcrypt hashes

### 🔐 Security & Auth (2 endpoints)
- `POST /jwt/encode` — Create JWT tokens
- `POST /jwt/decode` — Decode and verify JWT tokens

### 🌐 SEO & Analysis (2 endpoints)
- `POST /seo/analyze` — Analyze page SEO score
- `GET /seo/keywords` — Extract keywords from text

---

## ⚡ Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/backstagebarcelona66-maker/api-starter-kit.git
cd api-starter-kit

# 2. Install dependencies
pip install flask flask-cors requests Pillow reportlab qrcode beautifulsoup4

# 3. Start all services
python3 api-optimized/app.py &   # Port 5005
python3 value-api/app.py &       # Port 5006
python3 dev-tools/app.py &        # Port 5011

# 4. Test
curl http://localhost:5005/health
curl http://localhost:5006/health
curl http://localhost:5011/health
```

---

## 💰 Pricing

All endpoints work with included demo key. Production use requires API key.

| Plan | Price | Requests/Day |
|------|-------|-------------|
| Free | $0 | 100 |
| Starter | $15/mo | 1,000 |
| Professional | $35/mo | 10,000 |
| Enterprise | $75/mo | Unlimited |

**Get your API key → Contact me**

---

## 📦 One-Click Deploy

Deploy to your own server in 5 minutes:

```bash
# Deploy to Linux server
curl -fsSL https://raw.githubusercontent.com/backstagebarcelona66-maker/api-starter-kit/main/deploy.sh | bash
```

---

## 🧪 Examples

### Generate a QR Code
```bash
curl -X POST http://localhost:5006/qrcode \
  -H "Content-Type: application/json" \
  -d '{"data": "https://yoursite.com", "size": 300}'
```

### Clean Text
```bash
curl -X POST http://localhost:5005/clean \
  -H "Content-Type: application/json" \
  -H "X-API-Key: demo-key-001" \
  -d '{"text": "  Hello    World!  "}'
```

### Generate Fake Data
```bash
curl -X POST http://localhost:5011/fake-data \
  -H "Content-Type: application/json" \
  -d '{"type": "user", "count": 10}'
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│            API Gateway Layer            │
│         (Authentication + Rate Limit)   │
└──────────┬──────────┬──────────────────┘
           │          │          │
      ┌────▼───┐ ┌───▼────┐ ┌──▼──────┐
      │ Text   │ │Docs &  │ │ Dev     │
      │ Process│ │ Images │ │ Tools   │
      │ :5005  │ │ :5006  │ │ :5011   │
      └────────┘ └────────┘ └─────────┘
```

---

## 👨‍💻 About Me

Full-stack developer specializing in API development, automation, and backend systems. I build scalable tools that save developers hours of repetitive work.

**Languages:** Python, JavaScript, Node.js  
**Infrastructure:** Google Cloud, Docker, Cloud Run  
**Contact:** backstagebarcelona66@gmail.com

---

## 📄 License

MIT License — Free to use, modify, and commercialize.

---

⭐ **Star this repo if it helped you!**
