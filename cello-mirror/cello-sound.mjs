// Sound for the cello drawing: pitch detection, note <-> finger position on the string, and a bowed-string tone.
export const CELLO_STRINGS = [['C', 65.406], ['G', 97.999], ['D', 146.832], ['A', 220.0]];
const NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];
export function freqToNote(f, a4 = 440) { const m = 69 + 12 * Math.log2(f / a4), r = Math.round(m); return { name: NAMES[((r % 12) + 12) % 12] + (Math.floor(r / 12) - 1), midi: r, cents: (m - r) * 100 }; }
// Finger distance from the nut (mm) on string i for a given pitch; the vibrating length is L * f0 / f.
export function mmFromFreq(freq, stringIdx, L = 690, a4 = 440) { const f0 = CELLO_STRINGS[stringIdx][1] * a4 / 440; return L * (1 - f0 / freq); }
export function freqFromMm(mm, stringIdx, L = 690, a4 = 440) { return CELLO_STRINGS[stringIdx][1] * a4 / 440 * L / (L - mm); }
// Highest open string at or below the heard pitch (a guess: the same note can be played on two strings).
export function stringFor(freq, a4 = 440) { let p = -1; CELLO_STRINGS.forEach(([, f0], i) => { if (f0 * a4 / 440 <= freq * 1.012) p = i; }); return p; }
export function yin(buf, sr, minF = 60, maxF = 1100, thr = 0.15) {
  let e = 0; for (let i = 0; i < buf.length; i++) e += buf[i] * buf[i];
  const rms = Math.sqrt(e / buf.length); if (rms < 0.008) return { freq: null, prob: 0, rms };
  const half = buf.length >> 1, tauMax = Math.min(half - 1, Math.floor(sr / minF)), tauMin = Math.max(2, Math.floor(sr / maxF)), d = new Float32Array(tauMax + 2);
  for (let tau = 1; tau <= tauMax; tau++) { let s = 0; for (let j = 0; j < half; j++) { const x = buf[j] - buf[j + tau]; s += x * x; } d[tau] = s; }
  d[0] = 1; let run = 0; for (let tau = 1; tau <= tauMax; tau++) { run += d[tau]; d[tau] = run ? d[tau] * tau / run : 1; }
  let tau = -1; for (let t = tauMin; t <= tauMax; t++) if (d[t] < thr) { while (t + 1 <= tauMax && d[t + 1] < d[t]) t++; tau = t; break; }
  if (tau < 0) return { freq: null, prob: 0, rms };
  let t0 = tau; if (tau > 1 && tau < tauMax) { const a = d[tau - 1], b = d[tau], c = d[tau + 1], den = a - 2 * b + c; if (den) t0 = tau + (a - c) / (2 * den); }
  return { freq: sr / t0, prob: 1 - d[tau], rms };
}
// A bowed-string stand-in: sawtooth through a low-pass, slow vibrato, soft attack and release. Not a sampled cello.
export function makeVoice(ctx) {
  let o = null, g = null;
  return {
    on(freq) {
      if (!o) {
        o = ctx.createOscillator(); o.type = 'sawtooth'; const lp = ctx.createBiquadFilter(); lp.type = 'lowpass'; lp.Q.value = 0.7; g = ctx.createGain(); g.gain.value = 0;
        const lfo = ctx.createOscillator(), lg = ctx.createGain(); lfo.frequency.value = 5.2; lg.gain.value = 0; lfo.connect(lg); lg.connect(o.detune); lfo.start();
        o.connect(lp); lp.connect(g); g.connect(ctx.destination); o.start(); o._lp = lp; o._lg = lg;
        const t = ctx.currentTime; g.gain.setTargetAtTime(0.22, t, 0.06); lg.gain.setTargetAtTime(14, t + 0.25, 0.3);
      }
      o.frequency.setTargetAtTime(freq, ctx.currentTime, 0.015); o._lp.frequency.setTargetAtTime(Math.min(freq * 7, 3500), ctx.currentTime, 0.02);
    },
    off() { if (!o) return; const t = ctx.currentTime; g.gain.setTargetAtTime(0, t, 0.08); const x = o; o = null; setTimeout(() => { try { x.stop(); } catch (e) {} }, 500); },
  };
}
