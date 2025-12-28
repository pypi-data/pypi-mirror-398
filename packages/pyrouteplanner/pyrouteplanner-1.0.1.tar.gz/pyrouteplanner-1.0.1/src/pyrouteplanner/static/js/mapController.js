import { totalDistance } from './geo.js'

function randColorFactory() {
    let used = 0;

    return () => {
        const hue = (used * 137.508) % 360; // golden-angle spacing
        used++;
        // adjust saturation/lightness for contrast
        return `hsl(${hue}, 70%, 45%)`;
    };
}

const randColor = randColorFactory();

export default class MapController {
    constructor(mapID, opts={}) {
        this.map = L.map(mapID).setView(opts.center, opts.zoom);

        this._streetLayer = L.tileLayer(
            opts.tileUrl || 'https://{s}.tile.openstreetmaps.org/{z}/{x}/{y}.png', 
            { attribution: opts.attribution || '&copy; OpenTopoMap contributors' });
        this._topoLayer = L.tileLayer(
            opts.topoUrl || 'https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',
            { attribution: opts.topoAttribution || '&copy; OpenTopoMap contributors' }); 

        this.activeTile = (opts.defaultLayer === 'topo') ? 'topo' : 'street';
        if (this.activeTile === 'street') this._streetLayer.addTo(this.map);
        else this._topoLayer.addTo(this.map);

        this.active = this._createPath(true);
        this.history = []; // array of path objects
        this.historyLayer = L.layerGroup().addTo(this.map);

        // TODO
        this.onPathUpdated = () => null;
        this.onPathFinished = () => null;

        this.map.on('click', (e) => {
            this.addPoint(e.latlng);
        });
    }

    setTileSource(name) {
        if (name === this.activeTile) return;
        if (name === 'street') {
            if (this._topoLayer) this.map.removeLayer(this._topoLayer);
            this.map.addLayer(this._streetLayer);
            this._streetLayer.bringToBack();
            this.activeTile = 'street';
        } else if (name === 'topo') {
            if (this._streetLayer) this.map.removeLayer(this._streetLayer);
            this.map.addLayer(this._topoLayer);
            this._topoLayer.bringToBack();
            this.activeTile = 'topo';
        }
    }

    getTileSource() {
        return this.activeTile;
    }

    _createPath(isActive = false) {
        const color = randColor();
        return {
            id: Date.now().toString(36) + Math.random().toString(36).slice(2,8),
            latlngs: [],
            markers: [],
            polyline: L.polyline([], { color }).addTo(this.map),
            color,
            isActive
        };
    }

    addPoint(latlng) {
        const p = {lat: +latlng.lat, lng: +latlng.lng};

        this.active.latlngs.push(p);
        const marker = L.marker([p.lat, p.lng]).addTo(this.map);
        this.active.markers.push(marker);
        this.active.polyline.setLatLngs(
            this.active.latlngs.map(p => [p.lat, p.lng]));

        this.onPathUpdated(this.active);
    }

    undoLastPoint() {
        if (!this.active.latlngs.length) return;
        this.active.latlngs.pop();
        const m = this.active.markers.pop();
        if (m) this.map.removeLayer(m);
        this.active.polyline.setLatLngs(
            this.active.latlngs.map(p => [p.lat, p.lng]));

        this.onPathUpdated(this.active);
    }

    finishActivePath() {
        if (this.active.latlngs.length < 2) return null;
        
        // compute total distance of path
        const meters = totalDistance(this.active.latlngs);
        
        // move polyline and markers into history layer
        this.historyLayer.addLayer(this.active.polyline);

        // mark start and end
        this.active.markers[0].bindTooltip('Start', 
            {permanent: true, direction: 'right'}).openTooltip();
        this.active.markers[this.active.markers.length-1].bindTooltip('Finish', 
            {permanent: true, direction: 'right'}).openTooltip();

        // keep first and last markers
        const lastIndex = this.active.markers.length - 1;
        for (let i = 0; i <= lastIndex; i++) {
            const m = this.active.markers[i];
            if (i === 0 || i === lastIndex) continue;
            if (this.map.hasLayer(m)) this.map.removeLayer(m);
        }
        this.history.push(this.active);

        const finished = this.active;
        finished.isActive = false;
        // add the total distance to this object for later use
        finished.distanceMeters = meters;
        
        // create a new active path
        this.active = this._createPath(true);

        this.onPathFinished(finished);
        return finished;
    }

    clearActivePath() {
        if (this.active.polyline) this.map.removeLayer(this.active.polyline);
        this.active.markers.forEach(m => this.map.removeLayer(m));
        this.active = this._createPath(true);

        this.onPathUpdated(this.active);
    }

    center(latlng, zoom) {
        this.map.setView([latlng.lat, latlng.lng], zoom || this.map.getZoom());
    }

    getActiveLatLngs() {
        return this.active.latlngs.slice();
    }
}
