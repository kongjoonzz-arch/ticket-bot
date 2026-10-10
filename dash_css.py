CSS = """<style>
:root{--bg:#0f172a;--card:#1e293b;--line:#334155;--txt:#e2e8f0;--acc:#5865F2}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--txt);font-family:system-ui,sans-serif}
.wrap{max-width:1080px;margin:0 auto;padding:24px}
h1{font-size:22px}h2{font-size:16px;margin:28px 0 10px}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px;margin-bottom:14px}
.row{display:flex;gap:8px;flex-wrap:wrap;align-items:center}
input,textarea{background:#0b1220;border:1px solid var(--line);color:var(--txt);border-radius:8px;padding:8px 10px;font-size:14px}
input{min-width:120px}textarea{width:100%;min-height:64px}
button{background:var(--acc);border:0;color:#fff;border-radius:8px;padding:9px 14px;font-size:14px;cursor:pointer}
button.ghost{background:#334155}button.danger{background:#ed4245}
table{width:100%;border-collapse:collapse;font-size:13px}th,td{border-bottom:1px solid var(--line);padding:8px;text-align:left}
.badge{display:inline-block;padding:2px 8px;border-radius:99px;font-size:12px;background:#334155}
.badge.open{background:#15803d}.badge.closed{background:#64748b}
.lock{max-width:420px;margin:80px auto;text-align:center}
.hint{color:#94a3b8;font-size:13px}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:12px}
</style>"""
