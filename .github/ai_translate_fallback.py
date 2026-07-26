#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AI 翻译 help://// 注释 + 工具描述 — 安全转义，不破坏 Rust 语法"""

import re, os, sys, time, json, urllib.request, urllib.parse

WORKSPACE = os.environ.get("GITHUB_WORKSPACE", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def safe_escape(text):
    """用 json.dumps 获得安全转义，再去掉外层引号"""
    return json.dumps(text, ensure_ascii=False)[1:-1]


def google_translate(text, source='en', target='zh-CN'):
    if not text or not text.strip():
        return text
    
    url = "https://translate.googleapis.com/translate_a/single?" + urllib.parse.urlencode({
        'client': 'gtx', 'sl': source, 'tl': target, 'dt': 't', 'q': text
    })
    
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode())
            parts = []
            for segment in data[0]:
                if segment[0]:
                    parts.append(segment[0])
            result = ''.join(parts).strip()
            if not re.search(r'[\u4e00-\u9fff]', result):
                return text
            return result
        except:
            if attempt == 2:
                return text
            time.sleep(2)
    return text


def main():
    targets = [
        os.path.join(WORKSPACE, 'crates', 'zeroclaw-config', 'src', 'sections.rs'),
        os.path.join(WORKSPACE, 'crates', 'zeroclaw-config', 'src', 'presets.rs'),
        os.path.join(WORKSPACE, 'crates', 'zeroclaw-config', 'src', 'schema.rs'),
        os.path.join(WORKSPACE, 'crates', 'zeroclaw-runtime', 'src', 'tools'),
    ]
    
    for fp in targets:
        if not os.path.exists(fp):
            continue
        
        with open(fp, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original = content
        rel = fp.replace(WORKSPACE + os.sep, '')
        print(f"\n=== {rel} ===")
        
        # ── 1. help:  "..." → AI 翻译 ──
        def repl_help(m):
            text = m.group(2)
            if re.search(r'[\u4e00-\u9fff]', text):
                return m.group(0)
            # 合并多行
            flat = text.replace('\\\n', ' ').replace('\n', ' ').replace('\\"', '"').strip()
            if not re.search(r'[a-zA-Z]{10,}', flat):
                return m.group(0)
            translated = google_translate(flat)
            if translated == flat or translated == text:
                return m.group(0)
            escaped = safe_escape(translated)
            print(f"  help: {flat[:60]}...")
            print(f"  →    {translated[:60]}...")
            return f'{m.group(1)}"{escaped}"'
        
        content = re.sub(r'(help:\s+)"(.*?)"(\s*,)', repl_help, content, flags=re.DOTALL)
        
        # ── 2. /// 文档注释 → AI 翻译 ──
        def repl_doc(m):
            text = m.group(1).strip()
            if re.search(r'[\u4e00-\u9fff]', text):
                return m.group(0)
            if not re.search(r'[a-zA-Z]{15,}', text):
                return m.group(0)
            translated = google_translate(text)
            if translated == text:
                return m.group(0)
            escaped = safe_escape(translated)
            print(f"  doc:  {text[:60]}...")
            print(f"  →    {translated[:60]}...")
            return f'/// {escaped}'
        
        content = re.sub(r'/// (.+)', repl_doc, content)
        
        # ── 3. fn description() { "..." } → AI 翻译 ──
        def repl_fn_desc(m):
            text = m.group(2)
            if re.search(r'[\u4e00-\u9fff]', text):
                return m.group(0)
            if not re.search(r'[a-zA-Z]{15,}', text):
                return m.group(0)
            translated = google_translate(text)
            if translated == text:
                return m.group(0)
            escaped = safe_escape(translated)
            print(f"  tool: {text[:60]}...")
            print(f"  →    {translated[:60]}...")
            return f'{m.group(1)}"{escaped}"{m.group(3)}'
        
        content = re.sub(
            r'(fn description\(&self\)\s*->\s*&str\s*\{\s*)"([^"]+)"(\s*\})',
            repl_fn_desc, content
        )
        
        if content != original:
            with open(fp, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  OK updated")
        else:
            print(f"  (no changes)")

if __name__ == "__main__":
    main()
