from datetime import datetime
import html
import json as _json
from pathlib import Path

import pandas as pd
from rich import print


# 注意：内联 <script> 的常见陷阱与修复要点
# 1) 在 <script> 中注入 JSON 时，切勿做 HTML 转义（例如将引号变为 &quot;）。
#    否则脚本会在解析时发生语法错误，导致后续函数（如 window.exportCSV / window.toggleAll）未定义。
#    本文件通过直接注入 JSON 字符串（不经 HTML 转义）解决。
# 2) 需要在内联 onclick 调用里可见函数时，将函数挂载到 window，例如：
#    window.exportCSV = function() { ... }；window.toggleAll = function() { ... }。
#    否则在某些环境/策略下，函数不在全局作用域会触发 ReferenceError。
# 3) JS 字符串中的换行应使用 "\\n"（字面量转义）拼接到 CSV，避免实际换行打断脚本。


def df_to_html(
    df: pd.DataFrame,
    title: str,
    src_dir_hint: str = "",
    with_checkbox: bool = False,
) -> str:
    """
    生成可视化 HTML，with_checkbox=True 时包含“标记删除+导出未选中”的交互。
    """

    def esc(x: str) -> str:
        return html.escape(x or "")

    # 列类型推断：image_path / code / text
    image_exts = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tif", ".tiff"}

    def looks_like_path(val: str) -> bool:
        if not val:
            return False
        s = str(val)
        return ("/" in s or "\\" in s) and "." in Path(s).name

    def looks_like_image(val: str) -> bool:
        try:
            return Path(str(val)).suffix.lower() in image_exts
        except Exception:
            return False

    def looks_like_json(val: str) -> bool:
        """检测字符串是否看起来像JSON格式"""
        if not val:
            return False
        s = str(val).strip()
        if (s.startswith("{") and s.endswith("}")) or (s.startswith("[") and s.endswith("]")):
            if '"' in s and (":" in s or "," in s):
                return True
        return False

    column_specs = []  # [{name, type}]
    for col in df.columns:
        name_lc = str(col).lower()
        sample_vals = df[col].dropna().astype(str).head(20).tolist()
        any_path_like = any(looks_like_path(v) for v in sample_vals)
        any_image_like = any(looks_like_image(v) for v in sample_vals)
        any_json_like = any(looks_like_json(v) for v in sample_vals)
        if any_image_like or (
            any_path_like
            and ("img" in name_lc or "image" in name_lc or "pic" in name_lc)
        ):
            col_type = "image_path"
        elif any_path_like or any_json_like or ("path" in name_lc or "file" in name_lc):
            col_type = "code"
        else:
            col_type = "text"
        column_specs.append({"name": str(col), "type": col_type})

    # 构建表格行：根据 with_checkbox 决定是否添加勾选列
    rows_html = []
    for idx, r in df.iterrows():
        cells_html = []
        for spec in column_specs:
            col_name = spec["name"]
            col_type = spec["type"]
            val = r.get(col_name, "")
            if isinstance(val, list):
                val_str = str(val)
            elif val is None or pd.isna(val):
                val_str = ""
            else:
                val_str = str(val)
            if col_type == "image_path":
                img_onclick = ' onclick="openLightbox(this.src)"' if with_checkbox else ""
                cells_html.append(
                    f"""
        <td style="padding:12px;vertical-align:top;border-bottom:1px solid #e5e7eb;">
          <div style="display:flex;gap:10px;align-items:center;">
            <img class="zoomable-img" src="{esc(val_str)}" alt="{esc(col_name)}" style="width:min(100%, 480px);height:auto;border:1px solid #e5e7eb;border-radius:8px;display:block;cursor:pointer;"{img_onclick} />
          </div>
          <div class="cell-path" title="{esc(val_str)}" style="color:#6b7280;font-size:12px;margin-top:8px;max-width:480px;white-space:pre-wrap;word-break:break-all;">{esc(val_str)}</div>
        </td>
                    """
                )
            elif col_type == "code":
                cells_html.append(
                    f"""
        <td style="padding:12px;vertical-align:top;border-bottom:1px solid #e5e7eb;">
          <div class="cell-path" style="font-family:ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace; font-size:12px; color:#374151; word-break:break-all;">{esc(val_str)}</div>
        </td>
                    """
                )
            else:
                cells_html.append(
                    f"""
        <td style="padding:12px;vertical-align:top;border-bottom:1px solid #e5e7eb;white-space:pre-wrap;">{esc(val_str)}</td>
                    """
                )

        row_cells = []
        if with_checkbox:
            row_cells.append(
                """
        <td style="padding:12px;vertical-align:top;border-bottom:1px solid #e5e7eb;text-align:center;">
          <input type="checkbox" class="row-check" />
        </td>
                """
            )
        row_cells.append(
            f"""
        <td style="padding:12px;vertical-align:top;border-bottom:1px solid #e5e7eb;text-align:center;color:#6b7280;">{esc(str(idx))}</td>
            """
        )
        row_cells.extend(cells_html)

        rows_html.append(
            f"""
      <tr>
        {"".join(row_cells)}
      </tr>
            """
        )

    colgroup_parts = []
    if with_checkbox:
        colgroup_parts.append('<col style="width: 6%;" />')  # 选择
    colgroup_parts.append('<col style="width: 6%;" />')  # 索引
    for spec in column_specs:
        if spec["type"] == "image_path":
            colgroup_parts.append('<col style="width: 26%;" />')
        else:
            colgroup_parts.append('<col style="width: 16%;" />')

    header_cells = []
    if with_checkbox:
        header_cells.append('<th style="text-align:center;">标记删除</th>')
    header_cells.append('<th style="text-align:center;">索引</th>')
    for spec in column_specs:
        label = esc(spec["name"])
        header_cells.append(f"<th>{label}</th>")

    toolbar_html = ""
    if with_checkbox:
        toolbar_html = """
  <div class="toolbar">
    <label style="display:flex;align-items:center;gap:6px;">
      <input id="check-all" type="checkbox" onclick="toggleAll(this)" />
      <span>全选</span>
    </label>
    <button class="btn secondary" onclick="exportCSV()">导出未选中为CSV</button>
  </div>
        """

    column_specs_json = _json.dumps(column_specs, ensure_ascii=False)

    checkbox_script = ""
    if with_checkbox:
        checkbox_script = f"""
  <script>
    const columnSpecs = {column_specs_json};

    window.toggleAll = function(source){{
      const checks = document.querySelectorAll('.row-check');
      checks.forEach(c => {{ c.checked = source.checked; }});
    }}
    window.exportCSV = function(){{
      const rows = Array.from(document.querySelectorAll('tbody tr'));
      const header = ['index', ...columnSpecs.map(s => s.name)];
      const data = [header];
      rows.forEach(tr => {{
        const checkbox = tr.querySelector('.row-check');
        if (checkbox && checkbox.checked) return; // 勾选表示删除，导出未勾选
        const tds = tr.querySelectorAll('td');
        if (tds.length < 2) return; // 选择 + 索引
        const indexCell = tds[1];
        const idxText = (indexCell ? indexCell.textContent : '').trim();
        const values = [];
        for (let i = 0; i < columnSpecs.length; i++) {{
          const td = tds[2 + i];
          const spec = columnSpecs[i];
          if (!td) {{ values.push(''); continue; }}
          if (spec.type === 'image_path' || spec.type === 'code') {{
            const div = td.querySelector('.cell-path');
            values.push((div ? div.textContent : td.textContent).trim());
          }} else {{
            values.push((td.textContent || '').trim());
          }}
        }}
        data.push([idxText, ...values]);
      }});
      const esc = (s) => {{
        if (s == null) return '';
        s = String(s);
        if (s.includes('"') || s.includes(',') || s.includes('\\n')) {{
          return '"' + s.replaceAll('"','""') + '"';
        }}
        return s;
      }};
      const csv = data.map(row => row.map(esc).join(',')).join('\\n');
      const blob = new Blob([csv], {{ type: 'text/csv;charset=utf-8;' }});
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      const now = new Date();
      const month = String(now.getMonth() + 1).padStart(2, '0');
      const day = String(now.getDate()).padStart(2, '0');
      const hour = String(now.getHours()).padStart(2, '0');
      const minute = String(now.getMinutes()).padStart(2, '0');
      const date = month + '_' + day + '_' + hour + '_' + minute;
      a.href = url;
      a.download = (document.title || 'kept') + '_' + date + '.csv';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }}
  </script>
        """

    lightbox_script = """
  <script>
    (function() {
      const lb = document.getElementById('lightbox');
      const im = document.getElementById('lightbox-img');
      function openLightbox(src) {
        if (!lb || !im) return;
        im.src = src || '';
        lb.style.display = 'flex';
      }
      function closeLightbox() {
        if (!lb || !im) return;
        im.src = '';
        lb.style.display = 'none';
      }
      window.openLightbox = openLightbox;
      window.closeLightbox = closeLightbox;
      if (lb) {
        lb.addEventListener('click', function() {
          closeLightbox();
        });
      }
      document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
          closeLightbox();
        }
      });
      document.addEventListener('click', function(e) {
        const target = e.target;
        if (target && target.classList && target.classList.contains('zoomable-img')) {
          openLightbox(target.src);
        }
      });
    })();
  </script>
    """

    return f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{esc(title)}</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'Noto Sans', 'PingFang SC', 'Microsoft YaHei', sans-serif; margin: 16px; color: #1f2937; }}
    h1 {{ font-size: 22px; margin: 0 0 12px; }}
    .meta {{ color: #6b7280; font-size: 12px; margin-bottom: 16px; }}
    table {{ width: 100%; border-collapse: collapse; table-layout: fixed; }}
    th, td {{ word-break: break-word; }}
    th {{ text-align:left; padding:12px; border-bottom:2px solid #e5e7eb; }}
    .toolbar {{ display:flex; gap:10px; margin: 8px 0 14px; flex-wrap: wrap; }}
    .btn {{ background:#111827; color:white; border:1px solid #111827; padding:8px 12px; border-radius:8px; cursor:pointer; }}
    .btn.secondary {{ background:#ffffff; color:#111827; border:1px solid #e5e7eb; }}
    .btn:disabled {{ opacity:.6; cursor:not-allowed; }}
  </style>
  <meta name="robots" content="noindex" />
  <meta name="color-scheme" content="light dark" />
  <style>
    @media (prefers-color-scheme: dark) {{
      body {{ color: #e5e7eb; background:#0b0f19; }}
      .meta {{ color: #9ca3af; }}
      table {{ color: #e5e7eb; }}
      .btn.secondary {{ background:#0b0f19; color:#e5e7eb; border-color:#1f2a44; }}
      .cell-path {{ color: #9ca3af !important; }}
      td[style*="color:#374151"] {{ color: #9ca3af !important; }}
      td[style*="color:#6b7280"] {{ color: #9ca3af !important; }}
    }}
    @media (max-width: 900px) {{
      table {{ table-layout: auto; }}
      col {{ width: auto !important; }}
    }}
    /* lightbox */
    #lightbox {{
      display:none;
      position:fixed;
      inset:0;
      background:rgba(0,0,0,.8);
      z-index:9999;
      align-items:center;
      justify-content:center;
    }}
    #lightbox img {{
      max-width:90vw;
      max-height:90vh;
      border-radius:8px;
      box-shadow:0 10px 30px rgba(0,0,0,.5);
    }}
  </style>
</head>
<body>
  <h1>{esc(title)}</h1>
  <div class="meta">生成于 {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} · 记录数：{len(df)}</div>
  {toolbar_html}
  <table>
    <colgroup>
      {"".join(colgroup_parts)}
    </colgroup>
    <thead>
      <tr>
        {"".join(header_cells)}
      </tr>
    </thead>
    <tbody>
      {"".join(rows_html)}
    </tbody>
  </table>
  <div id="lightbox" onclick="closeLightbox()">
    <img id="lightbox-img" src="" alt="preview" />
  </div>
  {checkbox_script}
  {lightbox_script}
</body>
</html>
"""


if __name__ == "__main__":
    input_path = "/data/data_processor/vlm/vqa/dpo_v2/output/King-ADV-002_sample_nomal_clean_rewrite_clean.xlsx"

    input_path = Path(input_path)
    OUT_DIR = Path(__file__).parent / "output"

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_excel(input_path)

    title = f"{input_path.stem}"
    html_text = df_to_html(df, title, with_checkbox=False)

    save_dir = Path(__file__).parent / "output"
    save_dir.mkdir(parents=True, exist_ok=True)
    save_path = save_dir / f"{input_path.stem}.html"

    save_path.write_text(html_text, encoding="utf-8")
    print(f"[完成] 生成单页表格: {save_path}")
