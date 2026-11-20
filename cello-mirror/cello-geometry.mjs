// Full-size (4/4) cello geometry in millimetres. y runs down the instrument from the top edge of the body (0); x is across, 0 on the centre line.
// SPEC values are the middle of what several makers and museums publish; `seen` is the range found, `status` says how well it is backed.
export const SPEC = {
  bodyLength:   { v: 756, seen: [745, 762], status: 'verified', note: 'Stradivari Davidov-type 756, Form B 759, workshop cellos 756-762' },
  upperBout:    { v: 342, seen: [340, 345], status: 'verified', note: 'Gore-Booth 341.5, makers 340-345' },
  middleBout:   { v: 233, seen: [229, 238], status: 'verified', note: 'Gore-Booth 229, makers 233-238' },
  lowerBout:    { v: 437, seen: [432, 440], status: 'verified', note: 'Gore-Booth 437, makers 432-440' },
  stop:         { v: 400, seen: [400, 405], status: 'verified', note: 'top edge of body to bridge' },
  stringLength: { v: 690, seen: [690, 696], status: 'verified', note: 'string makers use 690 for full size; makers 690-696' },
  fingerboard:  { v: 580, seen: [578, 585], status: 'verified', note: 'length of ebony fingerboard' },
  fbWidthNut:   { v: 32,  seen: [31.5, 32.5], status: 'verified' },
  fbWidthEnd:   { v: 62.5, seen: [62, 63.5], status: 'verified' },
  stringSpanNut:    { v: 23, seen: [22.5, 23.5], status: 'verified', note: 'outer string to outer string' },
  stringSpanBridge: { v: 47, seen: [46, 48], status: 'verified', note: 'outer string to outer string' },
  bridgeFoot:   { v: 90,  seen: [88, 92], status: 'verified' },
  pegbox:       { v: 135, seen: [135, 135], status: 'single source' },
  ribHeight:    { v: 118, seen: [115, 126], status: 'verified', note: 'about 116 at neck, 122 at bottom' },
  afterLength:  { v: 115, seen: [115, 115], status: 'estimate', note: 'bridge to tailpiece, about one sixth of the string length' },
  tailpiece:    { v: 175, seen: [175, 175], status: 'estimate', note: 'length of the tailpiece body' },
  bowLength:    { v: 720, seen: [711, 730], status: 'verified', note: 'full-size cello bow, tip to end of button' },
};
export const stringLength = s => s.stringLength.v;
export const neckLength = s => s.stringLength.v - s.stop.v;           // nut to top edge of body; string length = neck + stop

// Where along the body each width occurs and the shape between them is NOT verified: the stations below are my estimate. Widths are exact by construction.
export function stations(s) {
  const L = s.bodyLength.v, U = s.upperBout.v / 2, C = s.middleBout.v / 2, B = s.lowerBout.v / 2, k = L / 756;
  // Landmark positions (fractions of body length) were checked against a front-view drawing of a cello: upper bout widest ~0.19, upper corners ~0.32, waist ~0.415, lower corners ~0.575, lower bout widest ~0.78. The curves between them are my own.
  return [[0, 0], [5, 0.20 * U], [16, 0.40 * U], [36, 0.60 * U], [62, 0.79 * U], [98, 0.935 * U], [140, U], [180, 0.985 * U], [214, 0.95 * U], [236, 0.915 * U], [250, 0.84 * U], [268, 0.76 * U], [292, 0.70 * U], [314, C],
    [345, 1.02 * C], [380, 1.08 * C], [404, 1.17 * C], [422, 1.40 * C], [436, 0.80 * B], [462, 0.855 * B], [500, 0.915 * B], [545, 0.965 * B], [590, B], [640, 0.965 * B], [690, 0.84 * B], [725, 0.62 * B], [745, 0.35 * B], [752, 0.18 * B], [756, 0]]
    .map(([y, w]) => [y * k, w]);
}
// Monotone cubic (no overshoot), so the stated widths are the true maxima.
export function pchip(pts) {
  const n = pts.length, h = [], d = [], m = new Array(n).fill(0);
  for (let i = 0; i < n - 1; i++) { h[i] = pts[i + 1][0] - pts[i][0]; d[i] = (pts[i + 1][1] - pts[i][1]) / h[i]; }
  for (let i = 1; i < n - 1; i++) { if (d[i - 1] * d[i] <= 0) m[i] = 0; else { const w1 = 2 * h[i] + h[i - 1], w2 = h[i] + 2 * h[i - 1]; m[i] = (w1 + w2) / (w1 / d[i - 1] + w2 / d[i]); } }
  m[0] = d[0]; m[n - 1] = d[n - 2];
  return y => { let i = Math.min(n - 2, Math.max(0, pts.findIndex((p, j) => j < n - 1 && y >= p[0] && y <= pts[j + 1][0])));
    const t = (y - pts[i][0]) / h[i], t2 = t * t, t3 = t2 * t; return (2 * t3 - 3 * t2 + 1) * pts[i][1] + (t3 - 2 * t2 + t) * h[i] * m[i] + (-2 * t3 + 3 * t2) * pts[i + 1][1] + (t3 - t2) * h[i] * m[i + 1]; };
}
export function outline(s, step = 1) {
  const L = s.bodyLength.v, w = pchip(stations(s)), right = [];
  for (let y = 0; y <= L + 1e-9; y += step) right.push([Math.max(0, w(Math.min(y, L))), y]);
  return right.concat(right.slice().reverse().map(([x, y]) => [-x, y]));
}
export function layout(s) {
  const nut = -neckLength(s), fbEnd = nut + s.fingerboard.v, L = s.bodyLength.v;
  const span = (a, b, t) => a + (b - a) * t, strings = [0, 1, 2, 3].map(i => { const u = i / 3 - 0.5;
    return { name: 'CGDA'[i], nut: [u * s.stringSpanNut.v, nut], bridge: [u * s.stringSpanBridge.v, s.stop.v] }; });
  return { nut, fbEnd, strings, bridgeY: s.stop.v, pegboxTop: nut - s.pegbox.v, endpinY: L };
}

// Offsets a closed outline inwards by d (mm), along averaged normals.
export function inset(pts, d) {
  const n = pts.length; return pts.map((p, i) => { const a = pts[(i - 1 + n) % n], b = pts[(i + 1) % n]; let tx = b[0] - a[0], ty = b[1] - a[1]; const l = Math.hypot(tx, ty) || 1; tx /= l; ty /= l;
    // outline runs down the right side, so the inward normal is (+ty, -tx) turned toward the centre line
    let nx = -ty, ny = tx; if (nx * p[0] > 0) { nx = -nx; ny = -ny; } return [p[0] + nx * d, p[1] + ny * d]; });
}
// Draws the cello on a 2D canvas context. (x0, y0) is where the centre line meets the top edge of the body, in pixels; k is pixels per millimetre.
export function drawCello(c, s, x0, y0, k) {
  const L = layout(s), X = x => x0 + x * k, Y = y => y0 + y * k, u = k / 0.85;
  const line = (pts, close) => { c.beginPath(); pts.forEach(([x, y], i) => i ? c.lineTo(X(x), Y(y)) : c.moveTo(X(x), Y(y))); if (close) c.closePath(); };
  const out = outline(s, 2); c.save(); c.lineCap = 'butt'; c.lineJoin = 'round';
  // body: edge, then top plate with a soft varnish gradient, then purfling
  line(out, true); c.fillStyle = '#2a1a0e'; c.fill();
  const g = c.createRadialGradient(X(-60), Y(s.bodyLength.v * 0.62), 10 * k, X(0), Y(s.bodyLength.v * 0.5), 330 * k); g.addColorStop(0, '#b9742f'); g.addColorStop(0.55, '#8a4f1f'); g.addColorStop(1, '#4a2a12');
  line(inset(out, 3), true); c.fillStyle = g; c.fill(); c.strokeStyle = '#d9a566'; c.lineWidth = Math.max(1.5, 2 * u); c.stroke();
  line(inset(out, 11), true); c.strokeStyle = 'rgba(20,12,6,.85)'; c.lineWidth = Math.max(1, 1.6 * u); c.stroke();
  // neck, pegbox with open slot, scroll
  c.fillStyle = '#6b3d18'; line([[-19, L.nut], [-27, 8], [27, 8], [19, L.nut]], true); c.fill();
  c.fillStyle = '#7a4520'; c.strokeStyle = '#d9a566'; c.lineWidth = Math.max(1, 1.5 * u);
  line([[-23, L.nut], [-28, L.pegboxTop], [28, L.pegboxTop], [23, L.nut]], true); c.fill(); c.stroke();
  c.fillStyle = '#1a0f07'; line([[-9, L.nut - 6], [-11, L.pegboxTop + 14], [11, L.pegboxTop + 14], [9, L.nut - 6]], true); c.fill();
  const sc = [0, L.pegboxTop - 30]; c.fillStyle = '#7a4520'; c.beginPath(); c.arc(X(sc[0]), Y(sc[1]), 33 * k, 0, 7); c.fill(); c.stroke();
  c.strokeStyle = '#2a1a0e'; c.lineWidth = Math.max(1, 2 * u); c.beginPath(); for (let t = 0; t <= 4.2 * Math.PI; t += 0.1) { const r = (2 + 1.9 * t), x = sc[0] + Math.cos(t + 1) * r * 0.9, y = sc[1] + Math.sin(t + 1) * r * 0.9; t ? c.lineTo(X(x), Y(y)) : c.moveTo(X(x), Y(y)); } c.stroke();
  // pegs
  c.strokeStyle = '#d9a566'; c.fillStyle = '#2a1a0e'; c.lineWidth = Math.max(1, 1.5 * u);
  [[-1, L.pegboxTop + 38], [-1, L.pegboxTop + 78], [1, L.pegboxTop + 58], [1, L.pegboxTop + 98]].forEach(([sg, y]) => { c.beginPath(); c.moveTo(X(sg * 24), Y(y)); c.lineTo(X(sg * 46), Y(y)); c.stroke(); c.beginPath(); c.ellipse(X(sg * 58), Y(y), 12 * k, 18 * k, 0, 0, 7); c.fill(); c.stroke(); });
  // fingerboard, ebony, with highlight
  c.fillStyle = '#0b0b0d'; line([[-s.fbWidthNut.v / 2, L.nut], [s.fbWidthNut.v / 2, L.nut], [s.fbWidthEnd.v / 2, L.fbEnd], [-s.fbWidthEnd.v / 2, L.fbEnd]], true); c.fill();
  c.strokeStyle = 'rgba(255,255,255,.10)'; c.lineWidth = Math.max(1, 1.2 * u); line([[-s.fbWidthNut.v / 2 + 2, L.nut], [-s.fbWidthEnd.v / 2 + 2, L.fbEnd]]); c.stroke();
  // tailpiece with fine-tuner holes, tail gut to the endpin button
  const tp0 = L.bridgeY + s.afterLength.v, tp1 = tp0 + s.tailpiece.v;
  c.fillStyle = '#16100b'; c.strokeStyle = '#6f5535'; c.lineWidth = Math.max(1, 1.5 * u);
  c.beginPath(); c.moveTo(X(-25), Y(tp0)); c.lineTo(X(25), Y(tp0)); c.quadraticCurveTo(X(26), Y(tp0 + 40), X(15), Y(tp1 - 14)); c.quadraticCurveTo(X(0), Y(tp1 + 8), X(-15), Y(tp1 - 14)); c.quadraticCurveTo(X(-26), Y(tp0 + 40), X(-25), Y(tp0)); c.closePath(); c.fill(); c.stroke();
  c.fillStyle = '#8f8f96'; L.strings.forEach(st => { c.beginPath(); c.arc(X(st.bridge[0] * 0.4), Y(tp0 + 10), 3.2 * k, 0, 7); c.fill(); });
  c.strokeStyle = '#6f5535'; c.lineWidth = Math.max(1, 2 * u); line([[0, tp1], [0, s.bodyLength.v - 4]]); c.stroke();
  c.fillStyle = '#16100b'; c.beginPath(); c.arc(X(0), Y(s.bodyLength.v - 4), 7 * k, 0, 7); c.fill();
  // f-holes: S-curve with an eye at each end
  c.strokeStyle = '#120a05'; c.fillStyle = '#120a05'; c.lineCap = 'round';
  for (const sg of [-1, 1]) {
    const ft = L.bridgeY - 64, fb = L.bridgeY + 64;
    c.lineWidth = Math.max(2, 5 * u); c.beginPath(); c.moveTo(X(sg * 70), Y(ft + 8)); c.bezierCurveTo(X(sg * 56), Y(ft + 40), X(sg * 54), Y(L.bridgeY - 4), X(sg * 58), Y(L.bridgeY + 8)); c.bezierCurveTo(X(sg * 62), Y(L.bridgeY + 24), X(sg * 78), Y(fb - 22), X(sg * 70), Y(fb - 6)); c.stroke();
    c.beginPath(); c.arc(X(sg * 78), Y(ft), 5.5 * k, 0, 7); c.fill(); c.beginPath(); c.arc(X(sg * 72), Y(fb + 4), 7 * k, 0, 7); c.fill();
    c.fillStyle = '#6b3d18'; c.beginPath(); c.arc(X(sg * 61), Y(L.bridgeY), 2 * k, 0, 7); c.fill(); c.fillStyle = '#120a05';
  }
  c.lineCap = 'butt';
  // strings
  const cols = ['#cfd6dc', '#cfd6dc', '#e3e6e9', '#f0f2f4']; c.lineWidth = Math.max(0.8, 1.4 * u);
  L.strings.forEach((st, i) => { c.strokeStyle = cols[i]; c.beginPath(); c.moveTo(X(st.nut[0]), Y(st.nut[1])); c.lineTo(X(st.bridge[0]), Y(st.bridge[1])); c.lineTo(X(st.bridge[0] * 0.4), Y(tp0 + 10)); c.stroke(); });
  // bridge, seen face-on: arched top, two feet
  c.fillStyle = '#e8cf9f'; c.strokeStyle = '#8a6b46'; c.lineWidth = Math.max(1, 1.2 * u);
  c.beginPath(); c.moveTo(X(-45), Y(L.bridgeY + 8)); c.lineTo(X(-45), Y(L.bridgeY - 1)); c.quadraticCurveTo(X(0), Y(L.bridgeY - 14), X(45), Y(L.bridgeY - 1)); c.lineTo(X(45), Y(L.bridgeY + 8)); c.lineTo(X(30), Y(L.bridgeY + 8)); c.quadraticCurveTo(X(0), Y(L.bridgeY - 4), X(-30), Y(L.bridgeY + 8)); c.closePath(); c.fill(); c.stroke();
  // endpin
  c.strokeStyle = '#9aa7b3'; c.lineWidth = Math.max(2, 4 * u); line([[0, s.bodyLength.v], [0, s.bodyLength.v + 220]]); c.stroke();
  c.restore();
}
// The bow lane: halfway between the end of the fingerboard and the bridge (bow square to the strings).
export const bowLaneY = s => { const L = layout(s); return (L.fbEnd + L.bridgeY) / 2; };
