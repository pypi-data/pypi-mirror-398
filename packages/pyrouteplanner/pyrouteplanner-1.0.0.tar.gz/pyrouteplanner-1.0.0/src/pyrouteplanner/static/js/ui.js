import MapController from './mapController.js'
import { formatDistance, totalDistance } from './geo.js'

const mc = new MapController('map', { 
    tileUrl: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    attribution: '&copy; OpenStreetMap contributors',
    center: {lat: 37.229, lng: -80.414},
    zoom: 12
    });

// controls container
const controls = document.createElement('div');
controls.id = 'controls';
document.body.appendChild(controls);

// search row
const searchRow = document.createElement('div');
searchRow.id = 'search-row';

const searchInput = document.createElement('input');
searchInput.id = 'search-input';
searchInput.type = 'text';
searchInput.placeholder = 'Search place or address';

const searchButton = document.createElement('button');
searchButton.id = 'search-button';
searchButton.textContent = 'Search';

searchRow.appendChild(searchInput);
searchRow.appendChild(searchButton);
controls.appendChild(searchRow);

// second row
const secondRow = document.createElement('div');
secondRow.id = 'button-row'

const undoButton = document.createElement('button');
undoButton.textContent = 'Undo';

const clearButton = document.createElement('button');
clearButton.textContent = 'Clear';

const tileSelect = document.createElement('select');
tileSelect.id = 'tile-select';

const optStreet = document.createElement('option');
optStreet.value = 'street';
optStreet.textContent = 'Street';

const optTopo = document.createElement('option');
optTopo.value = 'topo'
optTopo.textContent = 'Topographic';

tileSelect.appendChild(optStreet);
tileSelect.appendChild(optTopo);
secondRow.appendChild(tileSelect);

secondRow.appendChild(undoButton);
secondRow.appendChild(clearButton);
controls.appendChild(secondRow);

// third row
const thirdRow = document.createElement('div');

const calcButton = document.createElement('button');
calcButton.id = 'calculate-distance';
calcButton.textContent = 'Calculate Distance';
calcButton.disabled = true;

const unitSelect = document.createElement('select');
unitSelect.id = 'unit-select';
['mi','km','m', 'ft'].forEach(v => {
  const opt = document.createElement('option');
  opt.value = v; opt.textContent = v;
  unitSelect.appendChild(opt);
});

thirdRow.appendChild(calcButton);
thirdRow.appendChild(unitSelect);
controls.appendChild(thirdRow);

const saved = localStorage.getItem('tileSource');
const initial = (saved === 'street' || saved === 'topo') ? saved : (mc.getTileSource ? mc.getTileSource() : 'street');
tileSelect.value = initial;
mc.setTileSource(initial);

tileSelect.addEventListener('change', (e) => {
    const v = e.target.value;
    mc.setTileSource(v);
    localStorage.setItem('tileSource', v);
});

undoButton.addEventListener('click', () => mc.undoLastPoint());
clearButton.addEventListener('click', () => mc.clearActivePath());

searchButton.addEventListener('click', () => 
    searchAndCenter(searchInput.value));
searchInput.addEventListener('keydown', (e) => { 
    if (e.key === 'Enter') searchAndCenter(e.target.value); 
});

calcButton.addEventListener('click', () => {
    const finished = mc.finishActivePath();
    if (!finished) return;
});

const totalDistanceOutput = document.createElement('div');
totalDistanceOutput.id = 'distance-output';
totalDistanceOutput.style.maxHeight = '50vh';
totalDistanceOutput.style.overflow = 'auto';
totalDistanceOutput.style.background = 'white';
totalDistanceOutput.style.padding = '6px';
totalDistanceOutput.style.boxShadow = '0 2px 6px rgba(0,0,0,0.15)';
controls.appendChild(totalDistanceOutput);

const liveDistanceOutput = document.createElement('div');
liveDistanceOutput.id = 'live-distance';
liveDistanceOutput.style.position = 'fixed';
liveDistanceOutput.style.left = '10px';
liveDistanceOutput.style.bottom = '10px';
liveDistanceOutput.style.padding = '6px';
liveDistanceOutput.style.fontSize = '90%';
liveDistanceOutput.style.color = '#333';
liveDistanceOutput.style.background = 'white';
liveDistanceOutput.style.boxShadow = '0 2px 6px rgba(0,0,0,0.12)';
document.body.appendChild(liveDistanceOutput);

mc.onPathUpdated = (active) => {
    const meters = totalDistance(active.latlngs);
    liveDistanceOutput.textContent = `Current: ${formatDistance(meters, unitSelect.value)}`;
    calcButton.disabled = active.latlngs.length < 2;
};

mc.onPathFinished = (finished) => {
    appendDistanceRow(finished.distanceMeters, finished.color);
};

// search using Nominatim
async function searchAndCenter(q){
    if (!q) return;

    const res = await fetch('https://nominatim.openstreetmap.org/search?format=json&q='
        + encodeURIComponent(q));
    const r = (await res.json())[0];

    if (!r) return alert('No results');

    mc.center({ lat: parseFloat(r.lat), lng: parseFloat(r.lon)}, 15);
}

function appendDistanceRow(meters, color) {
    const unit = unitSelect.value;
    const formatted = formatDistance(meters, unit);

    const row = document.createElement('div');
    row.className = 'distance-row';
    row.style.display = 'flex';
    row.style.alignItems = 'center';
    row.style.padding = '4px 6px';
    row.style.borderBottom = '1px solid #eee';

    const swatch = document.createElement('span');
    swatch.style.width = '14px';
    swatch.style.height = '14px';
    swatch.style.borderRadius = '3px';
    swatch.style.marginRight = '8px';
    swatch.style.background = color;
    swatch.style.flex = '0 0 auto';

    const text = document.createElement('span');
    text.textContent = formatted;

    row.appendChild(swatch);
    row.appendChild(text);

    totalDistanceOutput.appendChild(row);
}
