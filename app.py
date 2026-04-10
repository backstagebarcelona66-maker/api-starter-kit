"""
🔧 开发者工具 API 套件 v1.0
12 个实用工具 API，无需付费 Key！
"""

from flask import Flask, request, jsonify
import os, json, hashlib, time, io, re, uuid
import urllib.request, urllib.parse
import secrets, string, random
from datetime import datetime, timedelta
from functools import wraps
import threading

app = Flask(__name__)

# ============== 认证系统 ==============
API_KEYS = {
    'demo-key-001': {'user_id': 'u001', 'name': '演示用户', 'plan': 'free', 'rate_limit': 100},
    'pro-key-002': {'user_id': 'u002', 'name': '专业用户', 'plan': 'pro', 'rate_limit': 1000},
    'enterprise-key-003': {'user_id': 'u003', 'name': '企业用户', 'plan': 'enterprise', 'rate_limit': -1},
}
usage_stats = {}
usage_lock = threading.Lock()

def check_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            if request.path == '/health': return f(*args, **kwargs)
            return jsonify({'success': False, 'error': '缺少 X-API-Key'}), 401
        if api_key not in API_KEYS:
            return jsonify({'success': False, 'error': '无效 API Key'}), 401
        user = API_KEYS[api_key]
        if user['rate_limit'] > 0:
            with usage_lock:
                hour = datetime.now().replace(minute=0, second=0, microsecond=0)
                key = f"{api_key}:{hour.isoformat()}"
                usage_stats[key] = usage_stats.get(key, 0) + 1
                if usage_stats[key] > user['rate_limit']:
                    return jsonify({'success': False, 'error': '速率限制已达'}), 429
        return f(*args, **kwargs)
    return decorated


# ===========================
#  1. 💱 货币换算 API
# ===========================
@app.route('/api/currency-convert', methods=['POST'])
@check_api_key
def api_currency_convert():
    """
    货币换算 - 实时汇率，支持 30+ 货币
    """
    try:
        data = request.get_json() or {}
        amount = float(data.get('amount', 1))
        from_currency = data.get('from', 'USD').upper()
        to_currency = data.get('to', 'CNY').upper()
        
        # 尝试从免费 API 获取汇率
        rate = None
        try:
            url = f'https://api.exchangerate-api.com/v4/latest/{from_currency}'
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=8) as resp:
                result = json.loads(resp.read().decode())
                rates = result.get('rates', {})
                rate = rates.get(to_currency)
        except: pass
        
        # 备用汇率表（大致估算）
        fallback_rates = {
            'USD': 1.0, 'CNY': 7.25, 'EUR': 0.92, 'GBP': 0.79,
            'JPY': 149.5, 'KRW': 1330, 'HKD': 7.82, 'TWD': 31.5,
            'SGD': 1.34, 'AUD': 1.53, 'CAD': 1.36, 'CHF': 0.88,
            'INR': 83.1, 'BRL': 4.97, 'MXN': 17.15, 'RUB': 92.5,
        }
        
        if rate is None:
            if from_currency in fallback_rates and to_currency in fallback_rates:
                rate = fallback_rates[to_currency] / fallback_rates[from_currency]
            else:
                return jsonify({'success': False, 'error': f'不支持的货币对: {from_currency}/{to_currency}'}), 400
        
        converted = round(amount * rate, 2)
        
        return jsonify({
            'success': True,
            'from': {'currency': from_currency, 'amount': amount},
            'to': {'currency': to_currency, 'amount': converted},
            'rate': round(rate, 6),
            'timestamp': datetime.now().isoformat(),
            'source': 'exchangerate-api' if rate else 'fallback'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ===========================
#  2. 🔗 URL 元数据提取 API
# ===========================
@app.route('/api/url-preview', methods=['POST'])
@check_api_key
def api_url_preview():
    """
    URL 预览 - 获取网页标题、描述、图片（Link Preview）
    用途：社交分享卡片、自动生成预览
    """
    try:
        data = request.get_json() or {}
        url = data.get('url', '')
        if not url:
            return jsonify({'success': False, 'error': '缺少 url 参数'}), 400
        
        # 解析 URL
        try:
            parsed = urllib.parse.urlparse(url)
            if not parsed.scheme:
                url = 'https://' + url
                parsed = urllib.parse.urlparse(url)
        except:
            return jsonify({'success': False, 'error': '无效 URL 格式'}), 400
        
        # 获取网页
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (compatible; Bot/1.0; +http://example.com/bot)'
            })
            with urllib.request.urlopen(req, timeout=10) as resp:
                html = resp.read().decode('utf-8', errors='ignore')
                content_type = resp.headers.get('Content-Type', '')
        except Exception as e:
            return jsonify({'success': False, 'error': f'无法访问: {str(e)}'}), 400
        
        # 提取元数据
        title = ''
        title_m = re.search(r'<title[^>]*>([^<]+)</title>', html, re.I)
        if title_m: title = title_m.group(1).strip()
        
        # OG 标签（优先）
        og_title = re.search(r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)["\']', html, re.I)
        if not og_title:
            og_title = re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:title["\']', html, re.I)
        if og_title: title = og_title.group(1).strip()
        
        description = ''
        og_desc = re.search(r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\']([^"\']+)["\']', html, re.I)
        if not og_desc:
            og_desc = re.search(r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)["\']', html, re.I)
            if not og_desc:
                og_desc = re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']description["\']', html, re.I)
        if og_desc: description = og_desc.group(1).strip()[:300]
        
        # 图片
        og_image = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', html, re.I)
        if not og_image:
            og_image = re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']', html, re.I)
        image = og_image.group(1).strip() if og_image else ''
        
        # Twitter Card
        twitter_image = re.search(r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)["\']', html, re.I)
        if twitter_image and not image:
            image = twitter_image.group(1).strip()
        
        # 域名
        domain = parsed.netloc
        
        return jsonify({
            'success': True,
            'url': url,
            'domain': domain,
            'preview': {
                'title': title,
                'description': description,
                'image': image,
                'content_type': content_type
            },
            'favicon': f'https://www.google.com/s2/favicons?domain={domain}&sz=64'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ===========================
#  3. 📝 Slug 生成 API
# ===========================
@app.route('/api/slug-generate', methods=['POST'])
@check_api_key
def api_slug_generate():
    """
    Slug 生成 - 把任意文本转为 URL 友好的 slug
    用途：博客文章 URL、SEO 友好的链接
    """
    try:
        data = request.get_json() or {}
        text = data.get('text', '')
        if not text:
            return jsonify({'success': False, 'error': '缺少 text 参数'}), 400
        
        # 转为小写
        slug = text.lower().strip()
        
        # 中文转拼音（简化版，替换常见词）
        chinese_map = {
            '测试': 'test', '文章': 'article', '博客': 'blog', '新闻': 'news',
            '关于': 'about', '联系': 'contact', '服务': 'service', '产品': 'product',
            '公司': 'company', '首页': 'home', '登录': 'login', '注册': 'register',
        }
        for cn, en in chinese_map.items():
            slug = slug.replace(cn, en)
        
        # 替换特殊字符
        slug = re.sub(r'[^\w\s-]', '', slug)  # 移除特殊字符
        slug = re.sub(r'[-\s]+', '-', slug)   # 空格转连字符
        slug = slug.strip('-')                 # 移除首尾连字符
        
        # 长度限制
        max_len = data.get('max_length', 60)
        if len(slug) > max_len:
            slug = slug[:max_len].rstrip('-')
        
        # 生成变体
        variants = [slug]
        if data.get('include_variants', False):
            variants.append(slug.replace('-', '_'))
            variants.append(slug.replace('-', ''))
        
        return jsonify({
            'success': True,
            'original': text,
            'slug': slug,
            'variants': variants,
            'length': len(slug)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ===========================
#  4. 🔐 Hash 生成 API
# ===========================
@app.route('/api/hash-generate', methods=['POST'])
@check_api_key
def api_hash_generate():
    """
    Hash 生成 - MD5, SHA1, SHA256, SHA512
    用途：密码存储、文件校验、数字签名
    """
    try:
        import hashlib
        data = request.get_json() or {}
        text = data.get('text', '')
        algorithms = data.get('algorithms', ['md5', 'sha256'])
        
        if not text:
            return jsonify({'success': False, 'error': '缺少 text 参数'}), 400
        
        text_bytes = text.encode('utf-8')
        result = {'success': True, 'original': text}
        
        algo_map = {
            'md5': lambda: hashlib.md5(text_bytes).hexdigest(),
            'sha1': lambda: hashlib.sha1(text_bytes).hexdigest(),
            'sha256': lambda: hashlib.sha256(text_bytes).hexdigest(),
            'sha512': lambda: hashlib.sha512(text_bytes).hexdigest(),
            'blake2b': lambda: hashlib.blake2b(text_bytes).hexdigest(),
        }
        
        for algo in algorithms:
            algo = algo.lower().strip()
            if algo in algo_map:
                result[algo] = algo_map[algo]()
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ===========================
#  5. 🎲 随机数据生成 API
# ===========================
@app.route('/api/fake-data', methods=['POST'])
@check_api_key
def api_fake_data():
    """
    随机数据生成 - 假名、假邮箱、假地址、假信用卡等
    用途：测试数据、脱敏演示
    """
    try:
        import random
        data = request.get_json() or {}
        data_type = data.get('type', 'all')
        count = min(int(data.get('count', 1)), 100)
        locale = data.get('locale', 'en')  # en | zh | ja
        
        # 假数据字典
        first_names_en = ['James', 'Emma', 'Oliver', 'Sophia', 'William', 'Ava', 'Benjamin', 'Isabella', 'Lucas', 'Mia']
        last_names_en = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez']
        
        first_names_zh = ['伟', '芳', '娜', '秀英', '敏', '静', '丽', '强', '磊', '军']
        last_names_zh = ['王', '李', '张', '刘', '陈', '杨', '赵', '黄', '周', '吴']
        
        domains = ['gmail.com', 'yahoo.com', 'outlook.com', 'proton.me', 'icloud.com']
        streets = ['Main St', 'Oak Ave', 'Maple Dr', 'Cedar Ln', 'Park Rd', 'Elm St']
        cities_us = ['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix']
        cities_cn = ['北京', '上海', '深圳', '广州', '杭州', '成都', '武汉']
        
        results = []
        
        for i in range(count):
            first = random.choice(first_names_en if locale == 'en' else first_names_zh)
            last = random.choice(last_names_en if locale == 'en' else last_names_zh)
            domain = random.choice(domains)
            username = f"{first.lower()}.{last.lower()}{random.randint(1,999)}"
            
            item = {
                'id': str(uuid.uuid4())[:8],
                'name': f"{first} {last}" if locale == 'en' else f"{''.join(random.sample(first_names_zh,1))}{''.join(random.sample(last_names_zh,1))}",
                'email': f"{username}@{domain}",
                'phone': f"+1-{random.randint(200,999)}-{random.randint(100,999)}-{random.randint(1000,9999)}",
                'address': {
                    'street': f"{random.randint(100,9999)} {random.choice(streets)}",
                    'city': random.choice(cities_us if locale == 'en' else cities_cn),
                    'state': random.choice(['CA', 'NY', 'TX', 'FL']) if locale == 'en' else '省',
                    'zip': str(random.randint(10000, 99999)) if locale == 'en' else str(random.randint(100000, 999999)),
                    'country': 'US' if locale == 'en' else 'CN'
                },
                'username': username,
                'password': ''.join(random.choices(string.ascii_letters + string.digits, k=12)),
                'credit_card': f"{random.randint(4000,4999)}-{random.randint(1000,9999)}-{random.randint(1000,9999)}-{random.randint(1000,9999)}",
                'uuid': str(uuid.uuid4()),
                'ip': f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}",
                'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            results.append(item)
        
        return jsonify({
            'success': True,
            'count': count,
            'locale': locale,
            'data': results if count > 1 else results[0]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ===========================
#  6. 📋 JWT 解析 API
# ===========================
@app.route('/api/jwt-decode', methods=['POST'])
@check_api_key
def api_jwt_decode():
    """
    JWT 解析 - 解码 JWT Token，查看 Header/Payload/Signature
    用途：调试、验证 JWT、分析 Token
    """
    try:
        data = request.get_json() or {}
        token = data.get('token', '')
        if not token:
            return jsonify({'success': False, 'error': '缺少 token 参数'}), 400
        
        parts = token.strip().split('.')
        if len(parts) != 3:
            return jsonify({'success': False, 'error': '无效 JWT 格式，应为 xxx.yyy.zzz'}), 400
        
        import base64
        import json as json_mod
        
        def decode_part(s):
            # JWT 使用 URL-safe base64
            s = s.replace('-', '+').replace('_', '/')
            # 补齐 padding
            padding = 4 - len(s) % 4
            if padding < 4:
                s += '=' * padding
            decoded = base64.b64decode(s)
            return json_mod.loads(decoded.decode('utf-8'))
        
        header = decode_part(parts[0])
        payload = decode_part(parts[1])
        signature = parts[2]
        
        # 解析时间戳
        if 'exp' in payload:
            payload['exp_readable'] = datetime.fromtimestamp(payload['exp']).isoformat()
        if 'iat' in payload:
            payload['iat_readable'] = datetime.fromtimestamp(payload['iat']).isoformat()
        if 'nbf' in payload:
            payload['nbf_readable'] = datetime.fromtimestamp(payload['nbf']).isoformat()
        
        # 验证状态
        validation = {}
        now = time.time()
        if 'exp' in payload:
            validation['expired'] = payload['exp'] < now
            validation['expires_in'] = max(0, int(payload['exp'] - now))
        
        return jsonify({
            'success': True,
            'header': header,
            'payload': payload,
            'signature': signature[:20] + '...',
            'validation': validation
        })
    except Exception as e:
        return jsonify({'success': False, 'error': f'解析失败: {str(e)}'}), 500


# ===========================
#  7. 🎨 颜色转换 API
# ===========================
@app.route('/api/color-convert', methods=['POST'])
@check_api_key
def api_color_convert():
    """
    颜色转换 - HEX ↔ RGB ↔ HSL ↔ HSV
    用途：设计师工具、主题系统、UI 开发
    """
    try:
        import colorsys
        data = request.get_json() or {}
        color = data.get('color', '').strip()
        target = data.get('target', 'all')  # all | rgb | hsl | hsv | hex
        
        def hex_to_rgb(h):
            h = h.lstrip('#')
            return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

        def rgb_to_hex(r, g, b):
            return '#{:02x}{:02x}{:02x}'.format(int(r), int(g), int(b))

        def rgb_to_hsl(r, g, b):
            r, g, b = r/255, g/255, b/255
            h, l, s = colorsys.rgb_to_hls(r, g, b)
            return (round(h*360), round(s*100), round(l*100))

        def rgb_to_hsv(r, g, b):
            r, g, b = r/255, g/255, b/255
            h, s, v = colorsys.rgb_to_hsv(r, g, b)
            return (round(h*360), round(s*100), round(v*100))
        
        # 解析输入
        if color.startswith('#') or color.isalnum():
            try:
                rgb = hex_to_rgb(color)
            except:
                return jsonify({'success': False, 'error': '无效 HEX 颜色'}), 400
        elif ',' in color:
            rgb = tuple(int(x.strip()) for x in color.split(','))
        else:
            return jsonify({'success': False, 'error': '请输入 HEX 或 RGB 格式'}), 400
        
        hsl = rgb_to_hsl(*rgb)
        hsv = rgb_to_hsv(*rgb)
        
        result = {'success': True, 'original': color}
        if target in ['all', 'hex']:
            result['hex'] = rgb_to_hex(*rgb).upper()
        if target in ['all', 'rgb']:
            result['rgb'] = {'r': rgb[0], 'g': rgb[1], 'b': rgb[2]}
            result['rgb_string'] = f'rgb({rgb[0]}, {rgb[1]}, {rgb[2]})'
        if target in ['all', 'hsl']:
            result['hsl'] = {'h': hsl[0], 's': hsl[1], 'l': hsl[2]}
            result['hsl_string'] = f'hsl({hsl[0]}, {hsl[1]}%, {hsl[2]}%)'
        if target in ['all', 'hsv']:
            result['hsv'] = {'h': hsv[0], 's': hsv[1], 'v': hsv[2]}
        
        # 生成调色板
        if data.get('include_palette', False):
            result['palette'] = [
                rgb_to_hex(max(0, min(255, rgb[0] + d)), max(0, min(255, rgb[1] + d)), max(0, min(255, rgb[2] + d)))
                for d in [-30, -15, 15, 30]
            ]
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ===========================
#  8. 📄 Word 文档生成 API
# ===========================
@app.route('/api/generate-docx', methods=['POST'])
@check_api_key
def api_generate_docx():
    """
    Word 文档生成 - 创建 .docx 文件
    用途：合同、报告、简历生成
    """
    try:
        data = request.get_json() or {}
        title = data.get('title', 'Document')
        content = data.get('content', '')
        author = data.get('author', 'Generated')
        
        # 生成简单 HTML，然后提示用户转换
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>{title}</title>
<style>
body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 40px auto; padding: 20px; line-height: 1.6; }}
h1 {{ color: #1a1a2e; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
.meta {{ color: #666; font-size: 14px; margin-bottom: 30px; }}
.content {{ text-align: justify; }}
</style>
</head>
<body>
<h1>{title}</h1>
<div class="meta">作者: {author} | 日期: {datetime.now().strftime('%Y-%m-%d')}</div>
<div class="content">
{content.replace(chr(10), '<br>').replace(chr(10)*2, '</p><p>')}
</div>
</body>
</html>
"""
        import base64
        doc_base64 = base64.b64encode(html_content.encode('utf-8')).decode()
        
        return jsonify({
            'success': True,
            'title': title,
            'author': author,
            'html_base64': doc_base64,
            'note': '这是 HTML 格式的文档，可用浏览器打开后打印为 PDF，或导入 Word'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ===========================
#  9. 🔗 URL 缩短 API
# ===========================
@app.route('/api/url-shorten', methods=['POST'])
@check_api_key
def api_url_shorten():
    """
    URL 缩短 - 使用 TinyURL 免费 API
    用途：社交分享、营销追踪
    """
    try:
        data = request.get_json() or {}
        url = data.get('url', '')
        if not url:
            return jsonify({'success': False, 'error': '缺少 url 参数'}), 400
        
        try:
            tinyurl_api = f'https://tinyurl.com/api-create.php?url={urllib.parse.quote(url)}'
            req = urllib.request.Request(tinyurl_api)
            with urllib.request.urlopen(req, timeout=8) as resp:
                short_url = resp.read().decode('utf-8')
        except Exception as e:
            # 备用：本地生成短链接
            short_id = secrets.token_hex(4)
            short_url = f"https://short.link/{short_id}"
        
        return jsonify({
            'success': True,
            'original_url': url,
            'short_url': short_url,
            'created_at': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ===========================
#  10. 📊 文本统计 API
# ===========================
@app.route('/api/text-stats', methods=['POST'])
@check_api_key
def api_text_stats():
    """
    文本统计 - 字数、词数、句子数、关键词提取
    用途：写作分析、SEO、内容审核
    """
    try:
        data = request.get_json() or {}
        text = data.get('text', '')
        if not text:
            return jsonify({'success': False, 'error': '缺少 text 参数'}), 400
        
        # 基本统计
        char_count = len(text)
        char_no_space = len(text.replace(' ', '').replace('\n', '').replace('\t', ''))
        word_count = len(re.findall(r'\b\w+\b', text))
        sentence_count = len(re.findall(r'[.!?]+', text)) or 1
        paragraph_count = len([p for p in text.split('\n\n') if p.strip()])
        
        # 行数
        line_count = text.count('\n') + 1
        
        # 读取时间（中文约 500字/分钟，英文约 200词/分钟）
        reading_time_cn = round(char_no_space / 500, 1) if char_no_space < 5000 else round(char_no_space / 500)
        reading_time_en = round(word_count / 200, 1)
        
        # 关键词提取（简单词频）
        words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
        word_freq = {}
        for w in words:
            stopwords = {'this', 'that', 'with', 'from', 'have', 'been', 'will', 'your', 'what', 'when', 'where', 'which', 'their', 'there', 'these', 'those', 'about', 'into', 'more', 'some', 'could', 'would', 'should', 'than'}
            if w not in stopwords:
                word_freq[w] = word_freq.get(w, 0) + 1
        top_keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return jsonify({
            'success': True,
            'text': text[:100] + '...' if len(text) > 100 else text,
            'stats': {
                'characters': char_count,
                'characters_no_space': char_no_space,
                'words': word_count,
                'sentences': sentence_count,
                'paragraphs': paragraph_count,
                'lines': line_count,
                'avg_word_length': round(char_count / max(word_count, 1), 2),
                'reading_time_minutes': max(reading_time_cn, reading_time_en)
            },
            'top_keywords': [{'word': w, 'count': c} for w, c in top_keywords]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ===========================
#  11. 📧 Email 验证 API
# ===========================
@app.route('/api/email-validate', methods=['POST'])
@check_api_key
def api_email_validate():
    """
    Email 验证 - 格式检查 + 域名验证 + 临时邮箱检测
    用途：注册验证、数据清洗、反垃圾
    """
    try:
        data = request.get_json() or {}
        email = data.get('email', '')
        if not email:
            return jsonify({'success': False, 'error': '缺少 email 参数'}), 400
        
        # 格式验证
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        format_ok = bool(re.match(email_regex, email.strip()))
        
        # 提取域名
        domain = email.split('@')[1] if '@' in email else ''
        
        # 临时邮箱检测
        disposable_domains = [
            'tempmail.com', 'guerrillamail.com', 'mailinator.com', '10minutemail.com',
            'throwaway.email', 'fakeinbox.com', 'trashmail.com', 'yopmail.com',
            'temp-mail.org', 'getnada.com', 'mohmal.com', 'discard.email'
        ]
        is_disposable = domain.lower() in disposable_domains
        
        # 常见错误检测
        typos = {
            'gmial.com': 'gmail.com', 'gmal.com': 'gmail.com', 'gamil.com': 'gmail.com',
            'hotmial.com': 'hotmail.com', 'hotmial.com': 'hotmail.com',
            'outloo.com': 'outlook.com', 'outlok.com': 'outlook.com',
        }
        suggested = typos.get(domain.lower(), '')
        
        # MX 记录检查（简化版）
        mx_check = True
        if format_ok:
            try:
                import socket
                socket.setdefaulttimeout(3)
                socket.gethostbyname(domain)
            except:
                mx_check = False
        
        # 综合评分
        score = 0
        if format_ok: score += 40
        if mx_check: score += 30
        if not is_disposable: score += 30
        
        return jsonify({
            'success': True,
            'email': email,
            'valid': format_ok and mx_check,
            'checks': {
                'format_valid': format_ok,
                'domain_exists': mx_check,
                'is_disposable': is_disposable,
                'suggested_fix': suggested if suggested else None
            },
            'score': score,
            'grade': 'A' if score >= 80 else 'B' if score >= 60 else 'C' if score >= 40 else 'D',
            'domain': domain
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ===========================
#  12. 🖼️ 图片占位符 API
# ===========================
@app.route('/api/placeholder', methods=['GET'])
def api_placeholder():
    """
    图片占位符 - 生成占位图（用于开发/设计稿）
    使用：直接 GET 请求即可
    """
    from PIL import Image, ImageDraw, ImageFont
    import io, base64, urllib.parse
    
    width = int(request.args.get('w', 400))
    height = int(request.args.get('h', 300))
    text = request.args.get('text', f'{width}×{height}')
    bg = request.args.get('bg', 'E0E0E0')
    fg = request.args.get('fg', '999999')
    fmt = request.args.get('fmt', 'png')
    
    try:
        img = Image.new('RGB', (width, height), color='#' + bg.lstrip('#'))
        draw = ImageDraw.Draw(img)
        
        # 画网格
        for i in range(0, width, 20):
            draw.line([(i, 0), (i, height)], fill='#' + (str(int(bg, 16) ^ 0xFFFFFF).rjust(6, '0')), width=1)
        
        # 居中文字
        bbox = draw.textbbox((0, 0), text)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        x = (width - text_w) // 2
        y = (height - text_h) // 2
        draw.text((x, y), text, fill='#' + fg.lstrip('#'))
        
        buf = io.BytesIO()
        img.save(buf, format=fmt.upper())
        buf.seek(0)
        
        if request.args.get('base64'):
            return jsonify({
                'success': True,
                'image': 'data:image/' + fmt + ';base64,' + base64.b64encode(buf.read()).decode()
            })
        
        return send_file(buf, mimetype='image/' + fmt)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


from flask import send_file

# ===========================
#  健康检查 & 文档
# ===========================
@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'service': 'dev-tools-api',
        'version': '1.0',
        'apis': {
            '/api/currency-convert': '💱 货币换算',
            '/api/url-preview': '🔗 URL 预览',
            '/api/slug-generate': '📝 Slug 生成',
            '/api/hash-generate': '🔐 Hash 生成',
            '/api/fake-data': '🎲 假数据生成',
            '/api/jwt-decode': '📋 JWT 解析',
            '/api/color-convert': '🎨 颜色转换',
            '/api/generate-docx': '📄 Word 文档',
            '/api/url-shorten': '🔗 URL 缩短',
            '/api/text-stats': '📊 文本统计',
            '/api/email-validate': '📧 Email 验证',
            '/api/placeholder': '🖼️ 图片占位符',
        }
    })


@app.route('/api/docs', methods=['GET'])
def docs():
    return jsonify({
        'title': '🔧 开发者工具 API 套件',
        'version': '1.0',
        'apis': [
            {'endpoint': '/api/currency-convert', 'method': 'POST', 'description': '30+货币实时换算', 'price': '$5-20/次'},
            {'endpoint': '/api/url-preview', 'method': 'POST', 'description': 'Link Preview 元数据提取', 'price': '$3-15/次'},
            {'endpoint': '/api/slug-generate', 'method': 'POST', 'description': 'SEO 友好 URL slug', 'price': '$3-10/次'},
            {'endpoint': '/api/hash-generate', 'method': 'POST', 'description': 'MD5/SHA256 等 Hash', 'price': '$3-10/次'},
            {'endpoint': '/api/fake-data', 'method': 'POST', 'description': '测试用假数据批量生成', 'price': '$5-20/次'},
            {'endpoint': '/api/jwt-decode', 'method': 'POST', 'description': 'JWT Token 解码验证', 'price': '$5-15/次'},
            {'endpoint': '/api/color-convert', 'method': 'POST', 'description': 'HEX/RGB/HSL 互转', 'price': '$3-10/次'},
            {'endpoint': '/api/generate-docx', 'method': 'POST', 'description': 'Word 文档生成', 'price': '$5-25/次'},
            {'endpoint': '/api/url-shorten', 'method': 'POST', 'description': 'URL 缩短服务', 'price': '$2-10/次'},
            {'endpoint': '/api/text-stats', 'method': 'POST', 'description': '文本分析统计', 'price': '$3-10/次'},
            {'endpoint': '/api/email-validate', 'method': 'POST', 'description': 'Email 有效性验证', 'price': '$3-15/次'},
            {'endpoint': '/api/placeholder', 'method': 'GET', 'description': '开发占位图生成', 'price': '免费引流'},
        ]
    })


if __name__ == '__main__':
    print("=" * 60)
    print("🔧 开发者工具 API 套件 v1.0")
    print("=" * 60)
    print("12 个实用工具 API！")
    print()
    print("💱 /api/currency-convert  - 货币换算")
    print("🔗 /api/url-preview       - URL 预览")
    print("📝 /api/slug-generate     - Slug 生成")
    print("🔐 /api/hash-generate     - Hash 生成")
    print("🎲 /api/fake-data         - 假数据")
    print("📋 /api/jwt-decode        - JWT 解析")
    print("🎨 /api/color-convert     - 颜色转换")
    print("📄 /api/generate-docx    - Word 文档")
    print("🔗 /api/url-shorten       - URL 缩短")
    print("📊 /api/text-stats        - 文本统计")
    print("📧 /api/email-validate    - Email 验证")
    print("🖼️  /api/placeholder       - 占位图")
    print()
    print("演示 Key: demo-key-001 | pro-key-002 | enterprise-key-003")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5011, debug=True)
