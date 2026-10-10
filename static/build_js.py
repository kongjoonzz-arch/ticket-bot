import os
BASE = os.path.dirname(os.path.abspath(__file__))
FRAGS = ["dash_core.js", "dash_prod.js", "dash_q.js"]
buf = []
for name in FRAGS:
    p = os.path.join(BASE, name)
    if os.path.exists(p):
        with open(p, "r", encoding="utf-8") as f:
            buf.append(f.read())
with open(os.path.join(BASE, "dash.js"), "w", encoding="utf-8") as f:
    f.write("\n".join(buf))
print("dash.js rebuilt from fragments")

