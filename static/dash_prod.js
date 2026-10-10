function renderProd() {
  document.getElementById("plist").innerHTML = PRODS.map((p, i) =>
    '<div class="card"><div class="row"><input value="' + esc(p.name) + '" data-i="' + i + '" data-k="name" class="pin" style="flex:2">' +
    '<input type="number" value="' + p.price + '" data-i="' + i + '" data-k="price" class="pin" style="flex:1">' +
    '<input type="number" value="' + p.stock + '" data-i="' + i + '" data-k="stock" class="pin" style="flex:1">' +
    '<label class="hint"><input type="checkbox" ' + (p.enabled ? "checked" : "") + ' data-i="' + i + '" data-k="enabled" class="pchk"> on</label>' +
    '<button class="danger" onclick="PRODS.splice(' + i + ',1);renderProd()">del</button></div>' +
    '<textarea data-i="' + i + '" data-k="description" class="pin">' + esc(p.description || "") + '</textarea></div>'
  ).join("");
  document.querySelectorAll(".pin").forEach(el => {
    el.oninput = () => { PRODS[+el.dataset.i][el.dataset.k] = el.value; };
  });
  document.querySelectorAll(".pchk").forEach(el => {
    el.onchange = () => { PRODS[+el.dataset.i].enabled = el.checked; };
  });
}
function addProd() { PRODS.push({name: "new product", price: 10000, stock: 10, description: "", enabled: true}); renderProd(); }
function saveProd() { api("/api/products", "POST", {products: PRODS}).then(d => msg(d.ok ? "saved" : "fail")); }
let CMDS = [];
function renderCmd() {
  const el = document.getElementById("clist");
  if (!el) return;
  el.innerHTML = CMDS.map((c, i) =>
    '<div class="card"><div class="row"><input value="' + esc(c.name) + '" data-i="' + i + '" data-k="name" class="cin" placeholder="명령어 이름 (예: 계좌)" style="flex:1">' +
    '<input value="' + esc(c.description || "") + '" data-i="' + i + '" data-k="description" class="cin" placeholder="설명" style="flex:2">' +
    '<input type="number" value="' + (c.color || 0x5865F2) + '" data-i="' + i + '" data-k="color" class="cin" style="width:130px" title="색상 숫자">' +
    '<label class="hint"><input type="checkbox" ' + (c.enabled !== false ? "checked" : "") + ' data-i="' + i + '" data-k="enabled" class="cchk"> on</label>' +
    '<label class="hint"><input type="checkbox" ' + (c.ephemeral ? "checked" : "") + ' data-i="' + i + '" data-k="ephemeral" class="cchk"> 나만보기</label>' +
    '<label class="hint"><input type="checkbox" ' + (c.admin_only ? "checked" : "") + ' data-i="' + i + '" data-k="admin_only" class="cchk"> 관리자만</label>' +
    '<button class="danger" onclick="CMDS.splice(' + i + ',1);renderCmd()">del</button></div>' +
    '<input value="' + esc(c.title || "") + '" data-i="' + i + '" data-k="title" class="cin" placeholder="임베드 제목" style="width:100%;margin-bottom:6px">' +
    '<textarea data-i="' + i + '" data-k="message" class="cin" placeholder="임베드 내용 (여기에 계좌번호/설명 입력)">' + esc(c.message || "") + '</textarea>' +
    '<div class="row"><input value="' + esc(c.image_url || "") + '" data-i="' + i + '" data-k="image_url" class="cin" placeholder="이미지 URL (선택)" style="flex:2">' +
    '<input value="' + esc(c.footer || "") + '" data-i="' + i + '" data-k="footer" class="cin" placeholder="하단 문구" style="flex:1"></div>' +
    '<div class="hint">사용: /' + esc(c.name || "?") + '</div></div>'
  ).join("") || "<p class='hint'>명령어 없음</p>";
  document.querySelectorAll(".cin").forEach(x => { x.oninput = () => { CMDS[+x.dataset.i][x.dataset.k] = x.value; }; });
  document.querySelectorAll(".cchk").forEach(x => { x.onchange = () => { CMDS[+x.dataset.i][x.dataset.k] = x.checked; }; });
}
function addCmd() { if (CMDS.length >= 25) return alert("max 25"); CMDS.push({name: "새명령어", description: "", title: "", message: "", color: 0x5865F2, image_url: "", footer: "Apex Bot", ephemeral: false, admin_only: false, enabled: true}); renderCmd(); }
function saveCmd() { api("/api/commands", "POST", {commands: CMDS}).then(d => { if (d.ok) CMDS = d.commands; renderCmd(); msg(d.ok ? "saved + /cmd-reload 실행" : "fail"); }); }
