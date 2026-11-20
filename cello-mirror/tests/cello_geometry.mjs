import assert from 'node:assert/strict';
import { SPEC, outline, layout, neckLength, pchip, stations } from '../cello-geometry.mjs';
const pts = outline(SPEC, 0.25);
const ys = pts.map(p => p[1]), xs = pts.map(p => p[0]);
assert(Math.abs(Math.max(...ys) - Math.min(...ys) - SPEC.bodyLength.v) < 0.01, 'body length');
const widthIn = (a, b) => { const s = pts.filter(p => p[1] >= a && p[1] <= b).map(p => Math.abs(p[0])); return 2 * Math.max(...s); };
const near = (v, want, tol, name) => assert(Math.abs(v - want) <= tol, `${name}: got ${v.toFixed(2)}, want ${want}`);
near(widthIn(0, 300), SPEC.upperBout.v, 0.5, 'upper bout');
near(widthIn(480, 756), SPEC.lowerBout.v, 0.5, 'lower bout');
// the narrowest point is the stated middle bout, exactly
const narrow = Math.min(...pts.filter(p => p[1] > 300 && p[1] < 420).map(p => 2 * Math.abs(p[0]))); near(narrow, SPEC.middleBout.v, 0.3, 'narrowest');
// symmetric and no overshoot past the stated maxima
assert(pts.every(([x, y]) => pts.some(([x2, y2]) => Math.abs(x2 + x) < 1e-9 && y2 === y)), 'symmetric');
assert(Math.max(...xs.map(Math.abs)) * 2 <= SPEC.lowerBout.v + 0.01, 'no overshoot');
// order of widths: lower > upper > middle
assert(SPEC.lowerBout.v > SPEC.upperBout.v && SPEC.upperBout.v > SPEC.middleBout.v);
// string length is neck plus stop, and equals nut to bridge in the layout
const L = layout(SPEC); near(L.bridgeY - L.nut, SPEC.stringLength.v, 1e-9, 'nut to bridge'); near(neckLength(SPEC), 290, 1e-9, 'neck');
near(Math.hypot(L.strings[0].bridge[0] - L.strings[0].nut[0], L.strings[0].bridge[1] - L.strings[0].nut[1]), SPEC.stringLength.v, 0.5, 'outer string is almost the same length');
assert(L.fbEnd < L.bridgeY && L.fbEnd > 0, 'fingerboard ends over the body, short of the bridge');
// every spec value is inside the range seen in sources
for (const [k, e] of Object.entries(SPEC)) assert(e.v >= e.seen[0] && e.v <= e.seen[1], k + ' outside its own range');
// pchip passes through its stations
const st = stations(SPEC), f = pchip(st); st.forEach(([y, w]) => near(f(y), w, 1e-6, 'station ' + y));
console.log('cello geometry OK');
