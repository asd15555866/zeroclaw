#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Actions: AI 翻译字典未覆盖的剩余英文。

原理：
  1. 翻译脚本已运行 → 字典能翻的都翻了
  2. 本脚本扫描修改过的文件 → 找出仍为英文的句子（含 5+ 个字母）
  3. 调用 Google Translate 免费 API 逐句翻译
  4. 替换回文件
"""

import re, os, sys, subprocess, time, glob

WORKSPACE = os.environ.get("GITHUB_WORKSPACE", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def install_translator():
    """安装翻译库"""
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'deep-translator', '-q'],
                   check=False, capture_output=True)


def translate_batch(texts, max_retries=3):
    """批量翻译英文→中文，带重试"""
    from deep_translator import GoogleTranslator
    
    if not texts:
        return {}
    
    # 去掉纯变量/代码片段
    valid = []
    for t in texts:
        t_clean = t.strip()
        if re.search(r'[a-zA-Z]{5,}', t_clean) and not re.search(r'[\u4e00-\u9fff]', t_clean):
            valid.append(t_clean)
    
    if not valid:
        return {}
    
    result = {}
    # Google Translate 逐条翻译
    for text in valid:
        for attempt in range(max_retries):
            try:
                translated = GoogleTranslator(source='en', target='zh-CN').translate(text)
                result[text] = translated
                break
            except Exception as e:
                if attempt == max_retries - 1:
                    print(f"  [FAIL] '{text[:50]}...': {e}")
                time.sleep(1)
    
    return result


def extract_untranslated(filepath):
    """从文件中提取仍未翻译的英文文本段"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except:
        return []
    
    untranslated = []
    
    # 模式 1: help:  "..." 中的全英文段落
    for m in re.finditer(r'help:\s+"(.*?)"', content, re.DOTALL):
        text = m.group(1).strip()
        # 分割续行并重新合并为句子
        text = text.replace('\\\n', ' ').replace('\n', ' ')
        # 按句子分割（. ! ? 后）
        sentences = re.split(r'(?<=[.!?])\s+', text)
        for s in sentences:
            s = s.strip().strip('"').strip()
            if re.search(r'[a-zA-Z]{10,}', s) and not re.search(r'[\u4e00-\u9fff]', s):
                untranslated.append(('help', s))
    
    # 模式 2: /// 文档注释中全英文的长句
    for m in re.finditer(r'/// (.+)', content):
        text = m.group(1).strip()
        if re.search(r'[a-zA-Z]{15,}', text) and not re.search(r'[\u4e00-\u9fff]', text):
            untranslated.append(('doc', text))
    
    # 模式 3: description = "..." 中的全英文
    for m in re.finditer(r'description\s*=\s*"([^"]+)"', content):
        text = m.group(1).strip()
        if re.search(r'[a-zA-Z]{10,}', text) and not re.search(r'[\u4e00-\u9fff]', text):
            untranslated.append(('desc', text))
    
    # 去重
    seen = set()
    unique = []
    for typ, text in untranslated:
        if text not in seen:
            seen.add(text)
            unique.append((typ, text))
    
    return unique


def apply_translations(filepath, translations):
    """把 AI 翻译的结果写回文件"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except:
        return 0
    
    replaced = 0
    for en_text, zh_text in translations.items():
        if en_text in content and en_text != zh_text:
            content = content.replace(en_text, zh_text)
            replaced += 1
    
    if replaced > 0:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
    
    return replaced


def main():
    print("Installing translator...")
    install_translator()
    
    # 只处理修改过的 .rs 文件
    rs_files = glob.glob(os.path.join(WORKSPACE, 'crates', '**', '*.rs'), recursive=True)
    
    priority = [
        os.path.join(WORKSPACE, 'crates', 'zeroclaw-config', 'src', 'sections.rs'),
        os.path.join(WORKSPACE, 'crates', 'zeroclaw-config', 'src', 'presets.rs'),
        os.path.join(WORKSPACE, 'crates', 'zeroclaw-config', 'src', 'schema.rs'),
    ]
    
    print(f"\nScanning {len(rs_files)} files for untranslated English...")
    
    total_translated = 0
    for fp in priority:
        if not os.path.exists(fp):
            continue
        
        untranslated = extract_untranslated(fp)
        if not untranslated:
            continue
        
        rel = fp.replace(WORKSPACE + os.sep, '')
        print(f"\n{rel}: {len(untranslated)} untranslated strings")
        
        # 只取英文文本部分
        texts = [t for _, t in untranslated]
        translations = translate_batch(texts)
        
        if translations:
            replaced = apply_translations(fp, translations)
            total_translated += replaced
            for en, zh in translations.items():
                if en != zh:
                    print(f"  EN: {en[:80]}...")
                    print(f"  ZH: {zh[:80]}...")
                    print()
    
    print(f"\nAI translated: {total_translated} strings")

if __name__ == "__main__":
    main()
