/*
 * ═══════════════════════════════════════════════════════════
 *  SMARTCARD — MODULE LISTE
 *  Extrait de index.html pour modularisation
 *  Contient : CSS Liste, HTML view #vListe, JS Liste/Chariot/Historique/Autocomplete/Swipe/Edit
 * ═══════════════════════════════════════════════════════════
 */

/* ── Injection du HTML de la vue Liste dans #vwrap ── */
(function injectListeView() {
  const vwrap = document.querySelector('.vwrap');
  if (!vwrap) return console.warn('[Liste] .vwrap introuvable');

  const html = `<!-- VIEW: LISTE -->
    <div class="view on" id="vListe">
      <div class="vb">
        <div class="lg-hello" id="lgHello">Bonjour 👋</div>
        <div class="lg-title">Ma Liste 🛒</div>
        <div class="lg-sub" id="lgSub">0 article à acheter</div>

        <div class="list-stats">
          <div class="ls-p"><div class="ls-v" id="statTotal">0</div><div class="ls-l">articles</div></div>
          <div class="ls-p"><div class="ls-v" id="statCoche">0</div><div class="ls-l">cochés</div></div>
          <div class="ls-p"><div class="ls-v" id="statBudget">0€</div><div class="ls-l">budget est.</div></div>
        </div>
        <div class="budget-bar-wrap">
          <div class="bb-track"><div class="bb-fill" id="bbFill" style="width:0%"></div></div>
          <div class="bb-lbl" id="bbLbl">0€ / 80€ semaine</div>
        </div>

        <div class="add-row">
          <div class="ac-wrap">
            <input class="inp" id="addInput" placeholder="Ajouter un article..." autocomplete="off"
              oninput="onSearchInput(this.value)" onkeydown="if(event.key==='Enter')addItemFromInput()">
            <div class="ac-list" id="acList" style="display:none;"></div>
          </div>
          <button class="btn acc" onclick="addItemFromInput()">+</button>        </div>

        <div class="cats" id="catChips">
          <div class="chip on" data-cat="all" onclick="filterCat(this)">Tout</div>
          <div class="chip" data-cat="🥛 Laitage" onclick="filterCat(this)">🥛 Laitage</div>
          <div class="chip" data-cat="🥩 Viande" onclick="filterCat(this)">🥩 Viande</div>
          <div class="chip" data-cat="🥦 Légumes" onclick="filterCat(this)">🥦 Légumes</div>
          <div class="chip" data-cat="🍎 Fruits" onclick="filterCat(this)">🍎 Fruits</div>
          <div class="chip" data-cat="🥖 Boulangerie" onclick="filterCat(this)">🥖 Boulangerie</div>
          <div class="chip" data-cat="🐟 Poisson" onclick="filterCat(this)">🐟 Poisson</div>
          <div class="chip" data-cat="🧴 Hygiène" onclick="filterCat(this)">🧴 Hygiène</div>
          <div class="chip" data-cat="🧹 Ménager" onclick="filterCat(this)">🧹 Ménager</div>
          <div class="chip" data-cat="🍝 Épicerie" onclick="filterCat(this)">🍝 Épicerie</div>
          <div class="chip" data-cat="🥤 Boissons" onclick="filterCat(this)">🥤 Boissons</div>
          <div class="chip" data-cat="🐾 Animaux" onclick="filterCat(this)">🐾 Animaux</div>
        </div>

        <div class="list-subtabs">
          <div class="list-subtab on" id="stab-tobuy" onclick="switchSubtab('tobuy')">🛒 À acheter</div>
          <div class="list-subtab" id="stab-cart" onclick="switchSubtab('cart')">🧺 Chariot</div>
          <div class="list-subtab" id="stab-done" onclick="switchSubtab('done')">✅ Historique</div>
        </div>

        <div id="subtab-tobuy">
          <div class="sec-row">
            <span class="sec-lbl" id="toBuyLabel">À acheter</span>
            <div style="display:flex;gap:6px;">
              <button class="btn sm" onclick="shareShoppingList()" title="Partager" style="padding:7px 10px;">📤</button>
              <button class="btn sm" onclick="sortItems()">A→Z</button>
              <button class="btn sm" style="color:var(--rd);" onclick="clearChecked()">Suppr. cochés</button>
            </div>
          </div>
          <div class="items" id="itemsWrap"></div>
          <div class="empty" id="emptyState" style="display:none;">
            <div class="empty-ic">🛒</div>
            <div class="empty-ti">Liste vide</div>
            <div class="empty-su">Ajoutez des articles via la barre de recherche ou les raccourcis.</div>
          </div>
        </div>

        <div id="subtab-cart" style="display:none;">
          <div id="cartBannerWrap"></div>
          <div class="items" id="cartItemsWrap"></div>
          <div class="empty" id="emptyCart" style="display:none;">
            <div class="empty-ic">🧺</div>
            <div class="empty-ti">Chariot vide</div>
            <div class="empty-su">Cochez des articles pour les voir ici.</div>
          </div>
        </div>

        <div id="subtab-done" style="display:none;">
          <div class="sechd" style="margin-bottom:14px;">
            <span class="sec-ti">Historique des courses</span>
            <span class="sec-cnt" id="histCount">0 session(s)</span>
          </div>
          <div id="historyWrap"></div>
          <div class="empty" id="emptyHistory" style="display:none;">
            <div class="empty-ic">📋</div>
            <div class="empty-ti">Aucun historique</div>
            <div class="empty-su">Terminez une course pour créer votre premier historique.</div>
          </div>
        </div>
      </div>
    </div>`;
  // Insérer en premier enfant du vwrap
  vwrap.insertAdjacentHTML('afterbegin', html);
})();

/* ═══════════════════════════════
   CSS — LISTE
═══════════════════════════════ */
(function injectListeCSS() {
  const style = document.createElement('style');
  style.id = 'sc-liste-styles';
  style.textContent = `
/* ══ STATS CARDS ══ */
.list-stats{display:flex;gap:10px;margin:16px 0;}
.ls-p{flex:1;background:var(--bg);border-radius:var(--rs);box-shadow:var(--so);padding:12px 8px;text-align:center;position:relative;overflow:hidden;}
.ls-p::after{content:'';position:absolute;top:-10px;right:-10px;width:40px;height:40px;border-radius:50%;opacity:.15;}
.ls-p:nth-child(1)::after{background:var(--ac);}
.ls-p:nth-child(2)::after{background:var(--gn);}
.ls-p:nth-child(3)::after{background:var(--or);}
.ls-v{font-size:1.35rem;font-weight:900;color:var(--tx);}
.ls-l{font-size:.56rem;font-weight:700;text-transform:uppercase;letter-spacing:.5px;color:var(--tx3);margin-top:2px;}

/* ══ BUDGET BAR ══ */
.budget-bar-wrap{margin-bottom:16px;}
.bb-track{height:8px;border-radius:99px;background:var(--bg);box-shadow:var(--si);overflow:hidden;}
.bb-fill{height:100%;border-radius:99px;background:var(--grad);transition:width .5s,background .3s;}
.bb-lbl{font-size:.68rem;color:var(--tx2);font-weight:600;margin-top:5px;}

/* ══ ADD ROW ══ */
.add-row{display:flex;gap:9px;margin-bottom:16px;}
.add-row .inp{flex:1;}
.cats{display:flex;gap:7px;overflow-x:auto;padding-bottom:3px;margin-bottom:16px;scrollbar-width:none;}
.cats::-webkit-scrollbar{display:none;}

/* ══ LIST SUBTABS ══ */
.list-subtabs{display:flex;gap:6px;margin-bottom:14px;background:var(--bg);border-radius:var(--rs);box-shadow:var(--si);padding:4px;}
.list-subtab{flex:1;text-align:center;padding:9px 4px;border-radius:11px;font-size:.72rem;font-weight:800;color:var(--tx2);cursor:pointer;transition:all .2s;white-space:nowrap;}
.list-subtab.on{background:var(--grad);color:#fff;box-shadow:3px 3px 8px rgba(255,107,107,.25);}

/* ══ ITEMS ══ */
.items{display:flex;flex-direction:column;gap:7px;}
.item-wrap{position:relative;border-radius:var(--rs);overflow:hidden;}
.item-delete-bg{position:absolute;right:0;top:0;bottom:0;width:80px;background:linear-gradient(90deg,transparent,rgba(231,76,60,.15));display:flex;align-items:center;justify-content:flex-end;padding-right:16px;color:var(--rd);font-size:.65rem;font-weight:700;}
.delbg-icon{text-align:center;}
.item{display:flex;align-items:center;gap:11px;background:var(--bg);border-radius:var(--rs);box-shadow:var(--so);padding:12px 13px;cursor:pointer;transition:transform .2s,box-shadow .2s;position:relative;z-index:1;user-select:none;}
.item.ck{opacity:.7;}
.item.swiping{transition:none;}
.item.deleting{pointer-events:none;}
.i-em{font-size:1.3rem;flex-shrink:0;}
.i-info{flex:1;min-width:0;}
.inm{font-weight:800;font-size:.88rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.imeta{font-size:.7rem;color:var(--tx2);margin-top:2px;}
.i-r{display:flex;align-items:center;gap:4px;flex-shrink:0;}
.ipr{font-size:.75rem;font-weight:800;color:var(--tl);}
.item-shared-badge{font-size:.58rem;background:rgba(52,152,219,.15);color:var(--bl);border-radius:4px;padding:2px 5px;font-weight:700;flex-shrink:0;}

/* ══ CART BANNER ══ */
.cart-banner{background:var(--grad);border-radius:var(--rs);padding:14px 16px;margin-bottom:14px;display:flex;align-items:center;justify-content:space-between;gap:10px;}
.cart-banner-tx{font-weight:800;font-size:.9rem;color:#fff;}
.cart-banner-sub{font-size:.72rem;color:rgba(255,255,255,.85);margin-top:2px;}
.finish-btn{background:rgba(255,255,255,.25);color:#fff;border-radius:var(--rp);padding:8px 14px;font-size:.78rem;font-weight:800;cursor:pointer;white-space:nowrap;flex-shrink:0;}
.finish-btn:active{background:rgba(255,255,255,.35);}

/* ══ FOYER CARD ══ */
.foyer-card{background:var(--bg);border-radius:var(--r);box-shadow:var(--so);padding:16px;margin-bottom:14px;border-left:3px solid var(--ac);}
.foyer-code{font-size:1.4rem;font-weight:900;color:var(--ac);letter-spacing:4px;text-align:center;padding:12px;background:var(--bg3);border-radius:var(--rx);margin:8px 0;}
.foyer-members{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px;}
.foyer-member{display:flex;align-items:center;gap:6px;padding:6px 12px;background:var(--bg);border-radius:var(--rp);box-shadow:var(--so);font-size:.75rem;font-weight:700;}
.foyer-member-av{width:22px;height:22px;border-radius:50%;background:var(--grad);display:flex;align-items:center;justify-content:center;font-size:.65rem;font-weight:800;color:#fff;flex-shrink:0;}

/* ══ HISTORY ══ */
.hist-session{background:var(--bg);border-radius:var(--rs);box-shadow:var(--so);margin-bottom:10px;overflow:hidden;}
.hist-session-hd{display:flex;align-items:center;justify-content:space-between;padding:13px 15px;cursor:pointer;}
.hist-session-date{font-weight:800;font-size:.87rem;}
.hist-session-meta{font-size:.7rem;color:var(--tx2);margin-top:2px;}
.hist-session-body{padding:0 15px 14px;}
.hist-item{display:flex;align-items:center;gap:8px;padding:6px 0;border-top:1px solid var(--bg2);font-size:.82rem;}
.hist-item-em{font-size:1rem;}

.ac-wrap{position:relative;flex:1;}
.ac-list{position:absolute;z-index:9999;background:var(--bg);border-radius:var(--rs);box-shadow:0 12px 40px rgba(0,0,0,.25),0 2px 8px rgba(0,0,0,.12);max-height:220px;overflow-y:auto;display:none;left:0;right:0;top:calc(100% + 4px);}
.ac-item{display:flex;align-items:center;gap:10px;padding:10px 14px;cursor:pointer;transition:background .12s;}
.ac-item:active{background:var(--bg2);}
.ac-item-em{font-size:1.2rem;flex-shrink:0;}
.ac-item-nm{font-weight:700;font-size:.85rem;flex:1;}
.ac-item-cat{font-size:.68rem;color:var(--tx2);}

/* ══ EDIT MODAL ══ */
.edit-field{margin-bottom:12px;}
.edit-label{font-size:.7rem;font-weight:800;text-transform:uppercase;letter-spacing:.8px;color:var(--tx3);display:block;margin-bottom:6px;}
.cat-selector{display:flex;flex-wrap:wrap;gap:6px;max-height:160px;overflow-y:auto;}
.cat-opt{padding:7px 13px;border-radius:var(--rp);background:var(--bg);box-shadow:var(--so);font-size:.75rem;font-weight:700;cursor:pointer;color:var(--tx2);transition:all .15s;white-space:nowrap;}
.cat-opt.on{background:var(--grad);color:#fff;}
  `;
  document.head.appendChild(style);
})();

/* ═══════════════════════════════
   JS — LISTE / CHARIOT / HISTORIQUE / AUTOCOMPLETE / SWIPE / EDIT MODAL
═══════════════════════════════ */
// LISTE
// ═══════════════════════════════════════════════
const CATEGORIES = ['🥛 Laitage','🥩 Viande','🥦 Légumes','🍎 Fruits','🥖 Boulangerie','🐟 Poisson','🧴 Hygiène','🧹 Ménager','🍝 Épicerie','🥤 Boissons','🐾 Animaux'];

function getFilteredItems() {
  let items = state.items.filter(i => !i.checked);
  if(state.filterCat !== 'all') items = items.filter(i => i.cat === state.filterCat);
  if(state.sortAZ) items = [...items].sort((a,b) => a.name.localeCompare(b.name));
  return items;
}

function renderList() {
  const items = getFilteredItems();
  const wrap = document.getElementById('itemsWrap');
  const empty = document.getElementById('emptyState');
  const showPrix = !state.profile || state.profile.showPrix !== false;
  const total = state.items.length;
  const checked = state.items.filter(i => i.checked).length;
  const budgetUsed = state.items.reduce((s,i) => s + (i.price || 0), 0);
  const weekBudget = state.budget || 80;

  document.getElementById('statTotal').textContent = total;
  document.getElementById('statCoche').textContent = checked;

  // Stat budget — masqué si prix désactivés
  const statBudgetEl = document.getElementById('statBudget');
  const statBudgetCard = statBudgetEl ? statBudgetEl.closest('.ls-p') : null;
  if(statBudgetCard) statBudgetCard.style.display = showPrix ? '' : 'none';
  if(statBudgetEl) statBudgetEl.textContent = budgetUsed.toFixed(0) + '€';

  document.getElementById('lgSub').textContent = items.length + ' article' + (items.length !== 1 ? 's' : '') + ' à acheter';
  document.getElementById('toBuyLabel').textContent = 'À acheter (' + items.length + ')';

  // Barre de budget — masquée si prix désactivés
  const budgetBarWrap = document.querySelector('.budget-bar-wrap');
  if(budgetBarWrap) budgetBarWrap.style.display = showPrix ? '' : 'none';

  if(showPrix) {
    const pct = Math.min(100, Math.round(budgetUsed / weekBudget * 100));
    const fill = document.getElementById('bbFill');
    if(fill) {
      fill.style.width = pct + '%';
      fill.style.background = pct > 90 ? 'linear-gradient(90deg,#e17055,#d63031)' : pct > 70 ? 'linear-gradient(90deg,#f0b429,#e17055)' : 'var(--grad)';
    }
    const lbl = document.getElementById('bbLbl');
    if(lbl) lbl.textContent = budgetUsed.toFixed(2).replace('.',',') + '€ / ' + weekBudget + '€ semaine';
  }

  if(!items.length) {
    if(wrap) wrap.innerHTML = '';
    if(empty) empty.style.display = 'block';
    return;
  }
  if(empty) empty.style.display = 'none';
  if(wrap) { wrap.innerHTML = items.map(item => itemHTML(item)).join(''); attachSwipe(); }
}

function getMemberBadgeColor(addedBy) {
  if(!addedBy) return '#888';
  // Use a hash of the name to assign a stable color
  let hash = 0;
  for(let i=0;i<addedBy.length;i++) hash = addedBy.charCodeAt(i)+((hash<<5)-hash);
  // Pick from palette: warm (F indicator) vs cool (H)
  const warmColors = ['#e84393','#e74c3c','#e67e22','#9b59b6','#ff6b9d'];
  const coolColors = ['#3498db','#2ecc71','#1abc9c','#27ae60','#2980b9'];
  // Try to detect gender from profile if it's the current user
  const isSelf = currentUser && (addedBy === currentUser.email || addedBy === (currentUser.displayName||''));
  let palette;
  if(isSelf && state.profile && state.profile.sex) {
    palette = state.profile.sex === 'F' ? warmColors : (state.profile.sex === 'H' ? coolColors : warmColors);
  } else {
    // default: alternate by hash
    palette = Math.abs(hash) % 2 === 0 ? warmColors : coolColors;
  }
  return palette[Math.abs(hash) % palette.length];
}

function getMemberInitial(addedBy) {
  if(!addedBy) return '?';
  return (addedBy.split('@')[0] || addedBy).charAt(0).toUpperCase();
}

function itemHTML(item) {
  const showPrice = state.profile && state.profile.showPrix !== false;
  const memberColor = item.addedBy ? getMemberBadgeColor(item.addedBy) : null;
  const memberInitial = item.addedBy ? getMemberInitial(item.addedBy) : null;
  return `<div class="item-wrap" data-id="${item.id}">
    <div class="item-delete-bg"><div class="delbg-icon">🗑️<br><span style="font-size:.6rem;font-weight:700;">Supprimer</span></div></div>
    <div class="item" data-id="${item.id}">
      <div class="chk${item.checked?' on':''}" onclick="event.stopPropagation();toggleCheck('${item.id}')">
        ${item.checked?'<svg width="14" height="14" viewBox="0 0 12 12"><path d="M2 6l3 3 5-5" stroke="#fff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></svg>':''}
      </div>
      <div class="i-em">${item.emoji||'🛒'}</div>
      <div class="i-info">
        <div class="inm">${item.name}</div>
        ${item.qty?`<div class="imeta"><span style="color:var(--tl);font-weight:700;">${item.qty}</span></div>`:''}
      </div>
      <div class="i-r">
        ${showPrice && item.price?`<span class="ipr">${item.price.toFixed(2)}€</span>`:''}
        ${state.houseId && memberColor?`<div title="Ajouté par ${item.addedBy||'?'}" style="width:22px;height:22px;border-radius:50%;background:${memberColor};display:flex;align-items:center;justify-content:center;font-size:.6rem;font-weight:800;color:#fff;flex-shrink:0;">${memberInitial}</div>`:''}
        <button class="btn ghost sm" style="padding:4px 6px;color:var(--tx3);" onclick="event.stopPropagation();openEdit('${item.id}')">✏️</button>
        <button class="btn ghost sm" style="padding:4px 6px;color:var(--rd);" onclick="event.stopPropagation();deleteItem('${item.id}')">🗑</button>
      </div>
    </div>
  </div>`;
}

function toggleCheck(id) {
  const item = state.items.find(i => i.id === id);
  if(!item) return;
  item.checked = !item.checked;
  item.checkedAt = item.checked ? Date.now() : null;
  saveItems();
  renderList();
  if(state.currentSubtab === 'cart') renderCart();
}

function addItemFromInput() {
  const inp = document.getElementById('addInput');
  const val = inp.value.trim();
  if(!val) return;
  const existing = state.items.find(i => i.name.toLowerCase() === val.toLowerCase() && !i.checked);
  if(existing) {
    const cur = existing.qty ? parseInt(existing.qty) || 1 : 1;
    confirm2('🔄', val + ' est déjà dans la liste', 'Quantité actuelle: ' + (existing.qty || '1') + '. Mettre à jour?', () => {
      existing.qty = String(cur + 1);
      saveItems(); renderList();
      showToast('🔄', val, 'Quantité mise à jour.');
    });
    inp.value = '';
    document.getElementById('acList').style.display = 'none';
    return;
  }
  const prod = PRODUCTS.find(p => p.name.toLowerCase() === val.toLowerCase());
  const item = {
    id: 'i' + Date.now() + Math.random().toString(36).slice(2,7),
    name: prod ? prod.name : val,
    emoji: prod ? prod.emoji : '🛒',
    cat: prod ? prod.cat : '🍝 Épicerie',
    price: prod ? prod.price : 0,
    qty: '', checked: false, addedAt: Date.now(),
    addedBy: currentUser ? (currentUser.displayName || currentUser.email) : 'Inconnu'
  };
  state.items.unshift(item);
  saveItems();
  inp.value = '';
  document.getElementById('acList').style.display = 'none';
  renderList();
  showToast('✅', item.name, 'Ajouté à votre liste.');
}

function addItemByName(name) {
  const prod = PRODUCTS.find(p => p.name.toLowerCase() === name.toLowerCase()) || {name, emoji:'🛒', cat:'🍝 Épicerie', price:0};
  const ex = state.items.find(i => i.name.toLowerCase() === name.toLowerCase() && !i.checked);
  if(ex) { ex.qty = String((parseInt(ex.qty)||1) + 1); saveItems(); renderList(); showToast('🔄', name, 'Quantité +1'); return; }
  state.items.unshift({id:'i'+Date.now()+Math.random().toString(36).slice(2,7),name:prod.name,emoji:prod.emoji,cat:prod.cat,price:prod.price,qty:'',checked:false,addedAt:Date.now(),addedBy:currentUser?currentUser.email:''});
  saveItems(); renderList();
  showToast('✅', prod.name, 'Ajouté à la liste.');
}

function deleteItem(id) {
  state.items = state.items.filter(i => i.id !== id);
  saveItems(); renderList();
  if(state.currentSubtab === 'cart') renderCart();
}

function clearChecked() {
  const n = state.items.filter(i => i.checked).length;
  if(!n) { showToast('ℹ️','Rien','Cochez d\'abord des articles.'); return; }
  confirm2('🗑️','Supprimer les cochés', `Supprimer ${n} article(s) coché(s) ?`, () => {
    state.items = state.items.filter(i => !i.checked);
    saveItems(); renderList();
    if(state.currentSubtab === 'cart') renderCart();
    showToast('✅', n + ' supprimé(s)', '');
  });
}

function sortItems() {
  state.sortAZ = !state.sortAZ;
  renderList();
  showToast('📋', state.sortAZ ? 'Trié A→Z' : 'Ordre original', '');
}

function filterCat(el) {
  document.querySelectorAll('#catChips .chip').forEach(c => c.classList.remove('on'));
  el.classList.add('on');
  state.filterCat = el.dataset.cat;
  renderList();
}

// ═══════════════════════════════════════════════
// CHARIOT
// ═══════════════════════════════════════════════
function renderCart() {
  const checked = state.items.filter(i => i.checked);
  const wrap = document.getElementById('cartItemsWrap');
  const empty = document.getElementById('emptyCart');
  const banner = document.getElementById('cartBannerWrap');
  if(!checked.length) {
    if(wrap) wrap.innerHTML = '';
    if(empty) empty.style.display = 'block';
    if(banner) banner.innerHTML = '';
    return;
  }
  if(empty) empty.style.display = 'none';
  const total = checked.reduce((s,i) => s+(i.price||0), 0).toFixed(2);
  if(banner) banner.innerHTML = `
    <div class="cart-banner">
      <div><div class="cart-banner-tx">${checked.length} article(s) dans le chariot</div><div class="cart-banner-sub">Total estimé : ${total}€</div></div>
      <div class="finish-btn" onclick="finishShopping()">✅ Terminer</div>
    </div>`;
  if(wrap) wrap.innerHTML = checked.map(item => `
    <div class="item-wrap" style="margin-bottom:7px;">
      <div class="item ck" data-id="${item.id}">
        <div class="chk on" onclick="toggleCheck('${item.id}');switchSubtab('cart')">
          <svg width="12" height="12" viewBox="0 0 12 12"><path d="M2 6l3 3 5-5" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
        </div>
        <div class="i-em">${item.emoji||'🛒'}</div>
        <div class="i-info"><div class="inm">${item.name}</div>${item.qty?`<div class="imeta">${item.qty}</div>`:''}</div>
        <div class="i-r">
          ${item.price?`<span class="ipr">${item.price.toFixed(2)}€</span>`:''}
          <button class="btn ghost sm" style="padding:4px 6px;color:var(--rd);" onclick="deleteItem('${item.id}');renderCart()">🗑</button>
        </div>
      </div>
    </div>`).join('');
}

function finishShopping() {
  const checked = state.items.filter(i => i.checked);
  if(!checked.length) return;
  confirm2('🎉', 'Courses terminées !', `Ajouter ${checked.length} article(s) au frigo et à l'historique ?`, () => {
    const session = {
      date: new Date().toLocaleDateString('fr-FR', {day:'2-digit',month:'2-digit',year:'2-digit'}),
      timestamp: Date.now(),
      items: checked.map(i => ({name:i.name,emoji:i.emoji,price:i.price||0})),
      total: checked.reduce((s,i) => s+(i.price||0), 0).toFixed(2)
    };
    state.history.unshift(session);
    if(state.history.length > 20) state.history.pop();
    checked.forEach(item => {
      const ex = state.fridge.find(f => f.name.toLowerCase() === item.name.toLowerCase());
      if(ex) { ex.qty = (parseInt(ex.qty)||1) + 1; }
      else { state.fridge.push({id:'f'+Date.now()+Math.random().toString(36).slice(2,5),name:item.name,emoji:item.emoji||'🛒',qty:1,cat:item.cat}); }
    });
    state.items = state.items.filter(i => !i.checked);
    saveItems(); saveFridge(); saveHistory();
    renderList(); renderFridge(); renderCart(); renderHistory();
    showToast('🎉', 'Course terminée !', 'Articles ajoutés au frigo et à l\'historique.');
    switchSubtab('done');
  });
}

// ═══════════════════════════════════════════════
// HISTORIQUE
// ═══════════════════════════════════════════════
function renderHistory() {
  const wrap = document.getElementById('historyWrap');
  const empty = document.getElementById('emptyHistory');
  const cnt = document.getElementById('histCount');
  if(cnt) cnt.textContent = state.history.length + ' session(s)';
  if(!state.history.length) {
    if(wrap) wrap.innerHTML = '';
    if(empty) empty.style.display = 'block';
    return;
  }
  if(empty) empty.style.display = 'none';
  if(wrap) wrap.innerHTML = state.history.map((s,i) => `
    <div class="hist-session">
      <div class="hist-session-hd" onclick="toggleHistSession(${i})">
        <div><div class="hist-session-date">🛒 Course du ${s.date}</div><div class="hist-session-meta">${s.items.length} articles · ${s.total}€</div></div>
        <span id="hist-arrow-${i}">▼</span>
      </div>
      <div class="hist-session-body" id="hist-body-${i}" style="display:none;">
        ${s.items.map(it => `<div class="hist-item"><span class="hist-item-em">${it.emoji||'🛒'}</span><span style="flex:1;">${it.name}</span><span style="color:var(--tx2);font-size:.75rem;">${it.price?it.price.toFixed(2)+'€':''}</span></div>`).join('')}
        <button class="btn sm acc" style="margin-top:8px;width:100%;" onclick="reorderFromHistory(${i})">🔄 Recommander ces articles</button>
      </div>
    </div>`).join('');
}

function toggleHistSession(i) {
  const body = document.getElementById('hist-body-' + i);
  const arrow = document.getElementById('hist-arrow-' + i);
  const open = body.style.display === 'block';
  body.style.display = open ? 'none' : 'block';
  if(arrow) arrow.textContent = open ? '▼' : '▲';
}

function reorderFromHistory(i) {
  const s = state.history[i]; let added = 0;
  s.items.forEach(it => {
    if(!state.items.some(si => si.name.toLowerCase() === it.name.toLowerCase() && !si.checked)) {
      state.items.unshift({id:'i'+Date.now()+Math.random().toString(36).slice(2,7),name:it.name,emoji:it.emoji,cat:'🍝 Épicerie',price:it.price||0,qty:'',checked:false,addedAt:Date.now()});
      added++;
    }
  });
  saveItems(); renderList(); switchSubtab('tobuy');
  showToast('✅', added + ' ajouté(s)', 'Depuis l\'historique.');
}

// ═══════════════════════════════════════════════
// AUTOCOMPLETE
// ═══════════════════════════════════════════════
let acTimeout;
function onSearchInput(val) {
  clearTimeout(acTimeout);
  if(!val.trim()) { document.getElementById('acList').style.display = 'none'; return; }
  acTimeout = setTimeout(() => {
    const matches = PRODUCTS.filter(p => p.name.toLowerCase().includes(val.toLowerCase())).slice(0,8);
    showAC('acList', 'addInput', matches);
  }, 150);
}

function showAC(listId, inputId, products) {
  const list = document.getElementById(listId);
  if(!products.length || !products) { if(list) list.style.display = 'none'; return; }
  const inp = document.getElementById(inputId);
  if(!inp || !list) return;
  // Use CSS absolute positioning (defined in .ac-list)
  list.style.position = '';
  list.style.zIndex = '';
  list.style.top = '';
  list.style.left = '';
  list.style.width = '';
  list.style.minWidth = '';
  list.style.display = 'block';
  list.innerHTML = products.map(p => {
    const safeName = (p.name||'').replace(/'/g,"&#39;");
    return '<div class="ac-item" onclick="acSelect(\'' + safeName + '\',\'' + listId + '\',\'' + inputId + '\')">'
      + '<span class="ac-item-em">' + (p.emoji||'🛍️') + '</span>'
      + '<span class="ac-item-nm">' + (p.name||'') + '</span>'
      + '<span class="ac-item-cat">' + (p.cat||'') + '</span>'
      + '</div>';
  }).join('');
}

function acSelect(name, listId, inputId) {
  document.getElementById(inputId).value = name;
  document.getElementById(listId).style.display = 'none';
  if(inputId === 'addInput') addItemFromInput();
  else if(inputId === 'fridgeInput') addFridgeItem();
}

document.addEventListener('click', e => {
  if(!e.target.closest('.ac-wrap')) document.querySelectorAll('.ac-list').forEach(l => l.style.display = 'none');
});

// ═══════════════════════════════════════════════
// SWIPE
// ═══════════════════════════════════════════════
function attachSwipe() {
  document.querySelectorAll('#itemsWrap .item').forEach(el => {
    let sx = 0, cx = 0, dragging = false;
    el.addEventListener('touchstart', e => { sx = e.touches[0].clientX; dragging = true; el.classList.add('swiping'); }, {passive:true});
    el.addEventListener('touchmove', e => {
      if(!dragging) return;
      cx = e.touches[0].clientX - sx;
      if(cx < 0) el.style.transform = `translateX(${Math.max(cx,-110)}px)`;
    }, {passive:true});
    el.addEventListener('touchend', () => {
      dragging = false; el.classList.remove('swiping');
      if(cx < -70) {
        const id = el.dataset.id;
        el.classList.add('deleting');
        el.style.transform = 'translateX(-110%)';
        el.style.opacity = '0';
        setTimeout(() => deleteItem(id), 220);
      } else { el.style.transform = ''; }
      cx = 0;
    });
  });
}

// ═══════════════════════════════════════════════
// EDIT MODAL
// ═══════════════════════════════════════════════
function openEdit(id) {
  const item = state.items.find(i => i.id === id);
  if(!item) return;
  state.editingItemId = id;
  document.getElementById('editModalInner').innerHTML = `
    <div class="mhdl"></div>
    <div class="modal-ti">Modifier l'article</div>
    <div class="edit-field"><label class="edit-label">Nom</label><input class="inp" id="editName" value="${item.name}"></div>
    <div class="edit-field"><label class="edit-label">Quantité / Note</label><input class="inp" id="editQty" value="${item.qty||''}"></div>
    <div class="edit-field"><label class="edit-label">Prix (€)</label><input class="inp" id="editPrice" type="number" value="${item.price||''}" placeholder="0.00" step="0.10" min="0"></div>
    <div class="edit-field"><label class="edit-label">Catégorie</label><div class="cat-selector" id="editCatSel">${CATEGORIES.map(c=>`<div class="cat-opt${item.cat===c?' on':''}" onclick="this.parentNode.querySelectorAll('.cat-opt').forEach(x=>x.classList.remove('on'));this.classList.add('on')" data-cat="${c}">${c}</div>`).join('')}</div></div>
    <div style="display:flex;gap:10px;margin-top:16px;">
      <button class="btn" style="flex:1;" onclick="closeEdit()">Annuler</button>
      <button class="btn acc" style="flex:1;" onclick="saveEdit()">Sauvegarder</button>
    </div>`;
  document.getElementById('editOverlay').classList.add('on');
}

function closeEdit() { document.getElementById('editOverlay').classList.remove('on'); state.editingItemId = null; }

function saveEdit() {
  const item = state.items.find(i => i.id === state.editingItemId);
  if(!item) return;
  item.name = document.getElementById('editName').value.trim() || item.name;
  item.qty = document.getElementById('editQty').value.trim();
  const pv = parseFloat(document.getElementById('editPrice').value);
  if(!isNaN(pv)) item.price = pv;
  const sel = document.querySelector('#editCatSel .cat-opt.on');
  if(sel) item.cat = sel.dataset.cat;
  saveItems(); closeEdit(); renderList();
  showToast('✅', item.name, 'Mis à jour.');
}

// ═══════════════════════════════════════════════

