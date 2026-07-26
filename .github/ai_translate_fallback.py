#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AI 翻译字典未覆盖的剩余英文 — 零外部依赖，用 urllib 调 Google Translate"""

import re, os, sys, time, glob, json, urllib.request, urllib.parse

WORKSPACE = os.environ.get("GITHUB_WORKSPACE", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def google_translate(text, source='en', target='zh-CN'):
    """用 Google Translate 免费 API 翻译（无需 API Key）"""
    # Google Translate 内部 API
    url = "https://translate.googleapis.com/translate_a/single"
    params = {
        'client': 'gtx',
        'sl': source,
        'tl': target,
        'dt': 't',
        'q': text
    }
    full_url = url + '?' + urllib.parse.urlencode(params)
    
    for attempt in range(3):
        try:
            req = urllib.request.Request(full_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
            # Google Translate returns [[[translated, original, ...]], ...]
            parts = []
            for segment in data[0]:
                if segment[0]:
                    parts.append(segment[0])
            return ''.join(parts)
        except Exception as e:
            if attempt == 2:
                return None
            time.sleep(1)
    return None


def translate_batch(texts):
    """逐条翻译"""
    result = {}
    for text in texts:
        t = text.strip()
        if not re.search(r'[a-zA-Z]{5,}', t) or re.search(r'[\u4e00-\u9fff]', t):
            continue
        translated = google_translate(t)
        if translated and translated != t:
            result[t] = translated
            print(f"  EN: {t[:80]}")
            print(f"  ZH: {translated[:80]}")
        time.sleep(0.3)  # 避免频率限制
    return result


def extract_texts(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except:
        return []
    
    items = []
    # help:  "..." 全英文长句
    for m in re.finditer(r'help:\s+"(.*?)"', content, re.DOTALL):
        t = m.group(1).replace('\n', ' ').strip()
        for s in re.split(r'(?<=[.!?])\s+', t):
            s = s.strip()
            if re.search(r'[a-zA-Z]{15,}', s) and not re.search(r'[\u4e00-\u9fff]', s):
                items.append(s)
    
    # /// 长英文
    for m in re.finditer(r'/// (.+)', content):
        t = m.group(1).strip()
        if re.search(r'[a-zA-Z]{20,}', t) and not re.search(r'[\u4e00-\u9fff]', t):
            items.append(t)
    
    return list(dict.fromkeys(items))


def apply_translations(filepath, translations):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except:
        return 0
    
    n = 0
    for en, zh in translations.items():
        if en in content and en != zh:
            content = content.replace(en, zh)
            n += 1
    
    if n:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
    return n


def main():
    print("Using Google Translate free API (no pip needed)")
    
    priority = [
        os.path.join(WORKSPACE, 'crates', 'zeroclaw-config', 'src', 'sections.rs'),
        os.path.join(WORKSPACE, 'crates', 'zeroclaw-config', 'src', 'presets.rs'),
        os.path.join(WORKSPACE, 'crates', 'zeroclaw-config', 'src', 'schema.rs'),
    ]
    
    total = 0
    for fp in priority:
        if not os.path.exists(fp):
            continue
        texts = extract_texts(fp)
        if not texts:
            continue
        
        rel = fp.replace(WORKSPACE + os.sep, '')
        print(f"\n{rel}: {len(texts)} untranslated strings")
        
        translations = translate_batch(texts)
        n = apply_translations(fp, translations)
        total += n
    
    print(f"\nAI translated: {total} strings")

if __name__ == "__main__":
    main()
