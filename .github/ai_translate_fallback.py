#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AI 翻译长句 help://// 注释 — 零外部依赖"""

import re, os, sys, time, json, urllib.request, urllib.parse

WORKSPACE = os.environ.get("GITHUB_WORKSPACE", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


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
            return ''.join(parts)
        except Exception as e:
            if attempt == 2:
                print(f"  [API-FAIL] {text[:50]}...: {e}")
                return text
            time.sleep(2)
    return text


def main():
    targets = [
        os.path.join(WORKSPACE, 'crates', 'zeroclaw-config', 'src', 'sections.rs'),
        os.path.join(WORKSPACE, 'crates', 'zeroclaw-config', 'src', 'presets.rs'),
        os.path.join(WORKSPACE, 'crates', 'zeroclaw-config', 'src', 'schema.rs'),
    ]
    
    for fp in targets:
        if not os.path.exists(fp):
            continue
        
        with open(fp, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original = content
        rel = fp.replace(WORKSPACE + os.sep, '')
        print(f"\n=== {rel} ===")
        
        # ── 1. help:  "..." 多行 ──
        def repl_help(m):
            text = m.group(2)
            # 如果已经是中文，跳过
            if re.search(r'[\u4e00-\u9fff]', text):
                return m.group(0)
            # 折叠换行符成一个段落（保持 Rust 字符串拼接）
            flat = text.replace('\\n', ' ').replace('\n', ' ')
            flat = flat.replace('\\\"', '"').strip()
            if not re.search(r'[a-zA-Z]{10,}', flat):
                return m.group(0)
            translated = google_translate(flat)
            # 如果翻译失败（无中文），保留原文
            if not re.search(r'[\u4e00-\u9fff]', translated):
                return m.group(0)
            print(f"  help: {flat[:60]}...")
            print(f"  →   {translated[:60]}...")
            return f'{m.group(1)}"{translated}"'
        
        content = re.sub(r'(help:\s+)"(.*?)"\s*,', repl_help, content, flags=re.DOTALL)
        
        # ── 2. /// 文档注释（中文优先跳过）──
        def repl_doc(m):
            text = m.group(1).strip()
            if re.search(r'[\u4e00-\u9fff]', text):
                return m.group(0)
            if not re.search(r'[a-zA-Z]{15,}', text):
                return m.group(0)
            translated = google_translate(text)
            if not re.search(r'[\u4e00-\u9fff]', translated):
                return m.group(0)
            print(f"  doc:  {text[:60]}...")
            print(f"  →    {translated[:60]}...")
            return f'/// {translated}'
        
        content = re.sub(r'/// (.+)', repl_doc, content)
        
        # ── 3. description = "..." （长句） ──
        def repl_desc(m):
            text = m.group(2)
            if re.search(r'[\u4e00-\u9fff]', text):
                return m.group(0)
            if len(text) < 50 or not re.search(r'[a-zA-Z]{10,}', text):
                return m.group(0)
            translated = google_translate(text)
            if not re.search(r'[\u4e00-\u9fff]', translated):
                return m.group(0)
            print(f"  desc: {text[:60]}...")
            print(f"  →    {translated[:60]}...")
            return f'{m.group(1)}"{translated}"'
        
        content = re.sub(r'(description\s*=\s*)"([^"]{50,})"', repl_desc, content)
        
        # ── 4. fn description(&self) -> &str { "..." } ──
        def repl_fn_desc(m):
            text = m.group(2)
            if re.search(r'[\u4e00-\u9fff]', text):
                return m.group(0)
            if not re.search(r'[a-zA-Z]{15,}', text):
                return m.group(0)
            translated = google_translate(text)
            if not re.search(r'[\u4e00-\u9fff]', translated):
                return m.group(0)
            print(f"  tool: {text[:60]}...")
            print(f"  →     {translated[:60]}...")
            return f'{m.group(1)}"{translated}"'
        
        content = re.sub(
            r'(fn description\(&self\)\s*->\s*&str\s*\{\s*)"([^"]+)"(\s*\})',
            repl_fn_desc,
            content
        )
        
        if content != original:
            with open(fp, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  ✅ {rel} 已更新")
        else:
            print(f"  ⏭ {rel} 无变化")

if __name__ == "__main__":
    main()