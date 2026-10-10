JS1 = """<script>
let PW="";
function api(p,m,b){return fetch(p,{method:m||"GET",headers:{"Content-Type":"application/json","X-Admin-PW":PW},body:b?JSON.stringify(b):undefined}).then(r=>r.json())}
function login(){PW=document.getElementById("pw").value;api("/api/settings").then(d=>{if(d.ok){document.getElementById("lock").style.display="none";document.getElementById("app").style.display="block";loadAll()}else{alert("wrong password")}})}
let PRODS=[],QB=[],QE=[],SET={};
function esc(s){return String(s??"").replace(/&/g,"&amp;").replace(/</g,"&lt;")}
function loadAll(){api("/api/products").then(d=>{PRODS=d.products||[];renderProd()});api("/api/questions").then(d=>{QB=d.questions.buy||[];QE=d.questions.error||[];renderQ()});api("/api/settings").then(d=>{SET=d.settings||{};renderSet()});api("/api/tickets").then(d=>{const tb=document.getElementById("tbody");tb.innerHTML=(d.tickets||[]).slice().reverse().map(t=>"<tr><td>#"+t.no+"</td><td>"+t.kind+"</td><td>"+esc(t.user_name)+"</td><td>"+esc(t.product?t.product.name:"-")+"</td><td>"+t.status+"</td><td>"+esc(t.created_at||"")+"</td></tr>").join("")||"<tr><td colspan=6>none</td></tr>"})}
function renderProd(){document.getElementById("plist").innerHTML=PRODS.map((p,i)=>'<div class="card"><div class="row"><input value="'+esc(p.name)+'" oninput="PRODS['+i+'].name=this.value" style="flex:2"><input type="number" value="'+p.price+'" oninput="PRODS['+i+'].price=this.value" style="flex:1"><input type="number" value="'+p.stock+'" oninput="PRODS['+i+'].stock=this.value" style="flex:1"><label class="hint"><input type="checkbox" '+(p.enabled?"checked":"")+' onchange="PRODS['+i+'].enabled=this.checked"> on</label><button class="danger" onclick="PRODS.splice('+i+',1);renderProd()">del</button></div><textarea oninput="PRODS['+i+'].description=this.value">'+esc(p.description||"")+'</textarea></div>').join("")}
function addProd(){PRODS.push({name:"new product",price:10000,stock:10,description:"",enabled:true});renderProd()}
function saveProd(){api("/api/products","POST",{products:PRODS}).then(d=>{msg(d.ok?"saved":"fail")})}
function msg(t){document.getElementById("msg").textContent=t}
</script>"""
