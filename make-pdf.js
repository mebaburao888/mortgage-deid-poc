const fs = require('fs');
const path = require('path');

// Read markdown
const md = fs.readFileSync('mortgage-deid-architecture.md', 'utf8');

// Simple markdown to HTML conversion
function mdToHtml(text) {
  return text
    // Code blocks
    .replace(/```[\w]*\n([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
    // Inline code
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    // H1
    .replace(/^# (.+)$/gm, '<h1>$1</h1>')
    // H2
    .replace(/^## (.+)$/gm, '<h2>$1</h2>')
    // H3
    .replace(/^### (.+)$/gm, '<h3>$1</h3>')
    // Bold
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    // Italic/blockquote style
    .replace(/^> (.+)$/gm, '<blockquote>$1</blockquote>')
    // HR
    .replace(/^---$/gm, '<hr>')
    // Tables
    .replace(/\|(.+)\|\n\|[-| :]+\|\n((?:\|.+\|\n?)+)/g, (match, header, rows) => {
      const ths = header.split('|').filter(c => c.trim()).map(c => `<th>${c.trim()}</th>`).join('');
      const trs = rows.trim().split('\n').map(row => {
        const tds = row.split('|').filter(c => c.trim()).map(c => `<td>${c.trim()}</td>`).join('');
        return `<tr>${tds}</tr>`;
      }).join('');
      return `<table><thead><tr>${ths}</tr></thead><tbody>${trs}</tbody></table>`;
    })
    // Unordered list items
    .replace(/^- (.+)$/gm, '<li>$1</li>')
    // Numbered list items
    .replace(/^\d+\. (.+)$/gm, '<li>$1</li>')
    // Wrap consecutive <li> in <ul>
    .replace(/(<li>.*<\/li>\n?)+/g, match => `<ul>${match}</ul>`)
    // Paragraphs (double newline)
    .replace(/\n\n(?!<)/g, '</p><p>')
    .replace(/^(?!<)/, '<p>')
    .replace(/(?!>)$/, '</p>');
}

const html = `<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
    font-size: 13px;
    line-height: 1.6;
    color: #1a1a1a;
    padding: 48px 56px;
    max-width: 900px;
    margin: 0 auto;
  }
  h1 {
    font-size: 24px;
    font-weight: 700;
    margin: 0 0 8px 0;
    color: #0f172a;
    border-bottom: 2px solid #0f172a;
    padding-bottom: 8px;
  }
  h2 {
    font-size: 17px;
    font-weight: 700;
    margin: 28px 0 10px 0;
    color: #0f172a;
    border-bottom: 1px solid #e2e8f0;
    padding-bottom: 4px;
  }
  h3 {
    font-size: 14px;
    font-weight: 700;
    margin: 20px 0 8px 0;
    color: #334155;
  }
  p { margin: 8px 0; }
  pre {
    background: #f1f5f9;
    border: 1px solid #e2e8f0;
    border-radius: 4px;
    padding: 12px 14px;
    font-size: 11px;
    overflow: auto;
    margin: 10px 0;
    font-family: 'Consolas', 'Monaco', monospace;
    white-space: pre-wrap;
    word-break: break-word;
  }
  code {
    font-family: 'Consolas', 'Monaco', monospace;
    font-size: 11px;
    background: #f1f5f9;
    padding: 1px 4px;
    border-radius: 3px;
  }
  pre code { background: none; padding: 0; font-size: inherit; }
  blockquote {
    border-left: 4px solid #3b82f6;
    background: #eff6ff;
    padding: 10px 14px;
    margin: 12px 0;
    font-style: italic;
    color: #1e40af;
    border-radius: 0 4px 4px 0;
  }
  table {
    width: 100%;
    border-collapse: collapse;
    margin: 12px 0;
    font-size: 12px;
  }
  th {
    background: #0f172a;
    color: white;
    padding: 8px 12px;
    text-align: left;
    font-weight: 600;
  }
  td {
    padding: 7px 12px;
    border-bottom: 1px solid #e2e8f0;
  }
  tr:nth-child(even) td { background: #f8fafc; }
  ul { margin: 8px 0 8px 20px; }
  li { margin: 3px 0; }
  hr {
    border: none;
    border-top: 1px solid #e2e8f0;
    margin: 24px 0;
  }
  strong { font-weight: 700; }
  .subtitle {
    color: #64748b;
    font-size: 13px;
    margin-bottom: 24px;
  }
  @page { margin: 0; }
</style>
</head>
<body>
${mdToHtml(md)}
</body>
</html>`;

fs.writeFileSync('mortgage-deid-architecture.html', html);
console.log('HTML written');
