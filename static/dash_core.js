let PW = "";
function api(p, m, b) {
  return fetch(p, {method: m || "GET", headers: {"Content-Type": "application/json", "X-Admin-PW": PW}, body: b ? JSON.stringify(b) : undefined}).then(r => r.json());
}
function msg(t) { document.getElementById("msg").textContent = t; }
function esc(s) { return String(s == null ? "" : s).replace(/&/g, "&amp;").replace(/</g, "&lt;"); }
function tab(k, el) {
  document.querySelectorAll(".tab").forEach(t => t.classList.remove("on"));
  if (el) el.classList.add("on");
  document.querySelectorAll(".sec").forEach(s => s.classList.remove("on"));
  document.getElementById("s-" + k).classList.add("on");
}
function login() {
  PW = document.getElementById("pw").value;
  api("/api/auth", "POST", {pw: PW}).then(d => {
    if (d.ok) { document.getElementById("lock").style.display = "none"; document.getElementById("app").style.display = "block"; loadAll(); }
    else alert("wrong password");
  });
}
let PRODS = [], QB = [], QE = [], SET = {};
function loadAll() {
  api("/api/products").then(d => { PRODS = d.products || []; renderProd(); stat(); });
  api("/api/questions").then(d => { QB = d.questions.buy || []; QE = d.questions.error || []; renderQ(); });
  api("/api/settings").then(d => { SET = d.settings || {}; renderSet(); renderMsg(); renderDM(); renderNotice(); });
  api("/api/tickets").then(d => {
    const rows = d.tickets || [];
    const tb = document.getElementById("tbody");
    tb.innerHTML = rows.slice().reverse().map(t => "<tr><td>#" + t.no + "</td><td>" + t.kind + "</td><td>" + esc(t.user_name) + "<br><span class='hint'>" + t.user_id + "</span></td><td>" + esc(t.product ? t.product.name : "-") + "</td><td><span class='badge " + t.status + "'>" + t.status + "</span></td><td>" + esc(t.close_reason || "-") + "</td><td>" + esc(t.created_at || "") + "</td></tr>").join("") || "<tr><td colspan=7>none</td></tr>";
    const open = rows.filter(t => t.status !== "closed").length;
    document.getElementById("stOpen").textContent = open;
    document.getElementById("stClosed").textContent = rows.length - open;
    stat();
  });
  api("/api/notices").then(d => {
    const rows = d.notices || [];
    document.getElementById("nbody").innerHTML = rows.slice().reverse().map(n => "<tr><td>" + esc(n.title) + "</td><td>" + n.channel_id + "</td><td>" + esc(n.by) + "</td><td>" + esc(n.at) + "</td></tr>").join("") || "<tr><td colspan=4>none</td></tr>";
    document.getElementById("stNotice").textContent = rows.length;
  });
}
function stat() {
  document.getElementById("stProd").textContent = PRODS.filter(p => p.enabled).length + "/" + PRODS.length;
}

