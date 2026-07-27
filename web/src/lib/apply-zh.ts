// Web 面板加载时，自动将 Rust 源码产生的英文替换为中文
import ZH_RUST_LABELS from './zh-rust-labels';

function applyLabels() {
  const walker = document.createTreeWalker(
    document.body,
    NodeFilter.SHOW_TEXT,
    { acceptNode: (node) => {
      // 跳过脚本、样式、已包含中文的节点
      const parent = node.parentElement;
      if (!parent) return NodeFilter.FILTER_REJECT;
      const tag = parent.tagName;
      if (tag === 'SCRIPT' || tag === 'STYLE' || tag === 'CODE' || tag === 'PRE') {
        return NodeFilter.FILTER_REJECT;
      }
      return NodeFilter.FILTER_ACCEPT;
    }}
  );

  const nodesToReplace: [ChildNode, string][] = [];
  while (walker.nextNode()) {
    const node = walker.currentNode;
    if (!node || !node.textContent) continue;
    
    let text = node.textContent;
    let changed = false;
    
    // 先查完整匹配
    if (ZH_RUST_LABELS[text.trim()]) {
      text = ZH_RUST_LABELS[text.trim()];
      changed = true;
    }
    
    if (changed) {
      nodesToReplace.push([node, text]);
    }
  }

  // 批量替换（避免遍历中修改 DOM）
  for (const [node, newText] of nodesToReplace) {
    (node as Text).textContent = newText;
  }
}

// 页面加载
document.addEventListener('DOMContentLoaded', applyLabels);

// SPA 路由变化
let lastUrl = location.href;
setInterval(() => {
  if (location.href !== lastUrl) {
    lastUrl = location.href;
    setTimeout(applyLabels, 300);
  }
}, 500);
