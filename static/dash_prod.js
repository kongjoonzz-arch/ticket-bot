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
