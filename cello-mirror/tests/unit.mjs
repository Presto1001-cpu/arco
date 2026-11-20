// top-level await is used below
const m = await import(process.env.APP_MJS);
import assert from 'node:assert';
// pose: shoulders level, elbow below, wrist forward
const P=Array.from({length:33},()=>({x:.5,y:.5,visibility:1}));
P[11]={x:.6,y:.4,visibility:1};P[12]={x:.4,y:.4,visibility:1};P[14]={x:.35,y:.6,visibility:1};P[16]={x:.2,y:.6,visibility:1};
const e=m.elbowMetrics(P,'right',1);
assert(Math.abs(e.rel-1.0)<1e-9,'rel '+e.rel);          // elbow 0.2 below, shoulder width 0.2
assert(Math.abs(e.angle-104.04)<0.1,'angle '+e.angle);
assert.equal(m.elbowState(1.0,1.0,.2).state,'green');
assert.equal(m.elbowState(1.3,1.0,.2).msg,'Elbow dropped');
assert.equal(m.elbowState(0.7,1.0,.2).msg,'Elbow raised');
assert.equal(m.elbowState(1,null,.2).state,'none');
assert.equal(m.elbowMetrics(P,'left',1).vis,1);
// hand shape / jump
const H=Array.from({length:21},()=>({x:0,y:0}));H[0]={x:0,y:0};H[9]={x:0,y:.2};H[5]={x:0,y:.1};H[8]={x:0,y:.2};
const s1=m.handShape(H,1);assert(Math.abs(s1.indexRatio-.5)<1e-9);
assert.equal(m.isJump(s1,{palm:s1.palm,indexRatio:.5}),false);
assert.equal(m.isJump(s1,{palm:s1.palm,indexRatio:.9}),true);
// motion + bands: 90 frames, fast third loses the hand
const frames=[];for(let i=0;i<90;i++){const mo=i<30?1:i<60?5:20;frames.push({motion:i===0?null:mo+i*1e-3,det:mo<20?true:i%2===0,conf:.9,jump:i%10===0?true:false});}
const s=m.summarize(frames);
assert.equal(s.bands[0].detectedPct,100);assert(Math.abs(s.bands[2].detectedPct-50)<5,'fast '+s.bands[2].detectedPct);
assert.equal(m.verdict(95),'good');assert.equal(m.verdict(75),'shaky');assert.equal(m.verdict(40),'poor');
assert.equal(m.motionEnergy(new Uint8ClampedArray([0,0,0,255,10,20,30,255]),new Uint8ClampedArray([0,0,0,255,0,0,0,255])),10);
console.log('ALL TESTS PASSED', JSON.stringify(s.bands.map(b=>[b.name,Math.round(b.detectedPct)])));

// ---- pitch tests: cello-range tones ----
const SR=48000, N=4096;
const tone=(f,shape='saw',amp=.3)=>{const b=new Float32Array(N);for(let i=0;i<N;i++){const ph=(f*i/SR)%1;b[i]=amp*(shape==='sine'?Math.sin(2*Math.PI*ph):shape==='saw'?2*ph-1:(Math.sin(2*Math.PI*ph)+.5*Math.sin(4*Math.PI*ph)+.33*Math.sin(6*Math.PI*ph)+.25*Math.sin(8*Math.PI*ph))/1.5);}return b;};
for(const [name,f] of [['C2',65.41],['G2',98.0],['D3',146.83],['A3',220.0],['A4',440.0],['E5',659.26]]){
  for(const shape of ['sine','saw','harm']){
    const r=m.yin(tone(f,shape),SR);
    assert(r.freq&&Math.abs(r.freq-f)/f<0.003,`${name} ${shape}: got ${r.freq}`);
  }
}
assert.equal(m.yin(new Float32Array(N),SR).freq,null);                       // silence
let seed=1;const noise=new Float32Array(N).map(()=>{seed=(seed*16807)%2147483647;return(seed/2147483647-.5)*.4;});
assert.equal(m.yin(noise,SR).freq,null);                                      // noise: no pitch
const n1=m.freqToNote(440);assert.equal(n1.name,'A4');assert(Math.abs(n1.cents)<1e-9);
assert.equal(m.freqToNote(65.41).name,'C2');
const sharp=m.freqToNote(440*Math.pow(2,20/1200));assert.equal(sharp.name,'A4');assert(Math.abs(sharp.cents-20)<1e-6);
assert.equal(m.freqToNote(442,442).name,'A4');
console.log('PITCH TESTS PASSED');

// ---- string position tests ----
const A3 = m.stringPositions(220.0);
assert.equal(A3.find(p=>p.string==='A').open, true);                         // open A string
assert(Math.abs(A3.find(p=>p.string==='D').semitones-7)<0.01);                // same pitch = 7 semitones up the D string
assert(Math.abs(A3.find(p=>p.string==='G').semitones-14)<0.01);               // and 14 semitones (a ninth) up the G string
const asharp = m.stringPositions(220*Math.pow(2,1/12)).find(p=>p.string==='A');
assert(Math.abs(asharp.semitones-1)<1e-9 && Math.abs(asharp.fromNut-(1-Math.pow(2,-1/12)))<1e-9);  // ~5.6% of the string
assert.equal(m.stringPositions(110).find(p=>p.string==='A'), undefined);      // below the A string: not on it
assert.deepEqual(m.stringPositions(220,440,'D').map(p=>p.string),['D']);     // string filter
assert(Math.abs(m.stringPositions(442,442)[0].semitones - m.stringPositions(440,440)[0].semitones)<1e-9); // tuning shift
const octaveUp = m.stringPositions(440,440,'A')[0]; assert(Math.abs(octaveUp.fromNut-0.5)<1e-9);       // octave = half the string
console.log('STRING POSITION TESTS PASSED');
// model arm: segment lengths preserved, wrist on the line, elbow below, stroke covers the amplitude
{
  const M = { ...m.MODEL_DEFAULT, amp: 0.6 };
  let minX = 9, maxX = -9;
  for (let k = 0; k <= 100; k++) {
    const a = m.modelArm(M, k / 100);
    assert(Math.abs(Math.hypot(a.elbow.x, a.elbow.y) - M.upper) < 1e-6, 'upper arm length');
    assert(Math.abs(Math.hypot(a.wrist.x - a.elbow.x, a.wrist.y - a.elbow.y) - M.fore) < 1e-6, 'forearm length');
    assert(Math.abs(a.wrist.y - M.drop) < 1e-3, 'wrist height steady');
    assert(a.elbow.y > 0 && a.elbow.y <= a.wrist.y + 1e-6 + 1, 'elbow hangs below shoulder');
    minX = Math.min(minX, a.wrist.x); maxX = Math.max(maxX, a.wrist.x);
  }
  assert(Math.abs((maxX - minX) - 0.6) < 0.01, 'stroke length ' + (maxX - minX));
  assert(m.modelArm(M, 0.25).down && !m.modelArm(M, 0.75).down);
  const far = m.solveArm(0.75, 0.7, 5, 0);   // unreachable target is clamped, lengths still kept
  assert(Math.abs(Math.hypot(far.wrist.x - far.elbow.x, far.wrist.y - far.elbow.y) - 0.7) < 1e-6);
  console.log('model arm OK');
}
// sessions
{
  const r = m.sessionRecord({ at: 1000, seconds: 600.4, level: 'beginner', focus: 'both', arm: 'right', size: '4/4', frames: 200, green: 170, drops: 2, voiced: 50, inTune: 30 });
  assert.equal(r.greenPct, 85); assert.equal(r.tunePct, 60); assert.equal(r.seconds, 600);
  assert.equal(m.sessionRecord({ at: 1, seconds: 10, level: 'x', focus: 'x', frames: 0, green: 0, voiced: 0, inTune: 0 }).greenPct, null);
  const now = Date.now(), day = 86400000;
  const list = [{ ...r, at: now - day }, { ...r, at: now - 2 * day, greenPct: 75, tunePct: null }, { ...r, at: now - 20 * day }];
  const w = m.weekStats(list, now);
  assert.equal(w.sessions, 2); assert.equal(w.minutes, 20); assert.equal(w.greenPct, 80); assert.equal(w.tunePct, 60); assert.equal(w.days, 2);
  assert(m.sessionSummary({ ...r, focus: 'bow' }).includes('Bow arm') && !m.sessionSummary({ ...r, focus: 'bow' }).includes('tune'));
  assert(m.sessionSummary({ ...r, focus: 'tune' }).includes('notes were in tune') && !m.sessionSummary({ ...r, focus: 'tune' }).includes('Bow arm'));
  assert(m.sessionSummary({ ...r, seconds: 5 }).includes('too short'));
  console.log('sessions OK');
}
// left hand signals
{
  const straight = Array.from({ length: 21 }, () => ({ x: 0, y: 0 }));
  for (const f of [[5, 6, 7, 8], [9, 10, 11, 12], [13, 14, 15, 16], [17, 18, 19, 20]]) f.forEach((k, j) => { straight[k] = { x: f[0] * 0.01, y: -j * 0.05 }; });
  assert(Math.abs(m.handCurve(straight) - 1) < 1e-9, 'straight fingers = 1');
  const bent = straight.map(p => ({ ...p })); for (const k of [7, 11, 15, 19]) bent[k] = { x: bent[k].x + 0.05, y: bent[k].y + 0.03 }; for (const k of [8, 12, 16, 20]) bent[k] = { x: bent[k].x + 0.05, y: bent[k].y + 0.1 };
  const cb = m.handCurve(bent); assert(cb < 0.9 && cb > 0.3, 'bent less than 1: ' + cb);
  assert.equal(m.smoothStep(null, 0.9), 0.9); assert.equal(m.smoothStep(0.9, null), 0.9); assert(Math.abs(m.smoothStep(1, 0, 0.25) - 0.75) < 1e-12);
  const pose = Array.from({ length: 33 }, () => ({ x: 0.5, y: 0.5 })); pose[16] = { x: 0.2, y: 0.5 };
  const near = straight.map(p => ({ x: 0.2, y: 0.5 })), far = straight.map(p => ({ x: 0.8, y: 0.5 }));
  assert.equal(m.pickNeckHand([near, far], pose, 'right'), far); assert.equal(m.pickNeckHand([near], pose, 'right'), near); assert.equal(m.pickNeckHand([], pose, 'right'), null);
  console.log('hand signals OK');
}
// pairing codes
{
  const d = { type: 'offer', sdp: 'v=0\r\no=- 1 2 IN IP4 127.0.0.1\r\na=ice-ufrag:ab\r\nm=video 9 UDP/TLS/RTP/SAVPF 96\r\n' };
  const code = m.encodeSignal(d); assert(/^[A-Za-z0-9+/=]+$/.test(code));
  assert.deepEqual(m.decodeSignal(code), d);
  assert.deepEqual(m.decodeSignal(code.replace(/(.{20})/g, '$1\n  ')), d);       // survives line breaks added by chat apps
  assert.throws(() => m.decodeSignal('hello')); assert.throws(() => m.decodeSignal(''));
  assert.throws(() => m.decodeSignal(m.encodeSignal({ type: 'offer', sdp: 'junk' })));
  console.log('pairing codes OK');
}
{
  const sdp = 'v=0\r\n' + Array.from({ length: 120 }, (_, i) => `a=candidate:${i} 1 udp 2113937151 192.168.1.${i} 5000${i} typ host\r\n`).join('');
  const d = { type: 'answer', sdp }; const z = await m.packSignal(d);
  assert(z[0] === 'Z' && z.length < m.encodeSignal(d).length / 2, 'compressed ' + z.length + ' vs ' + m.encodeSignal(d).length);
  assert.deepEqual(await m.unpackSignal(z), d); assert.deepEqual(await m.unpackSignal(z.replace(/(.{30})/g, '$1\n')), d);
  assert.deepEqual(await m.unpackSignal(m.encodeSignal(d)), d);
  await assert.rejects(m.unpackSignal('Zgarbage!!')); await assert.rejects(m.unpackSignal('xyz'));
  console.log('packed codes OK');
}
