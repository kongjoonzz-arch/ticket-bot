function renderQ() {
  const box = (arr, K) => arr.map((q, i) =>
    '<div class="card"><div class="row"><input value="' + esc(q.label) + '" data-a="' + K + '" data-i="' + i + '" data-k="label" class="qin" style="flex:2">' +
    '<input value="' + esc(q.placeholder || "") + '" data-a="' + K + '" data-i="' + i + '" data-k="placeholder" class="qin" style="flex:2">' +
    '<input type="number" value="' + (q.max_length || 200) + '" data-a="' + K + '" data-i="' + i + '" data-k="max_length" class="qin" style="width:80px">' +
    '<label class="hint"><input type="checkbox" ' + (q.required ? "checked" : "") + ' data-a="' + K + '" data-i="' + i + '" data-k="required" class="qchk"> req</label>' +
    '<label class="hint"><input type="checkbox" ' + ((q.enabled !== false) ? "checked" : "") + ' data-a="' + K + '" data-i="' + i + '" data-k="enabled" class="qchk"> on</label>' +
    '<button class="danger" onclick="' + K + '.splice(' + i + ',1);renderQ()">del</button></div></div>'
  ).join("");
  document.getElementById("qbuy").innerHTML = box(QB, "QB");
  document.getElementById("qerr").innerHTML = box(QE, "QE");
  const getArr = a => a === "QB" ? QB : QE;
  document.querySelectorAll(".qin").forEach(el => { el.oninput = () => { getArr(el.dataset.a)[+el.dataset.i][el.dataset.k] = el.value; }; });
  document.querySelectorAll(".qchk").forEach(el => { el.onchange = () => { getArr(el.dataset.a)[+el.dataset.i][el.dataset.k] = el.checked; }; });
}
function addQ(k) {
  if (k === "buy") { if (QB.length >= 5) return alert("max 5"); QB.push({label: "new Q", placeholder: "", required: true, max_length: 200, enabled: true}); }
  else { if (QE.length >= 5) return alert("max 5"); QE.push({label: "new Q", placeholder: "", required: true, max_length: 200, enabled: true}); }
  renderQ();
}
function saveQ() { api("/api/questions", "POST", {buy: QB, error: QE}).then(d => msg(d.ok ? "saved" : "fail")); }
const MSG_FIELDS = [
  ["panel_title", "패널 제목", 0],
  ["panel_description", "패널 설명", 1],
  ["panel_button_buy", "구매버튼 문구", 0],
  ["panel_button_buy_emoji", "구매버튼 이모지 (서버이모지 <:이름:ID> 또는 이모티콘)", 0],
  ["panel_button_error", "오류버튼 문구", 0],
  ["panel_button_error_emoji", "오류버튼 이모지 (<:이름:ID> 또는 이모티콘)", 0],
  ["panel_footer", "패널 하단", 0],
  ["panel_image_url", "패널 이미지 URL (하단 큰 이미지)", 0],
  ["panel_thumbnail_url", "패널 썸네일 URL (우측 작은 이미지)", 0],
  ["panel_color", "패널 색상(숫자)", 0],
  ["ticket_category_id", "티켓 공통 카테고리 ID (개별 미설정시)", 0],
  ["buy_category_id", "구매문의 카테고리 ID", 0],
  ["error_category_id", "오류문의 카테고리 ID", 0],
  ["ticket_log_channel_id", "로그 채널 ID", 0],
  ["purchase_log_channel_id", "구매로그 채널 ID (구매완료 기록)", 0],
  ["review_channel_id", "후기 채널 ID", 0],
  ["buyer_role_id", "구매자 역할 ID (구매완료시 지급)", 0],
  ["one_ticket_per_user", "1인 1티켓 true/false", 0],
  ["complete_button_label", "구매완료 버튼 문구", 0],
  ["complete_title", "구매완료 채널 제목", 0],
  ["complete_message", "구매완료 채널 내용", 1],
  ["complete_log_title", "구매로그 제목", 0],
  ["review_dm_title", "후기 DM 제목", 0],
  ["review_dm_message", "후기 DM 내용", 1],
  ["review_title_format", "후기 제목 형식 ({stars} {user} {no})", 0],
  ["review_min_length", "후기 최소 글자수", 0],
  ["admin_role_id", "관리자 역할 ID", 0],
  ["mention_admin_on_create", "생성시 관리자멘션 true/false", 0],
  ["mention_text", "관리자멘션 문구 ({admin_mention})", 1],
  ["welcome_message", "티켓 환영문구 ({user_mention})", 1],
  ["close_message", "닫기 채널문구", 1],
  ["close_reason_required", "닫기사유 필수 true/false", 0],
  ["close_reason_placeholder", "닫기사유 예시문구", 0],
  ["ticket_button_label", "티켓 닫기 버튼 문구", 0],
  ["delete_on_close", "닫으면 채널삭제 true/false", 0],
  ["delete_delay_sec", "삭제 대기 초 (1~30)", 0]
];
const DM_FIELDS = [
  ["dm_on_open", "열림 DM ON true/false", 0],
  ["dm_open_title", "열림 DM 제목 (#{no} 가능)", 0],
  ["dm_open_message", "열림 DM 내용", 1],
  ["dm_on_close", "닫힘 DM ON true/false", 0],
  ["dm_close_title", "닫힘 DM 제목 (#{no} 가능)", 0],
  ["dm_close_message", "닫힘 DM 내용", 1]
];
const NOTICE_FIELDS = [
  ["announce_channel_id", "공지 기본 채널 ID", 0],
  ["announce_title", "공지 제목", 0],
  ["announce_message", "공지 내용", 1],
  ["announce_color", "공지 색상(숫자)", 0],
  ["announce_image_url", "공지 이미지 URL", 0],
  ["announce_footer", "공지 하단", 0],
  ["announce_mention", "멘션 (none/here/everyone/role)", 0],
  ["announce_mention_role_id", "멘션 역할 ID (role일 때)", 0]
];
function fieldRow(k, label, area, cls) {
  const v = SET[k] == null ? "" : SET[k];
  if (area) return '<div style="margin-bottom:8px"><div class="hint">' + label + '<br>' + k + '</div><textarea data-k="' + k + '" class="' + cls + '">' + esc(v) + '</textarea></div>';
  return '<div style="margin-bottom:8px"><div class="hint">' + label + '<br>' + k + '</div><input value="' + esc(v) + '" data-k="' + k + '" class="' + cls + '" style="width:100%"></div>';
}
function bindCls(cls) {
  document.querySelectorAll("." + cls).forEach(el => { el.oninput = () => { SET[el.dataset.k] = el.value; }; });
}
function renderMsg() {
  const el = document.getElementById("mset");
  if (!el) return;
  el.innerHTML = MSG_FIELDS.map(f => fieldRow(f[0], f[1], f[2], "sin")).join("");
  bindCls("sin");
}
function renderDM() {
  const el = document.getElementById("dset");
  if (!el) return;
  el.innerHTML = DM_FIELDS.map(f => fieldRow(f[0], f[1], f[2], "sdm")).join("");
  bindCls("sdm");
}
function renderNotice() {
  const el = document.getElementById("nset");
  if (!el) return;
  el.innerHTML = NOTICE_FIELDS.map(f => fieldRow(f[0], f[1], f[2], "snc")).join("") +
    '<div class="hint">멘션 선택: <select data-k="announce_mention" class="snc">' +
    ["none", "here", "everyone", "role"].map(m => '<option value="' + m + '"' + (SET.announce_mention === m ? " selected" : "") + '>' + m + '</option>').join("") +
    '</select></div>';
  bindCls("snc");
  document.querySelectorAll("select.snc").forEach(el => { el.onchange = () => { SET[el.dataset.k] = el.value; }; });
  previewNotice();
}
function previewNotice() {
  const el = document.getElementById("nprev");
  if (!el) return;
  let c = parseInt(SET.announce_color) || 0x5865F2;
  el.innerHTML = '<div style="border-left:4px solid #' + c.toString(16).padStart(6, "0") + ';padding-left:10px">' +
    '<div style="font-weight:800">' + esc(SET.announce_title || "") + '</div>' +
    '<div style="white-space:pre-wrap;margin-top:6px">' + esc(SET.announce_message || "") + '</div>' +
    (SET.announce_image_url ? '<div class="hint">이미지: ' + esc(SET.announce_image_url) + '</div>' : "") +
    (SET.announce_footer ? '<div class="hint">' + esc(SET.announce_footer) + '</div>' : "") +
    '<div class="hint">멘션: ' + esc(SET.announce_mention || "none") + '</div></div>';
}
function renderSet() { renderMsg(); }
function saveSet() {
  const c = Object.assign({}, SET);
  c.panel_color = parseInt(c.panel_color) || 0x5865F2;
  c.announce_color = parseInt(c.announce_color) || 0x5865F2;
  c.review_min_length = parseInt(c.review_min_length) || 5;
  c.delete_delay_sec = Math.max(1, Math.min(30, parseInt(c.delete_delay_sec) || 5));
  ["mention_admin_on_create", "dm_on_open", "dm_on_close", "close_reason_required", "delete_on_close", "one_ticket_per_user"].forEach(k => {
    if (typeof c[k] === "string") c[k] = (c[k] === "true");
  });
  api("/api/settings", "POST", c).then(d => { if (d.ok) { SET = d.settings; renderMsg(); renderDM(); renderNotice(); } msg(d.ok ? "saved" : "fail"); });
}
function saveNotice() {
  const c = Object.assign({}, SET);
  c.announce_color = parseInt(c.announce_color) || 0x5865F2;
  api("/api/announce", "POST", Object.assign({save: true}, c)).then(d => { if (d.ok) { SET = d.settings; renderNotice(); } msg(d.ok ? "saved" : "fail"); });
}
