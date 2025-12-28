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
totalDistanceOutput.id = 'total-distance-output';
controls.appendChild(totalDistanceOutput);

const liveDistanceOutput = document.createElement('div');
liveDistanceOutput.id = 'live-distance';
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

    const swatch = document.createElement('span');
    swatch.className = 'swatch';
    swatch.style.background = color;

    const text = document.createElement('span');
    text.textContent = formatted;

    row.appendChild(swatch);
    row.appendChild(text);

    totalDistanceOutput.appendChild(row);
}
