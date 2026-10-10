import os
BASE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(BASE, "static", "dash_core.js"), encoding="utf-8") as f:
    a = f.read()
with open(os.path.join(BASE, "static", "dash_prod.js"), encoding="utf-8") as f:
    b = f.read()
with open(os.path.join(BASE, "static", "dash_q.js"), encoding="utf-8") as f:
    c = f.read()
with open(os.path.join(BASE, "static", "dash.js"), "w", encoding="utf-8") as f:
    f.write(a + "\n" + b + "\n" + c + "\n")
print("ok")
