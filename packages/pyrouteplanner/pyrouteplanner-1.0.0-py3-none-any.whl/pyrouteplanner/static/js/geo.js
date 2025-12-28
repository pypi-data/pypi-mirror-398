export function radians(deg) {
    return deg * Math.PI / 180;
}

// p and q are geopoints represented by objects {lat: number, lng: number}
// https://en.wikipedia.org/wiki/Haversine_formula
export function haversineDistance(p, q) {
    const R = 6371000; // Earth rad in m

    const phi1 = radians(p['lat']);
    const phi2 = radians(q['lat']);
    const lambda1 = radians(p['lng']);
    const lambda2 = radians(q['lng']);

    const dphi = phi2 - phi1;
    const dlambda = lambda2 - lambda1;

    const a = Math.sin(dphi / 2) ** 2 + 
        Math.cos(phi1) * Math.cos(phi2) * Math.sin(dlambda / 2) ** 2;

    return 2 * R * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

// latlngs is an array of {lat, lng}
export function totalDistance(latlngs) {
    if (latlngs.length < 2) return 0;
    
    let d = 0
    for (let i = 0; i < latlngs.length - 1; i++) {
        d += haversineDistance(latlngs[i], latlngs[i+1]);
    }

    return d;
}

export function formatDistance(meters, unit='m') {
    let d;
    switch (unit) {
        case 'mi':
            d = meters / 1609.344;
            break;
        case 'km':
            d = meters / 1000;
            break;
        case 'ft':
            d = meters / 0.3048;
            break;
        default:
            d = meters;
    }
    return d.toFixed(2) + ' ' + unit
}
