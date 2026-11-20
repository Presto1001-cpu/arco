import { mmFromFreq, freqFromMm, stringFor, yin, freqToNote, CELLO_STRINGS } from '../cello-sound.mjs';
const eq = (a, b, t, m) => { if (Math.abs(a - b) > t) { console.error('FAIL', m, a, b); process.exit(1); } };
for (let s = 0; s < 4; s++) for (const mm of [0, 50, 120, 200, 300, 400]) eq(mmFromFreq(freqFromMm(mm, s), s), mm, 1e-6, 'round trip');
eq(mmFromFreq(CELLO_STRINGS[3][1] * 2 ** (7 / 12), 3), 690 * (1 - 2 ** (-7 / 12)), 1e-6, 'fifth above A = 7 semitones');
eq(freqFromMm(345, 0), CELLO_STRINGS[0][1] * 2, 0.01, 'half the string = octave');
eq(stringFor(100), 1, 0, 'G2 region -> G string'); eq(stringFor(230), 3, 0, 'A string'); eq(stringFor(60), -1, 0, 'below C');
const sr = 44100; for (const f of [65.4, 110, 196, 330, 587]) { const b = new Float32Array(4096); for (let i = 0; i < b.length; i++) b[i] = 0.4 * Math.sin(2 * Math.PI * f * i / sr) + 0.2 * Math.sin(4 * Math.PI * f * i / sr); const r = yin(b, sr, 60, 700); eq(r.freq, f, f * 0.01, 'yin ' + f); }
eq(freqToNote(220).cents, 0, 1e-6, 'A3'); console.log('sound roundtrip OK');
