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
  bowLength:    { v: 720, seen: [711, 730], status: 'verified', note: 'full-size cello bow, tip to end of button' },
};
export const stringLength = s => s.stringLength.v;
export const neckLength = s => s.stringLength.v - s.stop.v;           // nut to top edge of body; string length = neck + stop

// Where along the body each width occurs and the shape between them is NOT verified: the stations below are my estimate. Widths are exact by construction.
export function stations(s) {
  const L = s.bodyLength.v, U = s.upperBout.v / 2, C = s.middleBout.v / 2, B = s.lowerBout.v / 2, k = L / 756;
  return [[0, 0], [6, 0.222 * U], [20, 0.41 * U], [45, 0.615 * U], [85, 0.825 * U], [130, 0.947 * U], [175, 0.99 * U], [210, U], [245, 0.955 * U], [285, 0.83 * U], [325, 0.71 * U],
    [352, C], [385, 1.03 * C], [430, 1.17 * C], [485, 0.78 * B], [545, 0.915 * B], [600, B], [650, 0.94 * B], [695, 0.79 * B], [728, 0.55 * B], [744, 0.35 * B], [752, 0.18 * B], [756, 0]]
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
