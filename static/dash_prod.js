let CATS = [];

function ensureCatBox() {
  let box = document.getElementById("catbox");
  if (box) return box;
  const plist = document.getElementById("plist");
  if (!plist || !plist.parentNode) return null;
  box = document.createElement("div");
  box.id = "catbox";
  const prev = plist.previousElementSibling;
  const anchor = (prev && prev.tagName === "H2") ? prev : plist;
  anchor.parentNode.insertBefore(box, anchor);
  return box;
}

function renderCats() {
  const box = ensureCatBox();
  if (!box) return;
  const rows = CATS.map((c, i) =>
    '<div class="row" style="margin-bottom:6px">' +
    '<span class="hint" style="min-width:26px">' + (i + 1) + '</span>' +
    '<input value="' + esc(c) + '" data-ci="' + i + '" class="catn" style="flex:2">' +
    '<button class="ghost" onclick="moveCat(' + i + ',-1)">&#9650;</button>' +
    '<button class="ghost" onclick="moveCat(' + i + ',1)">&#9660;</button>' +
    '<button class="danger" onclick="delCat(' + i + ')">del</button>' +
    '</div>'
  ).join("") || "<p class='hint'>카테고리 없음</p>";
  box.innerHTML =
    '<h2>카테고리 순서 (&#9650;&#9660; 로 변경 · 봇 구매창에 이 순서로 표시)</h2>' +
    '<div class="card">' + rows +
    '<div class="row" style="margin-top:8px">' +
    '<input id="newcat" placeholder="새 카테고리 이름" style="flex:2">' +
    '<button class="ghost" onclick="addCat()">+ 카테고리 추가</button>' +
    '</div>' +
    '<div class="row" style="margin-top:8px"><button onclick="saveCats()">카테고리 순서 저장</button></div>' +
    '</div>';
  document.querySelectorAll(".catn").forEach(el => {
    el.oninput = () => { CATS[+el.dataset.ci] = el.value; };
  });
}

function moveCat(i, d) {
  const j = i + d;
  if (j < 0 || j >= CATS.length) return;
  const t = CATS[i]; CATS[i] = CATS[j]; CATS[j] = t;
  renderCats();
}

function delCat(i) {
  const name = CATS[i];
  if (!confirm("카테고리 '" + name + "' 를 목록에서 제거할까요?\n(상품은 그대로 남습니다)")) return;
  CATS.splice(i, 1);
  renderCats();
}

function addCat() {
  const el = document.getElementById("newcat");
  const v = ((el && el.value) || "").trim();
  if (!v) return;
  if (CATS.indexOf(v) >= 0) return alert("이미 있는 카테고리입니다");
  CATS.push(v);
  if (el) el.value = "";
  renderCats();
  renderProd();
}

function saveCats() {
  api("/api/categories", "POST", {categories: CATS}).then(d => {
    if (d.ok) CATS = d.categories || CATS;
    renderCats();
    renderProd();
    msg(d.ok ? "카테고리 순서 저장됨" : "fail");
  });
}

function allCats() {
  const out = CATS.slice();
  PRODS.forEach(p => {
    const c = String(p.category || "").trim();
    if (c && out.indexOf(c) < 0) out.push(c);
  });
  return out;
}

function renderProd() {
  const cats = allCats();
  document.getElementById("plist").innerHTML = PRODS.map((p, i) =>
    '<div class="card"><div class="row">' +
    '<input type="number" value="' + (p.order || (i + 1)) + '" data-i="' + i + '" data-k="order" class="pin" style="width:66px" title="순서 (낮을수록 먼저)">' +
    '<input value="' + esc(p.name) + '" data-i="' + i + '" data-k="name" class="pin" style="flex:2" placeholder="상품명">' +
    '<input value="' + esc(p.category || "") + '" data-i="' + i + '" data-k="category" class="pin" style="flex:1" placeholder="카테고리" list="catlist">' +
    '<input type="number" value="' + p.price + '" data-i="' + i + '" data-k="price" class="pin" style="flex:1" title="가격">' +
    '<input type="number" value="' + (p.quantity || 1) + '" data-i="' + i + '" data-k="quantity" class="pin" style="width:72px" title="갯수">' +
    '<input type="number" value="' + (p.discount || 0) + '" data-i="' + i + '" data-k="discount" class="pin" style="width:86px" title="할인 금액">' +
    '<input type="number" value="' + p.stock + '" data-i="' + i + '" data-k="stock" class="pin" style="width:80px" title="재고">' +
    '<label class="hint"><input type="checkbox" ' + (p.enabled ? "checked" : "") + ' data-i="' + i + '" data-k="enabled" class="pchk"> on</label>' +
    '<button class="danger" onclick="PRODS.splice(' + i + ',1);renderProd()">del</button></div>' +
    '<div class="hint" style="margin:4px 0">순서 / 상품명 / 카테고리 / 가격 / 갯수 / 할인 / 재고</div>' +
    '<textarea data-i="' + i + '" data-k="description" class="pin">' + esc(p.description || "") + '</textarea></div>'
  ).join("") + '<datalist id="catlist">' + cats.map(c => '<option value="' + esc(c) + '"></option>').join("") + '</datalist>';
  document.querySelectorAll(".pin").forEach(el => {
    el.oninput = () => { PRODS[+el.dataset.i][el.dataset.k] = el.value; };
  });
  document.querySelectorAll(".pchk").forEach(el => {
    el.onchange = () => { PRODS[+el.dataset.i].enabled = el.checked; };
  });
  ensureProdButtons();
}

function addProd() {
  let max = 0;
  PRODS.forEach(p => { const o = parseInt(p.order) || 0; if (o > max) max = o; });
  PRODS.push({name: "새 상품", category: CATS[0] || "기타", price: 1000, quantity: 1,
              discount: 0, stock: 100, order: max + 1, description: "", enabled: true});
  renderProd();
}

function saveProd() {
  api("/api/products", "POST", {products: PRODS, categories: CATS}).then(d => {
    if (d.ok) {
      PRODS = d.products || PRODS;
      CATS = d.categories || CATS;
      renderCats();
      renderProd();
      stat();
    }
    msg(d.ok ? "상품 + 카테고리 저장됨" : "fail");
  });
}

function ensureProdButtons() {
  const plist = document.getElementById("plist");
  if (!plist) return;
  const row = plist.nextElementSibling;
  if (!row || row.tagName !== "DIV") return;
  if (document.getElementById("btnDefaults")) return;
  const b = document.createElement("button");
  b.id = "btnDefaults";
  b.className = "ghost";
  b.textContent = "기본 쿠키 18종 불러오기";
  b.onclick = loadDefaults;
  row.appendChild(b);
}

function loadDefaults() {
  if (!confirm("기본 쿠키 상품 18종을 추가할까요?\n(이미 있는 기본 상품은 건너뜁니다)")) return;
  api("/api/products/defaults", "POST", {mode: "merge"}).then(d => {
    if (d.ok) {
      PRODS = d.products || PRODS;
      CATS = d.categories || CATS;
      renderCats();
      renderProd();
      stat();
    }
    msg(d.ok ? "기본 쿠키 상품을 불러왔습니다" : "fail");
  });
}

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
