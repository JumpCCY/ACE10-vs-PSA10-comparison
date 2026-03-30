
const app = document.getElementById('app');
const searchInput = document.getElementById('searchInput');
const sortBtns = document.querySelectorAll('.sort-btn');

// SVG placeholder — Pokemon-card-back style, inline so no external file needed
const PLACEHOLDER = "https://pokemoncardimages.pokedata.io/images/placeholder.webp";

let allCards = [];
let currentSort = 'psa_desc';
let currentSearch = '';
let maxAbsProfit = 1;

async function fetchCards() {
app.innerHTML = `<div class="state-msg"><div class="spinner"></div><h2>Scraping in progress</h2><p>Fetching prices — please wait</p></div>`;
try {
    const res = await fetch('/api/cards');
    const data = await res.json();

    if (data.message) {
    // Still scraping — poll every 10s
    setTimeout(fetchCards, 10000);
    return;
    }

    allCards = data.cards || [];
    document.getElementById('lastUpdated').textContent = 'Updated ' + (data.last_updated || '—');
    maxAbsProfit = Math.max(1, ...allCards.map(c => Math.abs(c['Potential Profit'] || 0)));
    render();
} catch (e) {
    app.innerHTML = `<div class="state-msg"><div class="spinner"></div><h2>Connection Error</h2><p>Retrying in 15s…</p></div>`;
    setTimeout(fetchCards, 15000);
}
}

function sortCards(cards) {
const c = [...cards];
switch (currentSort) {
    case 'psa_desc':    return c.sort((a,b) => (b['PSA 10']||0) - (a['PSA 10']||0));
    case 'psa_asc':     return c.sort((a,b) => (a['PSA 10']||0) - (b['PSA 10']||0));
    case 'profit_desc': return c.sort((a,b) => (b['Potential Profit']||0) - (a['Potential Profit']||0));
    case 'profit_asc':  return c.sort((a,b) => (a['Potential Profit']||0) - (b['Potential Profit']||0));
    default: return c;
}
}

function filterCards(cards) {
if (!currentSearch) return cards;
const q = currentSearch.toLowerCase();
return cards.filter(c => c.card_name.toLowerCase().includes(q));
}

function render() {
const visible = sortCards(filterCards(allCards));

if (!visible.length) {
    app.innerHTML = `<div class="grid"><div class="no-results">No cards match "${currentSearch}"</div></div>`;
    return;
}

const html = visible.map((card, i) => {
    const ace    = card['ACE 10'];
    const psa    = card['PSA 10'];
    const profit = card['Potential Profit'];
    const imgSrc = `https://pokemoncardimages.pokedata.io/images/${card.set_name.replace(/\s+/g, '+')}/${card.card_name.replace(/\D+/g, '')}.webp`;

    const profitClass = profit == null ? 'null' : profit >= 0 ? 'positive' : 'negative';
    const profitSign  = profit > 0 ? '+' : '';
    const profitLabel = profit == null ? 'N/A' : profitSign + '£' + Math.abs(profit).toFixed(2);
    const barPct      = profit == null ? 0 : Math.min(100, (Math.abs(profit) / maxAbsProfit) * 100);

    return `
    <div class="card" style="animation-delay:${Math.min(i * 25, 600)}ms">
        <div class="card-img-wrap">
        <img src="${imgSrc}" alt="${card.card_name}" onerror="this.onerror=null;this.src='${PLACEHOLDER}'"/>
        </div>
        <div class="card-info">
        <div class="card-header">
            <div class="card-name">${card.card_name}</div>
            <div class="profit-badge ${profitClass}">${profitLabel}</div>
        </div>
        <div class="prices">
            <div class="price-block">
            <div class="price-label">ACE 10</div>
            <div class="price-value ${ace == null ? 'na' : ''}">${ace != null ? '£' + parseFloat(ace).toFixed(2) : '—'}</div>
            </div>
            <div class="price-block">
            <div class="price-label">PSA 10</div>
            <div class="price-value ${psa == null ? 'na' : ''}">${psa != null ? '£' + parseFloat(psa).toFixed(2) : '—'}</div>
            </div>
        </div>
        </div>
    </div>`;
}).join('');

app.innerHTML = `<div class="grid">${html}</div>`;
}

searchInput.addEventListener('input', e => { currentSearch = e.target.value.trim(); render(); });

sortBtns.forEach(btn => {
btn.addEventListener('click', () => {
    sortBtns.forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    currentSort = btn.dataset.sort;
    render();
});
});

fetchCards();
