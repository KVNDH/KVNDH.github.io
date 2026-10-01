/* 허브 트로피 선반. 시안 tmp/site-motion-2026-09-30/concepts/toon-shelf 를 사이트로 옮긴 것.
 셀 애니메이션 풍 선반에 앱 타일이 박자 맞춰 떨어져 앉고, 고르면 뒤집혀 각인과 스토어 그림 석 장을 펼친다.
 움직임은 Codematic 티켓 기계(TicketMachine.swift 의 Ease.settle, drive, 롤 착지, 되감기)를 따른다.
 - 카메라: 정투영에 사선 밀기(shear)를 얹었다. 앞면은 모양 그대로, 깊이는 오른쪽 위로 물러난다.
 - 그림: 네 단 톤 셰이더, 화면 픽셀 두께가 고정된 먹선 껍질, 한 톤 그림자.
 - 벽과 바닥은 투명하다. 뒤의 DOM 층(bg)에 앱마다 파스텔 번짐을 깔고, 그림자만 반투명으로 얹는다.
 - 호버와 초점: 그 자리 조명이 부드럽게 밝아지고 나머지는 살짝만 가라앉는다(BEAT.spot).
 - 모든 움직임은 drive(길이, f(0...1)) 로 값을 직접 바꾸고, 박자는 BEAT 표 하나에서 나온다(소리도 같은 표). */
import * as THREE from './three-lite.js';

var PI = Math.PI;
var FONT = '-apple-system, BlinkMacSystemFont, "Apple SD Gothic Neo", "Hiragino Sans", "PingFang SC", "PingFang TC", "Malgun Gothic", "Noto Sans KR", "Noto Sans", system-ui, sans-serif';

/* ---------------- 박자 표: 모든 움직임과 소리가 이 표를 본다 ---------------- */
var BEAT = {
  // 착지: Codematic 새 롤 착지(refill 4~5단계)와 같은 박자와 값
  fall: 0.34, fallFrom: 4.4,
  fallS: [0.88, 1.2],                       // 떨어질수록 [가로와 깊이, 세로] (inQuad)
  land: [                                    // 닿는 순간 찌그러졌다 한 번 튀어 선다
    [0.05, [1.16, 0.74], 'outQuad'],
    [0.12, [0.95, 1.08], 'outQuad'],
    [0.13, [1.06, 0.90], 'inQuad'],
    [0.20, [1.00, 1.00], 'settle']
  ],
  hop: [0.05, 0.12, 0.13], hopH: 0.14,       // 기다림, 튀어 오름, 다시 닿음(두 번째 톡), 높이
  plinth: [[0.06, [1.025, 0.955], 'outQuad'], [0.26, [1, 1], 'settle']],   // 받침이 눌렸다 튄다(몸통과 같은 값)
  // 아랫줄은 윗줄 앞을 스치지 않게 자기 줄 바로 위에서 떨어진다. 같은 낙하 속도라 길이는 높이의 제곱근에 비례
  fallLowMin: 0.16,
  // 입장 순서: 직, 지직, 지이이잉(PrintBeat 모양, 끝으로 갈수록 빨라지는 계단), 그리고 천.
  // 앱 수는 데이터에서 온다. 지이이잉 계단은 0.10 에서 0.01 씩 줄고 0.06 아래로는 가지 않는다
  enter: { first: [0.00, 0.42, 0.53], ramp: 0.78, gap0: 0.10, gapStep: 0.01, gapMin: 0.06, cloth: 0.31, clothGap: 0.16 },
  lamp: 0.1,                                 // 조명이 켜질 때 한 번 깜박(켜짐, 반쯤, 켜짐)
  cloth: { fall: 0.44, fallS: [0.86, 1.24], hit: 0.07, hitS: [1.14, 0.8], settle: 0.46 },
  hover: { press: 0.08, pressS: [1.025, 0.95], rise: 0.42, y: 0.2, drop: 0.14,
    land: [[0.05, [1.035, 0.93], 'outQuad'], [0.24, [1, 1], 'settle']] },
  // 시그니처: 움츠림(Codematic 몸통과 같은 값) → 솟아 앞으로 오며 180° → 카드 셋이 계단 박자로
  crouch: 0.13, crouchS: [1.03, 0.93],
  fly: 0.74, veil: 0.36,
  cards: [0.34, 0.50, 0.62], card: 0.5,
  // 되돌리기: 같은 곡선을 거꾸로, 빠르게. 카드는 역순, 계단이 점점 빨라진다
  cardsBack: [0.0, 0.06, 0.1], cardBack: 0.22,
  flyBackAt: 0.1, flyBack: 0.46, ghosts: [0.05, 0.1, 0.15],
  touch: [[0.05, [1.04, 0.9], 'outQuad'], [0.26, [1, 1], 'settle']],
  spin: 0.52,
  // 호버와 초점의 조명: 그 자리는 밝아지고(벽 조명, 등, 따뜻한 빛 한 겹) 나머지는 dim 만큼만 가라앉는다.
  // 계단 없이 dur 동안 outCubic 으로 잇고, 떠날 때와 옮길 때도 같은 곡선. 뒤 번짐도 같은 박자로 진해진다
  spot: { dur: 0.4, reduced: 0.15, ease: 'outCubic', dim: 0.18, lift: 0.07, fanRest: 0.62, blobUp: 1.6, blobDown: 0.85 },
  snapFade: 0.16                             // 동작 줄이기의 교차 페이드
};
// 입장 시각: 타일 n 개, 천 m 개
function enterTimes(n, m) {
  var E = BEAT.enter, out = [], t = E.ramp, gap = E.gap0;
  for (var i = 0; i < n; i++) {
    if (i < E.first.length) { out.push(E.first[i]); continue; }
    out.push(t); t += gap; gap = Math.max(E.gapMin, gap - E.gapStep);
  }
  var last = out.length ? out[out.length - 1] : 0;
  for (var k = 0; k < m; k++) out.push(last + E.cloth + k * E.clothGap);
  return out;
}
var FADE = 0.86;                              // 시그니처 때 선반이 물러나는 정도

/* ---------------- 곡선 ---------------- */
function clamp01(t) { return t < 0 ? 0 : t > 1 ? 1 : t; }
function lerp(a, b, t) { return a + (b - a) * t; }
var Ease = {
  lin: function (t) { return t; },
  outCubic: function (t) { return 1 - Math.pow(1 - t, 3); },
  inCubic: function (t) { return t * t * t; },
  inQuad: function (t) { return t * t; },
  outQuad: function (t) { return 1 - (1 - t) * (1 - t); },
  // 넘쳤다가 한 번 흔들리고 선다(0 → 1, 끝은 정확히 1). 첫 넘침은 18% 쯤. Codematic Ease.settle 과 같다.
  settle: function (t) { return 1 - (1 - t) * Math.exp(-4 * t) * Math.cos(3 * PI * t); }
};

/* ---------------- 색 ---------------- */
var C = {
  ink: '#1A1A1A', verm: '#E63946',
  wallLit: '#FFFFFF', wallShade: '#3C3870', floorTint: '#3C3870',
  shelf: ['#FFFFFF', '#FAF9F6', '#ECE9E3', '#D3CEC5'],     // 흰 칠 나무: 하이라이트, 윗면, 앞면, 옆면
  riserLit: '#F9F7F3',
  plinth: ['#C8AE93', '#9A7D63', '#7C624D', '#5B4739'],   // 칠한 호두나무 받침
  lamp: ['#8A8A92', '#55555C', '#3E3E44', '#2A2A2F'],
  lampOn: '#FFF4D6',
  paper: ['#FFFFFF', '#FFFFFF', '#EEECE8', '#D6D2CB'],
  cloth: ['#FFFDF8', '#F4EFE5', '#DDD4C5', '#B9B1A6'],
  shade: '#ECEBF4',                                         // 그림자: 곱하는 색(한 톤)
  stageShadow: '#BDBBCB',
  fade: '#EFEFF2'
};


/* ---------------- 셰이더 ---------------- */
var TOON_VS = [
  '#include <common>',
  '#include <shadowmap_pars_vertex>',
  'varying vec3 vWN;',
  'varying vec2 vUv;',
  'varying vec3 vWP;',
  'void main() {',
  '#include <beginnormal_vertex>',
  '#include <defaultnormal_vertex>',
  '#include <begin_vertex>',
  '#include <project_vertex>',
  '#include <worldpos_vertex>',
  '#include <shadowmap_vertex>',
  // 카메라는 돌지 않으므로 normalMatrix 가 곧 월드 법선(축마다 다른 크기에도 맞다)
  '  vWN = normalize( transformedNormal );',
  '  vUv = uv;',
  '  vWP = ( modelMatrix * vec4( transformed, 1.0 ) ).xyz;',
  '}'
].join('\n');

var TOON_FS = [
  'uniform vec3 uHi; uniform vec3 uL; uniform vec3 uM; uniform vec3 uD;',
  'uniform vec3 uT; uniform vec3 uDir; uniform vec3 uSunDir; uniform vec3 uShade; uniform float uRecv;',
  'uniform float uFade; uniform vec3 uFadeColor; uniform float uOpacity;',
  'uniform float uGlow; uniform vec3 uGlowColor;',
  // 호버 조명: 화면(사선 투영 평면)의 둥근 상자 안은 밝게, 밖은 살짝 가라앉게
  'uniform vec4 uSpotBox; uniform float uSpotAmt; uniform vec2 uObl; uniform float uSpotDim; uniform float uSpotLift; uniform vec3 uSpotColor;',
  '#ifdef MAPPED',
  'uniform sampler2D uMap;',
  '#endif',
  'varying vec3 vWN;',
  'varying vec2 vUv;',
  'varying vec3 vWP;',
  '#include <common>',
  '#include <bsdfs>',
  '#include <lights_pars_begin>',
  '#include <shadowmap_pars_fragment>',
  'float spotLit() {',
  '  vec2 v = vec2( vWP.x - uObl.x * vWP.z, vWP.y - uObl.y * vWP.z );',
  '  vec2 q = abs( v - uSpotBox.xy ) / uSpotBox.zw;',
  '  float d = pow( pow( q.x, 4.0 ) + pow( q.y, 4.0 ), 0.25 );',
  '  return 1.0 - smoothstep( 1.0, 1.4, d );',
  '}',
  'float sunShadow() {',
  '  float s = 1.0;',
  '  #if defined( USE_SHADOWMAP ) && NUM_DIR_LIGHT_SHADOWS > 0',
  '  DirectionalLightShadow dl = directionalLightShadows[ 0 ];',
  '  s = getShadow( directionalShadowMap[ 0 ], dl.shadowMapSize, dl.shadowIntensity, dl.shadowBias, dl.shadowRadius, vDirectionalShadowCoord[ 0 ] );',
  '  #endif',
  '  return s;',
  '}',
  'void main() {',
  '  vec3 n = normalize( vWN );',
  '  if ( ! gl_FrontFacing ) n = - n;',
  '  float d = dot( n, uDir );',
  '  float w = fwidth( d ) * 0.7 + 1e-4;',
  '#ifdef MAPPED',
  '  vec3 c = texture2D( uMap, vUv ).rgb;',
  '#else',
  // 네 단: 어둠 → 중간 → 밝음 → 모서리 하이라이트. 경계는 한 픽셀 폭으로만 부드럽게(계단 없이 딱 떨어지게)
  '  vec3 c = mix( uD, uM, smoothstep( uT.y - w, uT.y + w, d ) );',
  '  c = mix( c, uL, smoothstep( uT.x - w, uT.x + w, d ) );',
  '  c = mix( c, uHi, smoothstep( uT.z - w, uT.z + w, d ) );',
  '#endif',
  '  c = mix( c, uGlowColor, uGlow );',
  '  float lit = smoothstep( 0.03, 0.12, dot( n, uSunDir ) );',
  '  float sh = ( 1.0 - sunShadow() ) * lit * uRecv;',
  '  c = mix( c, c * uShade, sh );',
  '#ifndef NOSPOT',
  '  float sl = spotLit() * uSpotAmt;',
  '  c = mix( c, uSpotColor, uSpotLift * sl );',
  '  c *= 1.0 - uSpotDim * ( uSpotAmt - sl );',
  '#endif',
  '  c = mix( c, uFadeColor, uFade );',
  '  gl_FragColor = vec4( c, uOpacity );',
  '  #include <colorspace_fragment>',
  '}'
].join('\n');

// 시그니처 무대 뒤의 그림자 받이: 무대 조명(두 번째 그림자 지도)만 읽는다
var CATCH_FS = [
  'uniform vec3 uColor; uniform float uAmt;',
  'varying vec3 vWN;',
  'varying vec2 vUv;',
  '#include <common>',
  '#include <bsdfs>',
  '#include <lights_pars_begin>',
  '#include <shadowmap_pars_fragment>',
  'void main() {',
  '  float s = 1.0;',
  '  #if defined( USE_SHADOWMAP ) && NUM_DIR_LIGHT_SHADOWS > 1',
  '  DirectionalLightShadow dl = directionalLightShadows[ 1 ];',
  '  s = getShadow( directionalShadowMap[ 1 ], dl.shadowMapSize, dl.shadowIntensity, dl.shadowBias, dl.shadowRadius, vDirectionalShadowCoord[ 1 ] );',
  '  #endif',
  '  gl_FragColor = vec4( uColor, ( 1.0 - s ) * uAmt );',
  '  #include <colorspace_fragment>',
  '}'
].join('\n');

// 투명한 벽과 바닥: 해 그림자(첫 그림자 지도)만 반투명 한 톤으로. 바닥은 아주 옅은 바탕 톤을 더한다
// 되감기 잔상: 각인 그림 한 장을 옅게(MeshBasicMaterial 대신 짧은 셰이더로 묶음을 줄인다)
var GHOST_VS = [
  'varying vec2 vUv;',
  'void main() { vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4( position, 1.0 ); }'
].join('\n');
var GHOST_FS = [
  'uniform sampler2D uMap; uniform float uOpacity;',
  'varying vec2 vUv;',
  'void main() {',
  '  gl_FragColor = vec4( texture2D( uMap, vUv ).rgb, uOpacity );',
  '  #include <colorspace_fragment>',
  '}'
].join('\n');

var WALL_FS = [
  'uniform vec3 uColor; uniform float uAmt; uniform float uBase; uniform vec3 uSunDir; uniform float uFade; uniform vec2 uRes; uniform float uEdge;',
  'varying vec3 vWN;',
  'varying vec2 vUv;',
  'varying vec3 vWP;',
  '#include <common>',
  '#include <bsdfs>',
  '#include <lights_pars_begin>',
  '#include <shadowmap_pars_fragment>',
  'void main() {',
  '  float s = 1.0;',
  '  #if defined( USE_SHADOWMAP ) && NUM_DIR_LIGHT_SHADOWS > 0',
  '  DirectionalLightShadow dl = directionalLightShadows[ 0 ];',
  '  s = getShadow( directionalShadowMap[ 0 ], dl.shadowMapSize, dl.shadowIntensity, dl.shadowBias, dl.shadowRadius, vDirectionalShadowCoord[ 0 ] );',
  '  #endif',
  '  float lit = smoothstep( 0.03, 0.12, dot( normalize( vWN ), uSunDir ) );',
  // 캔버스 가장자리(왼쪽, 오른쪽, 아래)에서는 옅어져 뒤 번짐과 이어진다(그림자가 캔버스 끝에서 잘려 보이지 않게)
  '  vec2 p = gl_FragCoord.xy;',
  '  float edge = smoothstep( 0.0, uEdge, p.x ) * smoothstep( 0.0, uEdge, uRes.x - p.x ) * smoothstep( 0.0, uEdge, p.y );',
  '  gl_FragColor = vec4( uColor, ( uBase + ( 1.0 - s ) * lit * uAmt ) * ( 1.0 - uFade ) * edge );',
  '  #include <colorspace_fragment>',
  '}'
].join('\n');

// 먹색 외곽선: 뒤집은 껍질을 화면에서 정확히 uWidth 픽셀만큼 밀어낸다.
// 사선 투영에서도 화면의 바깥 방향은 밀기 전 법선의 xy 와 같다(실루엣에서 dot(N, v) = 0 을 풀면 나온다).
var HULL_VS = [
  'attribute vec3 onormal;',
  'uniform float uWidth; uniform vec2 uRes;',
  'void main() {',
  '  vec4 clip = projectionMatrix * modelViewMatrix * vec4( position, 1.0 );',
  '  vec3 nv = normalMatrix * onormal;',
  '  float l = length( nv.xy );',
  '  vec2 dir = l > 1e-5 ? nv.xy / l : vec2( 0.0 );',
  '  clip.xy += dir * uWidth * 2.0 / uRes * clip.w;',
  '  gl_Position = clip;',
  '}'
].join('\n');
var FLAT_FS = [
  'uniform vec3 uColor; uniform float uFade; uniform vec3 uFadeColor; uniform float uOpacity;',
  'void main() {',
  '  gl_FragColor = vec4( mix( uColor, uFadeColor, uFade ), uOpacity );',
  '  #include <colorspace_fragment>',
  '}'
].join('\n');

// 천 자락 끝(열린 가장자리)의 먹선: 화면 픽셀 두께가 일정한 띠
var LINE_VS = [
  'attribute vec3 aPrev; attribute vec3 aNext; attribute float aSide;',
  'uniform vec2 uRes; uniform float uWidth;',
  'vec2 scr( vec4 c ) { return c.xy / c.w * uRes * 0.5; }',
  'void main() {',
  '  mat4 m = projectionMatrix * modelViewMatrix;',
  '  vec4 c = m * vec4( position, 1.0 );',
  '  vec2 s0 = scr( m * vec4( aPrev, 1.0 ) ), s1 = scr( c ), s2 = scr( m * vec4( aNext, 1.0 ) );',
  '  vec2 d1 = s1 - s0, d2 = s2 - s1;',
  '  if ( length( d1 ) < 1e-3 ) d1 = d2;',
  '  if ( length( d2 ) < 1e-3 ) d2 = d1;',
  '  d1 = normalize( d1 + vec2( 1e-6 ) ); d2 = normalize( d2 + vec2( 1e-6 ) );',
  '  vec2 t = normalize( d1 + d2 + vec2( 1e-6 ) );',
  '  vec2 nr = vec2( - t.y, t.x );',
  '  float k = 1.0 / max( 0.4, dot( nr, vec2( - d1.y, d1.x ) ) );',
  '  c.xy += nr * uWidth * 0.5 * k * aSide / ( uRes * 0.5 ) * c.w;',
  '  c.z -= 0.0006 * c.w;',
  '  gl_Position = c;',
  '}'
].join('\n');

/* ---------------- 모양 ---------------- */
// iOS 아이콘 모양: 초타원 n=5. 45° 지점이 반경 22.4% 둥근 사각과 0.2% 안으로 겹치고 곡률이 이어진다.
function squirclePts(w, h, seg) {
  var pts = [], n = 5;
  for (var i = 0; i < seg; i++) {
    var t = i / seg * PI * 2, c = Math.cos(t), s = Math.sin(t);
    pts.push(new THREE.Vector2(Math.sign(c) * Math.pow(Math.abs(c), 2 / n) * w / 2, Math.sign(s) * Math.pow(Math.abs(s), 2 / n) * h / 2));
  }
  return pts;
}
function roundRectShape(w, h, r) {
  var s = new THREE.Shape(), x = -w / 2, y = -h / 2;
  r = Math.min(r, w / 2, h / 2);
  s.moveTo(x + r, y);
  s.lineTo(x + w - r, y); s.absarc(x + w - r, y + r, r, -PI / 2, 0, false);
  s.lineTo(x + w, y + h - r); s.absarc(x + w - r, y + h - r, r, 0, PI / 2, false);
  s.lineTo(x + r, y + h); s.absarc(x + r, y + h - r, r, PI / 2, PI, false);
  s.lineTo(x, y + r); s.absarc(x + r, y + r, r, PI, PI * 1.5, false);
  return s;
}
// 앞뒤 뚜껑 UV 를 모양 상자에 맞춘다
function capUV(minX, minY, w, h) {
  return {
    generateTopUV: function (g, v, a, b, c) {
      return [a, b, c].map(function (i) { return new THREE.Vector2((v[i * 3] - minX) / w, (v[i * 3 + 1] - minY) / h); });
    },
    generateSideWallUV: function () { return [new THREE.Vector2(), new THREE.Vector2(), new THREE.Vector2(), new THREE.Vector2()]; }
  };
}
// ExtrudeGeometry 의 뚜껑을 앞(0), 옆(1), 뒤(2) 세 무리로 다시 묶는다. 뒤 뚜껑은 180° 돌려 봤을 때 바로 읽히게 u 를 뒤집는다.
function splitCaps(g) {
  var P = g.attributes.position.array, U = g.attributes.uv.array;
  var g0 = g.groups[0], g1 = g.groups[1];
  var zmin = Infinity, zmax = -Infinity, i;
  for (i = 0; i < P.length; i += 3) { zmin = Math.min(zmin, P[i + 2]); zmax = Math.max(zmax, P[i + 2]); }
  var mid = (zmin + zmax) / 2, front = [], back = [], side = [];
  for (i = g0.start; i < g0.start + g0.count; i += 3) {
    var z = (P[i * 3 + 2] + P[i * 3 + 5] + P[i * 3 + 8]) / 3;
    (z > mid ? front : back).push(i);
  }
  for (i = g1.start; i < g1.start + g1.count; i += 3) side.push(i);
  var order = front.concat(side, back), n = order.length * 3;
  var pos = new Float32Array(n * 3), uv = new Float32Array(n * 2);
  order.forEach(function (t, k) {
    for (var j = 0; j < 3; j++) {
      var s = t + j, d = k * 3 + j;
      pos[d * 3] = P[s * 3]; pos[d * 3 + 1] = P[s * 3 + 1]; pos[d * 3 + 2] = P[s * 3 + 2];
      var u = U[s * 2];
      uv[d * 2] = k >= front.length + side.length ? 1 - u : u; uv[d * 2 + 1] = U[s * 2 + 1];
    }
  });
  var out = new THREE.BufferGeometry();
  out.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  out.setAttribute('uv', new THREE.BufferAttribute(uv, 2));
  out.addGroup(0, front.length * 3, 0);
  out.addGroup(front.length * 3, side.length * 3, 1);
  out.addGroup((front.length + side.length) * 3, back.length * 3, 2);
  out.computeVertexNormals();
  smoothSides(out, front.length * 3, side.length * 3);
  addOutlineNormals(out);
  g.dispose();
  return out;
}
function posKey(P, i) { return Math.round(P[i * 3] * 2e3) + ',' + Math.round(P[i * 3 + 1] * 2e3) + ',' + Math.round(P[i * 3 + 2] * 2e3); }
function faceNormals(P, start, count, cb) {
  var a = new THREE.Vector3(), b = new THREE.Vector3(), c = new THREE.Vector3(), ab = new THREE.Vector3(), ac = new THREE.Vector3();
  for (var i = start; i < start + count; i += 3) {
    a.fromArray(P, i * 3); b.fromArray(P, i * 3 + 3); c.fromArray(P, i * 3 + 6);
    ab.subVectors(b, a); ac.subVectors(c, a); ab.cross(ac);
    cb(i, ab);
  }
}
// 옆면(베벨 포함) 법선만 매끈하게: 톤 경계가 둥근 모서리를 따라 깔끔한 띠로 흐른다
function smoothSides(g, start, count) {
  var P = g.attributes.position.array, N = g.attributes.normal.array, acc = {};
  faceNormals(P, start, count, function (i, n) {
    for (var j = 0; j < 3; j++) { var k = posKey(P, i + j), v = acc[k] || (acc[k] = [0, 0, 0]); v[0] += n.x; v[1] += n.y; v[2] += n.z; }
  });
  for (var i = start; i < start + count; i++) {
    var v = acc[posKey(P, i)], l = Math.hypot(v[0], v[1], v[2]) || 1;
    N[i * 3] = v[0] / l; N[i * 3 + 1] = v[1] / l; N[i * 3 + 2] = v[2] / l;
  }
}
// 외곽선용 법선: 같은 자리의 모든 면을 평균(껍질이 모서리에서 갈라지지 않게)
function addOutlineNormals(g) {
  var P = g.attributes.position.array, n = P.length / 3, acc = {}, O = new Float32Array(n * 3), idx = g.index;
  if (idx) {
    // 색인 도형(원기둥 등): 면을 풀어서 모은다
    var I = idx.array, a = new THREE.Vector3(), b = new THREE.Vector3(), c = new THREE.Vector3();
    for (var t = 0; t < I.length; t += 3) {
      a.fromArray(P, I[t] * 3); b.fromArray(P, I[t + 1] * 3); c.fromArray(P, I[t + 2] * 3);
      var fn = new THREE.Vector3().subVectors(b, a).cross(new THREE.Vector3().subVectors(c, a));
      for (var j = 0; j < 3; j++) { var k = posKey(P, I[t + j]), v = acc[k] || (acc[k] = [0, 0, 0]); v[0] += fn.x; v[1] += fn.y; v[2] += fn.z; }
    }
  } else {
    faceNormals(P, 0, n, function (i, fn) {
      for (var j = 0; j < 3; j++) { var k = posKey(P, i + j), v = acc[k] || (acc[k] = [0, 0, 0]); v[0] += fn.x; v[1] += fn.y; v[2] += fn.z; }
    });
  }
  for (var i = 0; i < n; i++) {
    var v = acc[posKey(P, i)] || [0, 1, 0], l = Math.hypot(v[0], v[1], v[2]) || 1;
    O[i * 3] = v[0] / l; O[i * 3 + 1] = v[1] / l; O[i * 3 + 2] = v[2] / l;
  }
  g.setAttribute('onormal', new THREE.BufferAttribute(O, 3));
  return g;
}
// 모서리가 둥근 상자: 바닥이 y=0, x, z 가운데
function roundedBox(w, h, d, r) {
  var shape = roundRectShape(w - 2 * r, d - 2 * r, r * 0.8);
  var g = new THREE.ExtrudeGeometry(shape, { depth: Math.max(0.001, h - 2 * r), bevelEnabled: true, bevelThickness: r, bevelSize: r, bevelSegments: 3, curveSegments: 5, steps: 1 });
  g.rotateX(-PI / 2);
  g.translate(0, r, 0);
  g.computeVertexNormals();
  var n = g.attributes.position.count;
  smoothSides(g, 0, n);
  // 윗면과 아랫면은 평평하게(부드럽게 만든 법선 가운데 수직에 가까운 것은 그대로 수직으로)
  var N = g.attributes.normal.array;
  for (var i = 0; i < n; i++) if (Math.abs(N[i * 3 + 1]) > 0.995) { N[i * 3] = 0; N[i * 3 + 1] = Math.sign(N[i * 3 + 1]); N[i * 3 + 2] = 0; }
  g.clearGroups();
  addOutlineNormals(g);
  return g;
}

/* ---------------- 천: 절차적 드레이프(물리 대신 진행값으로 모양을 정한다) ---------------- */
function makeClothGeo(NX, NZ) {
  var n = (NX + 1) * (NZ + 1), g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(new Float32Array(n * 3), 3));
  g.setAttribute('uv', new THREE.BufferAttribute(new Float32Array(n * 2), 2));
  var idx = [];
  for (var j = 0; j < NZ; j++) for (var i = 0; i < NX; i++) {
    var a = j * (NX + 1) + i, b = a + 1, c = a + NX + 1, d = c + 1;
    idx.push(a, c, b, b, c, d);
  }
  g.setIndex(idx);
  // 자락 끝(가장자리) 순서
  var hem = [], i2;
  for (i2 = 0; i2 < NX; i2++) hem.push(i2);
  for (i2 = 0; i2 < NZ; i2++) hem.push(i2 * (NX + 1) + NX);
  for (i2 = NX; i2 > 0; i2--) hem.push(NZ * (NX + 1) + i2);
  for (i2 = NZ; i2 > 0; i2--) hem.push(i2 * (NX + 1));
  return { geo: g, NX: NX, NZ: NZ, hem: hem };
}
// p: { A, B (덮인 물건 반폭, 반깊이), H (높이), rc (모서리), lift, flare, fold, room (앞뒤로 퍼질 수 있는 한계) }
function drapeCloth(cl, p) {
  var P = cl.geo.attributes.position.array, NX = cl.NX, NZ = cl.NZ;
  var rho = 0.13, arc = rho * PI / 2, H = p.H + p.lift, drop = H - rho;
  var Sx = p.A + arc + p.H + 0.05, Sz = p.B + arc + p.H;
  for (var j = 0; j <= NZ; j++) for (var i = 0; i <= NX; i++) {
    var u = -1 + 2 * i / NX, v = -1 + 2 * j / NZ;
    var g = 1 - 0.26 * u * u * v * v;                // 네 귀를 조금 당겨 끝이 너무 멀리 고이지 않게
    var px = u * Sx * g, pz = v * Sz * g;
    var qx = Math.abs(px) - (p.A - p.rc), qz = Math.abs(pz) - (p.B - p.rc);
    var ox = Math.max(qx, 0), oz = Math.max(qz, 0), out = Math.hypot(ox, oz);
    var dd = out + Math.min(Math.max(qx, qz), 0) - p.rc;
    var X, Y, Z, k = (j * (NX + 1) + i) * 3;
    if (dd <= 0) {
      var r2 = (px * px) / (p.A * p.A) + (pz * pz) / (p.B * p.B);
      X = px; Z = pz; Y = H + 0.035 * (1 - Math.min(1, r2));
    } else {
      var nx, nz;
      if (qx > 0 && qz > 0) { nx = ox * Math.sign(px) / out; nz = oz * Math.sign(pz) / out; }
      else if (qx > qz) { nx = Math.sign(px); nz = 0; }
      else { nx = 0; nz = Math.sign(pz); }
      var fx = px - nx * dd, fz = pz - nz * dd;
      var th = Math.atan2(fz / p.B, fx / p.A);
      // 주름: 삼각 물결이라 면이 좌우로 꺾여 셀 톤이 또렷한 띠로 끊긴다. 자리마다 깊이를 조금씩 달리한다.
      var wave = Math.asin(Math.sin(th * 7 + 0.9)) * 2 / PI * (0.72 + 0.28 * Math.sin(th * 3 + 1.7));
      var h, y;
      if (dd < arc) { var ph = dd / rho; h = rho * Math.sin(ph); y = H - rho * (1 - Math.cos(ph)); }
      else {
        var s = dd - arc;
        if (s < drop) {
          var t = s / drop;
          h = rho + (0.075 + p.flare * 0.2) * t * t + p.fold * t * wave;
          y = H - rho - s;
        } else {
          var e = s - drop;
          h = rho + 0.075 + p.flare * 0.2 + p.fold * wave + e * 0.5;
          y = 0.004 + 0.012 * Math.max(0, wave) * Math.min(1, e * 6);
        }
      }
      X = fx + nx * h; Z = fz + nz * h; Y = y;
      // 선반 끝을 넘어가면 넘어간 만큼 아래로 늘어진다
      if (Z > p.room) { Y -= (Z - p.room); Z = p.room + 0.004; }
    }
    P[k] = X; P[k + 1] = Y; P[k + 2] = Z;
  }
  cl.geo.attributes.position.needsUpdate = true;
  cl.geo.computeVertexNormals();
  cl.geo.attributes.normal.needsUpdate = true;
}

/* ---------------- mount ----------------
   root: 선반이 들어갈 자리, DATA: render.py 가 허브에 넣은 JSON({ lang, ui, apps }), bgEl: 번짐을 깔 DOM 층.
   WebGL 을 못 만들면 null 을 돌려준다(부르는 쪽이 벤토를 그대로 둔다). */
export function mount(root, DATA, bgEl) {
  var dead = false;
  var reduced = !!(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches);
  var apps = DATA.apps, UI = DATA.ui;
  var trash = [], offs = [], timers = new Set();
  function keep(x) { trash.push(x); return x; }
  function on(el, type, fn, opt) { el.addEventListener(type, fn, opt); offs.push(function () { el.removeEventListener(type, fn, opt); }); }
  function later(fn, ms) { var id = setTimeout(function () { timers.delete(id); if (!dead) fn(); }, ms); timers.add(id); return id; }
  function cancelLater(id) { clearTimeout(id); timers.delete(id); }
  function wait(s) { return new Promise(function (r) { later(r, s * 1000); }); }

  /* ----- DOM ----- */
  root.innerHTML = '';
  var wrap = document.createElement('div');
  wrap.className = 'c-toon-shelf' + (reduced ? ' is-reduced' : '');
  wrap.innerHTML =
    '<canvas class="c-toon-shelf__gl" aria-hidden="true"></canvas>' +
    '<canvas class="c-toon-shelf__snap" aria-hidden="true"></canvas>' +
    '<div class="c-toon-shelf__hits" role="group"></div>' +
    '<div class="c-toon-shelf__stage">' +
      '<button type="button" class="c-toon-shelf__back" tabindex="-1" aria-hidden="true"></button>' +
      '<div class="c-toon-shelf__spin" aria-hidden="true"></div>' +
      '<a class="c-toon-shelf__more" href="#" tabindex="-1"><span></span><span class="c-toon-shelf__arrow" aria-hidden="true"></span></a>' +
      '<button type="button" class="c-toon-shelf__close" tabindex="-1"></button>' +
    '</div>' +
    '<button type="button" class="c-toon-shelf__sound" aria-pressed="false"><span class="c-toon-shelf__led" aria-hidden="true"></span><span></span></button>' +
    '<p class="c-toon-shelf__sr" aria-live="polite"></p>';
  root.appendChild(wrap);
  var canvas = wrap.querySelector('.c-toon-shelf__gl');
  var snapEl = wrap.querySelector('.c-toon-shelf__snap');
  var hitsEl = wrap.querySelector('.c-toon-shelf__hits');
  var stageEl = wrap.querySelector('.c-toon-shelf__stage');
  var backEl = wrap.querySelector('.c-toon-shelf__back');
  var spinEl = wrap.querySelector('.c-toon-shelf__spin');
  var moreEl = wrap.querySelector('.c-toon-shelf__more');
  var closeEl = wrap.querySelector('.c-toon-shelf__close');
  var soundEl = wrap.querySelector('.c-toon-shelf__sound');
  var liveEl = wrap.querySelector('.c-toon-shelf__sr');
  // 문구는 모두 언어별 JSON 에서 온다
  hitsEl.setAttribute('aria-label', UI.shelf);
  moreEl.firstChild.textContent = UI.more;
  closeEl.setAttribute('aria-label', UI.back);
  soundEl.lastChild.textContent = UI.sound;

  var renderer;
  try {
    renderer = new THREE.WebGLRenderer({ canvas: canvas, antialias: true, alpha: true, powerPreference: 'high-performance' });
  } catch (e) { renderer = null; }
  if (!renderer) { root.innerHTML = ''; return null; }

  var DPR = Math.min(window.devicePixelRatio || 1, 2);
  renderer.setPixelRatio(DPR);
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFShadowMap;
  renderer.setClearColor(0x000000, 0);   // 벽은 투명. 뒤 DOM 번짐이 보인다

  var scene = new THREE.Scene();
  var camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0.1, 120);
  camera.position.set(0, 0, 50);
  var OBL = { kx: 0.41, ky: 0.287 };
  var shearM = new THREE.Matrix4();
  function applyProjection() {
    camera.updateProjectionMatrix();
    var zc = camera.position.z;
    shearM.set(1, 0, -OBL.kx, -OBL.kx * zc, 0, 1, -OBL.ky, -OBL.ky * zc, 0, 0, 1, 0, 0, 0, 0, 1);
    camera.projectionMatrix.multiply(shearM);
    camera.projectionMatrixInverse.copy(camera.projectionMatrix).invert();
  }

  // 톤 빛(면의 톤을 정한다)과 그림자 빛은 따로 둔다(그림 쪽 편의). 무대 빛은 시그니처 그림자만 맡는다.
  var LT = new THREE.Vector3(-0.42, 0.78, 0.47).normalize();
  var LS = new THREE.Vector3(-0.34, 0.74, 0.58).normalize();
  var LSTAGE = new THREE.Vector3(-0.075, 0.105, 1).normalize();
  var SMAP = Math.min(window.innerWidth || 1280, window.innerHeight || 800) < 700 ? 1024 : 2048;
  var sun = new THREE.DirectionalLight(0xffffff, 1);
  sun.castShadow = true;
  sun.shadow.mapSize.set(SMAP, SMAP);
  sun.shadow.bias = -0.0005; sun.shadow.normalBias = 0.012; sun.shadow.radius = 1;
  scene.add(sun); scene.add(sun.target);
  var stageLight = new THREE.DirectionalLight(0xffffff, 1);
  stageLight.castShadow = true;
  stageLight.shadow.mapSize.set(SMAP, SMAP);
  stageLight.shadow.bias = -0.0008; stageLight.shadow.normalBias = 0.01; stageLight.shadow.radius = 1;
  stageLight.shadow.autoUpdate = false;
  scene.add(stageLight); scene.add(stageLight.target);

  var shared = {
    fade: { value: 0 }, fadeColor: { value: new THREE.Color(C.fade) },
    dir: { value: LT.clone() }, sunDir: { value: LS.clone() },
    shade: { value: new THREE.Color(C.shade) },
    inkW: { value: 2 }, res: { value: new THREE.Vector2(1, 1) }, edge: { value: 64 },
    // 호버 조명: 상자(화면 평면의 가운데와 반폭), 세기, 사선 계수
    spotBox: { value: new THREE.Vector4(0, 0, 1, 1) }, spotAmt: { value: 0 }, obl: { value: new THREE.Vector2(0.41, 0.287) },
    spotDim: { value: BEAT.spot.dim }, spotLift: { value: BEAT.spot.lift }, spotColor: { value: new THREE.Color(C.lampOn) }
  };
  var WHITE = new THREE.Color('#FFFFFF');

  function col(hex) { return new THREE.Color(hex); }
  function toon(o) {
    var u = THREE.UniformsUtils.merge([THREE.UniformsLib.lights, {
      uHi: { value: new THREE.Color() }, uL: { value: new THREE.Color() }, uM: { value: new THREE.Color() }, uD: { value: new THREE.Color() },
      uT: { value: new THREE.Vector3(0.62, 0.1, 0.87) },
      uRecv: { value: o.recv == null ? 1 : o.recv },
      uOpacity: { value: o.opacity == null ? 1 : o.opacity },
      uGlow: { value: 0 }, uGlowColor: { value: col(o.glow || '#FFFFFF') }
    }]);
    u.uFade = o.fade || shared.fade; u.uFadeColor = shared.fadeColor;
    u.uDir = shared.dir; u.uSunDir = shared.sunDir; u.uShade = shared.shade;
    u.uSpotBox = shared.spotBox; u.uSpotAmt = shared.spotAmt; u.uObl = shared.obl;
    u.uSpotDim = shared.spotDim; u.uSpotLift = shared.spotLift; u.uSpotColor = shared.spotColor;
    if (o.map) u.uMap = { value: o.map };
    if (o.recvU) u.uRecv = o.recvU;
    var fl = o.flat || '#FFFFFF', t = o.tones || [fl, fl, fl, fl];
    u.uHi.value.copy(t[0].isColor ? t[0] : col(t[0])); u.uL.value.copy(t[1].isColor ? t[1] : col(t[1]));
    u.uM.value.copy(t[2].isColor ? t[2] : col(t[2])); u.uD.value.copy(t[3].isColor ? t[3] : col(t[3]));
    var m = new THREE.ShaderMaterial({
      uniforms: u, vertexShader: TOON_VS, fragmentShader: TOON_FS, lights: true,
      defines: Object.assign(o.map ? { MAPPED: '' } : {}, o.nospot ? { NOSPOT: '' } : {}),
      side: o.side || THREE.FrontSide, transparent: !!o.transparent, depthWrite: o.depthWrite !== false
    });
    if (o.polygonOffset) { m.polygonOffset = true; m.polygonOffsetFactor = -1; m.polygonOffsetUnits = o.polygonOffset; }
    return keep(m);
  }
  // 투명한 벽과 바닥: 그림자와 아주 옅은 바탕 톤만 그린다
  function shadowMat(hex, base, amt) {
    var u = THREE.UniformsUtils.merge([THREE.UniformsLib.lights, { uColor: { value: col(hex) }, uAmt: { value: amt }, uBase: { value: base } }]);
    u.uSunDir = shared.sunDir; u.uFade = shared.fade; u.uRes = shared.res; u.uEdge = shared.edge;
    return keep(new THREE.ShaderMaterial({ uniforms: u, vertexShader: TOON_VS, fragmentShader: WALL_FS, lights: true, transparent: true, depthWrite: false }));
  }
  function hullMat(fadeU, opacityU) {
    return keep(new THREE.ShaderMaterial({
      uniforms: { uColor: { value: col(C.ink) }, uFade: fadeU || shared.fade, uFadeColor: shared.fadeColor, uOpacity: opacityU || { value: 1 }, uWidth: shared.inkW, uRes: shared.res },
      vertexShader: HULL_VS, fragmentShader: FLAT_FS, side: THREE.BackSide
    }));
  }
  function lineMat(fadeU) {
    return keep(new THREE.ShaderMaterial({
      uniforms: { uColor: { value: col(C.ink) }, uFade: fadeU || shared.fade, uFadeColor: shared.fadeColor, uOpacity: { value: 1 }, uWidth: shared.inkW, uRes: shared.res },
      vertexShader: LINE_VS, fragmentShader: FLAT_FS, side: THREE.DoubleSide
    }));
  }
  function mesh(geo, mat, cast, recv) {
    var m = new THREE.Mesh(geo, mat);
    m.castShadow = !!cast; m.receiveShadow = recv !== false; m.frustumCulled = false;
    return m;
  }
  function withHull(geo, mat, hmat, cast) {
    var g = new THREE.Group();
    var body = mesh(geo, mat, cast);
    var hull = mesh(geo, hmat, false, false);
    g.add(hull); g.add(body);
    g.userData.body = body; g.userData.hull = hull;
    return g;
  }

  /* ----- 색 도우미(sRGB 공간에서 톤을 만든다) ----- */
  function srgb(c) { var o = {}; c.getRGB(o, THREE.SRGBColorSpace); return o; }
  function fromSrgb(r, g, b) { return new THREE.Color().setRGB(r, g, b, THREE.SRGBColorSpace); }
  function shadeOf(base, k, tint, tk) {
    var a = srgb(base), t = srgb(col(tint));
    return fromSrgb(lerp(a.r * k, t.r, tk), lerp(a.g * k, t.g, tk), lerp(a.b * k, t.b, tk));
  }
  function tonesOf(base) {
    return [base.clone().lerp(WHITE, 0.7), base.clone(), shadeOf(base, 0.87, '#8C88A6', 0.07), shadeOf(base, 0.7, '#5F5A7C', 0.13)];
  }
  function hexOf(c) { return '#' + c.getHexString(THREE.SRGBColorSpace); }
  function relLum(hex) {
    var c = srgb(col(hex));
    function ch(v) { return v <= 0.04045 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); }
    return 0.2126 * ch(c.r) + 0.7152 * ch(c.g) + 0.0722 * ch(c.b);
  }
  function contrast(a, b) { var la = relLum(a), lb = relLum(b); return (Math.max(la, lb) + 0.05) / (Math.min(la, lb) + 0.05); }
  function enoughContrast(fg, bg, lighter) {
    var c = col(fg), to = lighter ? WHITE : new THREE.Color(0, 0, 0);
    for (var k = 0; k < 20 && contrast(hexOf(c), bg) < 4.5; k++) c.lerp(to, 0.15);
    return hexOf(c);
  }

  /* ----- 공유 도형 ----- */
  var TILE_W = 1, TILE_H = 1.08, TILE_D = 0.17, PL = { w: 1.16, h: 0.12, d: 0.6 };
  var tileShape = new THREE.Shape(squirclePts(1, 1, 128));
  var tileGeo = keep(splitCaps(new THREE.ExtrudeGeometry(tileShape, {
    depth: 0.08, bevelEnabled: true, bevelThickness: 0.045, bevelSize: 0.04, bevelSegments: 5, steps: 1,
    UVGenerator: capUV(-0.5, -0.5, 1, 1)
  })));
  tileGeo.translate(0, 0.54, -0.04);
  var ghostGeo = keep(new THREE.ShapeGeometry(new THREE.Shape(squirclePts(1.08, 1.08, 96))));
  (function () {
    // 뒷면 각인과 같은 UV(좌우 뒤집음): 뒤로 돌아 있는 동안 글자가 바로 읽힌다
    var P = ghostGeo.attributes.position.array, U = ghostGeo.attributes.uv.array;
    for (var i = 0; i < U.length / 2; i++) { U[i * 2] = 1 - (P[i * 3] / 1.08 + 0.5); U[i * 2 + 1] = P[i * 3 + 1] / 1.08 + 0.5; }
  })();
  ghostGeo.translate(0, 0.54, 0);
  var plinthGeo = keep(roundedBox(PL.w, PL.h, PL.d, 0.026));
  var CARD_AR = 480 / 1043, CARD_H = 1 / CARD_AR;
  var cardShape = roundRectShape(1, CARD_H, 0.085);
  var cardGeo = keep(splitCaps(new THREE.ExtrudeGeometry(cardShape, {
    depth: 0.012, bevelEnabled: true, bevelThickness: 0.006, bevelSize: 0.006, bevelSegments: 2, curveSegments: 8, steps: 1,
    UVGenerator: capUV(-0.5, -CARD_H / 2, 1, CARD_H)
  })));
  cardGeo.translate(0, 0, -0.012);

  /* ----- 공유 재질 ----- */
  var M = {
    plinth: toon({ tones: C.plinth }),
    lamp: toon({ tones: C.lamp }),
    shelf: toon({ tones: C.shelf }),
    paper: toon({ tones: C.paper }),
    wall: shadowMat(C.wallShade, 0, 0.1),
    floor: shadowMat(C.floorTint, 0, 0.1),
    cloth: toon({ tones: C.cloth, side: THREE.DoubleSide }),
    hull: hullMat(),
    line: lineMat()
  };

  /* ----- 그림(아이콘, 테 색) ----- */
  var images = [];
  function loadImage(src) {
    var im = new Image();
    im.decoding = 'async';
    im.src = src;
    return (im.decode ? im.decode() : new Promise(function (r) { im.onload = r; })).then(function () { return im; }, function () { return im; });
  }
  function texFrom(src, cb) {
    var tex = keep(new THREE.Texture());
    tex.colorSpace = THREE.SRGBColorSpace;
    tex.anisotropy = Math.min(8, renderer.capabilities.getMaxAnisotropy());
    tex.minFilter = THREE.LinearMipmapLinearFilter;
    var p = loadImage(src).then(function (im) { if (dead) return; tex.image = im; tex.needsUpdate = true; if (cb) cb(im); requestRender(); });
    tex.userData.ready = p;
    return tex;
  }
  // 아이콘 네 변 가운데 띠의 평균 색 = 타일 테 색(아이콘을 그대로 두툼하게 뽑아낸 것처럼)
  function edgeColor(im) {
    var c = document.createElement('canvas'); c.width = c.height = 40;
    var x = c.getContext('2d', { willReadFrequently: true });
    x.drawImage(im, 0, 0, 40, 40);
    var d = x.getImageData(0, 0, 40, 40).data, r = 0, g = 0, b = 0, n = 0;
    function add(px, py) { var i = (py * 40 + px) * 4; r += d[i]; g += d[i + 1]; b += d[i + 2]; n++; }
    for (var k = 12; k < 28; k++) { add(k, 1); add(k, 38); add(1, k); add(38, k); add(k, 2); add(k, 37); add(2, k); add(37, k); }
    return fromSrgb(r / n / 255, g / n / 255, b / n / 255);
  }

  /* ----- 소리(WebAudio 합성, 기본 꺼짐) ----- */
  var AC = null, soundOn = false, noiseBuf = null, master = null;
  function audioInit() {
    var Ctor = window.AudioContext || window.webkitAudioContext;
    if (!Ctor) return false;
    AC = new Ctor();
    master = AC.createGain(); master.gain.value = 0.8; master.connect(AC.destination);
    noiseBuf = AC.createBuffer(1, AC.sampleRate * 0.5, AC.sampleRate);
    var ch = noiseBuf.getChannelData(0);
    for (var i = 0; i < ch.length; i++) ch[i] = Math.random() * 2 - 1;
    return true;
  }
  function env(g, t, a, peak, dcy) { g.gain.setValueAtTime(0.0001, t); g.gain.linearRampToValueAtTime(peak, t + a); g.gain.exponentialRampToValueAtTime(0.0001, t + a + dcy); }
  function tone(t, f0, f1, dur, peak, type) {
    var o = AC.createOscillator(), g = AC.createGain();
    o.type = type || 'sine'; o.frequency.setValueAtTime(f0, t); o.frequency.exponentialRampToValueAtTime(f1, t + dur);
    env(g, t, 0.004, peak, dur); o.connect(g); g.connect(master); o.start(t); o.stop(t + dur + 0.05);
  }
  function noise(t, dur, peak, type, f0, f1, q) {
    var s = AC.createBufferSource(), f = AC.createBiquadFilter(), g = AC.createGain();
    s.buffer = noiseBuf; f.type = type; f.Q.value = q || 0.8;
    f.frequency.setValueAtTime(f0, t); f.frequency.exponentialRampToValueAtTime(f1 || f0, t + dur);
    env(g, t, Math.min(0.02, dur * 0.3), peak, dur); s.connect(f); f.connect(g); g.connect(master); s.start(t); s.stop(t + dur + 0.05);
  }
  function sfx(name, k) {
    if (!soundOn || !AC || dead) return;
    var t = AC.currentTime + 0.005;
    if (name === 'thud') { tone(t, 190, 62, 0.13, 0.26); noise(t, 0.035, 0.07, 'lowpass', 1400); }
    else if (name === 'tick') { tone(t, 150, 90, 0.07, 0.1); }
    else if (name === 'lamp') { tone(t, 2600, 2300, 0.014, 0.05, 'square'); tone(t + 0.035, 2600, 2300, 0.01, 0.025, 'square'); }
    else if (name === 'soft') { noise(t, 0.14, 0.09, 'bandpass', 900, 380, 0.7); tone(t, 120, 70, 0.1, 0.06); }
    else if (name === 'tap') { tone(t, 240, 120, 0.05, 0.07); }
    else if (name === 'crouch') { noise(t, 0.12, 0.035, 'lowpass', 500, 260); }
    else if (name === 'whoosh') { noise(t, 0.34, 0.07, 'bandpass', 380, 2600, 1.1); }
    else if (name === 'card') { tone(t, 1250 + (k || 0) * 180, 1900 + (k || 0) * 200, 0.045, 0.06, 'triangle'); noise(t, 0.02, 0.03, 'highpass', 3000); }
    else if (name === 'rewind') {
      noise(t, 0.5, 0.05, 'bandpass', 2400, 320, 1.2);
      for (var i = 0; i < 7; i++) tone(t + 0.5 * Math.sqrt((i + 1) / 8), 2200, 1900, 0.012, 0.03, 'square');
    }
    else if (name === 'on') { tone(t, 1800, 1700, 0.02, 0.05, 'square'); }
  }

  /* ----- 움직임 엔진: drive(길이, f(0...1)) ----- */
  var motions = [], raf = 0, dirty = true, visible = !document.hidden, inView = true;
  function now() { return performance.now() / 1000; }
  function drive(dur, fn, opt) {
    opt = opt || {};
    return new Promise(function (resolve) {
      if (dead) return;
      var m = { t0: now() + (opt.delay || 0), dur: Math.max(0.0001, dur), fn: fn, resolve: resolve, key: opt.key, onStart: opt.onStart, started: false, done: false };
      if (m.key) stopKey(m.key);
      motions.push(m);
      // 기다림 제한: 길이 + 0.5초. 렌더가 멈춰도 끝 상태로 놓는다.
      m.guard = later(function () { finish(m, true); }, ((opt.delay || 0) + dur + 0.5) * 1000);
      kick();
    });
  }
  function finish(m, apply) {
    if (m.done) return;
    m.done = true;
    if (apply) { if (!m.started && m.onStart) m.onStart(); m.fn(1); }
    var k = motions.indexOf(m); if (k >= 0) motions.splice(k, 1);
    cancelLater(m.guard);
    m.resolve();
    dirty = true; kick();
  }
  function stopKey(key) { motions.slice().forEach(function (m) { if (m.key === key) finish(m, false); }); }
  function stepMotions(t) {
    var list = motions.slice();
    for (var i = 0; i < list.length; i++) {
      var m = list[i];
      if (m.done || t < m.t0) continue;
      if (!m.started) { m.started = true; if (m.onStart) m.onStart(); }
      var u = (t - m.t0) / m.dur;
      if (u >= 1) finish(m, true); else m.fn(u);
    }
  }
  // 축마다 다른 크기를 차례로(Codematic Ease.scale 의 줄)
  function squashSeq(st, steps, key, tok, owner) {
    var p = Promise.resolve();
    steps.forEach(function (s) {
      p = p.then(function () {
        if (dead || (owner && tok !== owner.hTok)) return;
        var ax = st.sx, ay = st.sy, f = Ease[s[2]];
        return drive(s[0], function (t) { var e = f(t); st.sx = st.sz = lerp(ax, s[1][0], e); st.sy = lerp(ay, s[1][1], e); }, { key: key });
      });
    });
    return p;
  }
  // 모션끼리 줄 세우기(같은 노드를 두 곳에서 움직이지 않게)
  var queue = Promise.resolve();
  function claim() {
    var release, p = new Promise(function (r) { release = r; });
    var prev = queue; queue = queue.then(function () { return p; });
    return prev.then(function () { return release; });
  }

  function kick() { if (!raf && !dead && visible && inView) raf = requestAnimationFrame(frame); }
  function requestRender() { dirty = true; kick(); }
  function frame(ms) {
    raf = 0;
    if (dead) return;
    stepMotions(now());
    applyAll();
    renderer.render(scene, camera);
    dirty = false;
    if (motions.length) kick();
  }

  /* ----- 장면: 벽, 바닥, 선반, 받침, 명판, 조명 ----- */
  var world = new THREE.Group(); scene.add(world);
  var layoutGroup = null, layoutTrash = [], labelTrash = [];
  var wallGeo = keep(new THREE.PlaneGeometry(80, 40)); wallGeo.translate(0, 10, 0);   // 바닥(y=0) 위로만
  var wall = mesh(wallGeo, M.wall, false); world.add(wall);
  var floor = mesh(keep(new THREE.PlaneGeometry(80, 30)), M.floor, false); floor.rotation.x = -PI / 2; world.add(floor);

  /* ----- 앱 ----- */
  var items = apps.map(function (app, i) {
    var it = {
      i: i, app: app, cloth: !!app.unreleased,
      seat: new THREE.Vector3(), row: 0, tier: 0,
      st: { y: 0, sx: 1, sy: 1, sz: 1, fly: 0, spin: 0, shown: false },
      ps: { sx: 1, sy: 1, sz: 1 },
      fadeU: { value: 0 }, recvU: { value: 1 },
      fan: null, fanOn: 0, fanH: 0, lamp: null,
      hTok: 0, state: 'hidden', hovered: false, flyFromY: 0, restY: 0,
      pivot: new THREE.Group(), plinth: null, label: null
    };
    world.add(it.pivot);
    if (!it.cloth) {
      it.base = new THREE.Color('#F4F3EE');
      it.rimMat = toon({ tones: tonesOf(it.base), fade: it.fadeU, recvU: it.recvU });
      it.iconTex = texFrom(app.icon, function (im) {
        it.base = edgeColor(im);
        var t = tonesOf(it.base);
        it.rimMat.uniforms.uHi.value.copy(t[0]); it.rimMat.uniforms.uL.value.copy(t[1]);
        it.rimMat.uniforms.uM.value.copy(t[2]); it.rimMat.uniforms.uD.value.copy(t[3]);
      });
      it.iconMat = toon({ map: it.iconTex, fade: it.fadeU, recv: 0 });
      it.backMat = toon({ tones: tonesOf(it.base), fade: it.fadeU, recvU: it.recvU });
      it.hullMat = hullMat(it.fadeU);
      var tile = withHull(tileGeo, [it.iconMat, it.rimMat, it.backMat], it.hullMat, true);
      it.pivot.add(tile);
    } else {
      it.cl = makeClothGeo(46, 30);
      keep(it.cl.geo);
      it.cp = { A: 0.5, B: 0.31, H: 1.1, rc: 0.16, lift: 0, flare: 0, fold: 0.1, room: 0.62 };
      it.clothDirty = true;
      drapeCloth(it.cl, it.cp);
      // 외곽선 법선 = 천의 매끈한 법선(같은 속성을 나눠 쓴다. computeVertexNormals 는 이 속성을 제자리에서 고친다)
      it.cl.geo.setAttribute('onormal', it.cl.geo.attributes.normal);
      var cm = mesh(it.cl.geo, M.cloth, true);
      var ch = mesh(it.cl.geo, M.hull, false, false);
      it.pivot.add(ch); it.pivot.add(cm);
      it.hem = makeHem(it.cl.hem.length);
      it.pivot.add(it.hem.mesh);
    }
    return it;
  });
  var released = items.filter(function (it) { return !it.cloth; });
  var veiled = items.filter(function (it) { return it.cloth; });

  /* ----- 뒤 번짐(DOM): 출시 앱마다 제 번짐 그림(없으면 강조색을 아주 옅게)을 그 자리 뒤 벽에 크게 흐려 겹친다 ----- */
  var blobs = [], veilEl = null;
  if (bgEl) {
    bgEl.innerHTML = '';
    released.forEach(function (it) {
      var a = it.app, el = document.createElement('i');
      el.className = 'shelf-blob' + (a.field ? ' is-field' : ' is-tint');
      if (a.field) el.style.background = 'url("' + a.field + '") center / cover no-repeat, ' + a.color;
      else el.style.background = a.accent;
      // 글자가 밝은(어두운 번짐) 앱은 옅게 깔아 파스텔로 둔다
      var base = a.field ? (a.ink === 'light' ? 0.34 : 0.72) : 0.16;
      el.style.opacity = String(base);
      bgEl.appendChild(el);
      var b = { it: it, el: el, base: base, o: base, o0: base, o1: base };
      it.blob = b;
      blobs.push(b);
    });
    veilEl = document.createElement('i');
    veilEl.className = 'shelf-veil';
    veilEl.style.background = C.fade;
    veilEl.style.opacity = '0';
    bgEl.appendChild(veilEl);
  }
  // 번짐 자리: 맨 윗줄은 타일 뒤, 아랫줄은 같은 세로줄의 벽(윗줄보다 조금 위). 벽만 보이므로 아래는 선반이 가린다
  function placeBlobs() {
    if (!bgEl || !L) return;
    var r = wrap.getBoundingClientRect(), br = bgEl.getBoundingClientRect();
    var ox = r.left - br.left, oy = r.top - br.top, top = L.R - 1;
    var size = L.P * view.ppu * (L.wide ? 2.3 : 2.1);
    var topY = toPx(0, L.h(top) + PL.h + TILE_H * 0.5, L.wallZ + L.D / 2).y;
    blobs.forEach(function (b) {
      var it = b.it, x = toPx(it.seat.x, 0, it.seat.z).x;
      var y = it.tier === top ? topY : topY - (top - it.tier) * size * 0.22;
      b.el.style.width = b.el.style.height = Math.round(size) + 'px';
      b.el.style.transform = 'translate(' + Math.round(ox + x - size / 2) + 'px,' + Math.round(oy + y - size / 2) + 'px)';
    });
    bgEl.style.height = Math.round(r.bottom - br.top + 40) + 'px';
    veilEl.style.top = Math.round(oy) + 'px'; veilEl.style.height = Math.round(r.height) + 'px';
  }
  if (bgEl) on(window, 'resize', placeBlobs);
  var iconsReady = Promise.all(released.map(function (it) { return it.iconTex.userData.ready; }));

  // 자락 끝 먹선(닫힌 줄)
  function makeHem(n) {
    var cnt = n + 1, g = new THREE.BufferGeometry();
    var pos = new Float32Array(cnt * 2 * 3), prv = new Float32Array(cnt * 2 * 3), nxt = new Float32Array(cnt * 2 * 3), side = new Float32Array(cnt * 2);
    for (var i = 0; i < cnt; i++) { side[i * 2] = -1; side[i * 2 + 1] = 1; }
    var idx = [];
    for (var k = 0; k < cnt - 1; k++) { var a = k * 2; idx.push(a, a + 1, a + 2, a + 1, a + 3, a + 2); }
    g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    g.setAttribute('aPrev', new THREE.BufferAttribute(prv, 3));
    g.setAttribute('aNext', new THREE.BufferAttribute(nxt, 3));
    g.setAttribute('aSide', new THREE.BufferAttribute(side, 1));
    g.setIndex(idx);
    keep(g);
    var m = new THREE.Mesh(g, M.line); m.frustumCulled = false;
    return { mesh: m, geo: g, n: n };
  }
  function updateHem(it) {
    var P = it.cl.geo.attributes.position.array, H = it.cl.hem, h = it.hem, n = h.n;
    var pos = h.geo.attributes.position.array, prv = h.geo.attributes.aPrev.array, nxt = h.geo.attributes.aNext.array;
    function put(arr, slot, vi) { for (var s = 0; s < 2; s++) { var o = (slot * 2 + s) * 3; arr[o] = P[vi * 3]; arr[o + 1] = P[vi * 3 + 1]; arr[o + 2] = P[vi * 3 + 2]; } }
    for (var k = 0; k <= n; k++) {
      var cur = H[k % n], pv = H[(k - 1 + n) % n], nx = H[(k + 1) % n];
      put(pos, k, cur); put(prv, k, pv); put(nxt, k, nx);
    }
    h.geo.attributes.position.needsUpdate = true; h.geo.attributes.aPrev.needsUpdate = true; h.geo.attributes.aNext.needsUpdate = true;
  }

  /* ----- 카드(스크린샷)와 잔상, 무대 그림자 받이 ----- */
  var cardTex = {};
  var cards = [0, 1, 2].map(function (k) {
    var zero = { value: 0 };
    var mat = toon({ map: null, recv: 0, fade: zero });
    mat.uniforms.uMap = { value: null };
    mat.defines.MAPPED = '';
    var side = toon({ tones: C.paper, recv: 0, fade: zero });
    var g = withHull(cardGeo, [mat, side, side], hullMat({ value: 0 }), true);
    g.visible = false;
    world.add(g);
    return { k: k, group: g, mat: mat, c: 0 };
  });
  var ghosts = [0.34, 0.2, 0.1].map(function (a) {
    var m = new THREE.Mesh(ghostGeo, keep(new THREE.ShaderMaterial({
      uniforms: { uMap: { value: null }, uOpacity: { value: 0 } },
      vertexShader: GHOST_VS, fragmentShader: GHOST_FS, transparent: true, depthWrite: false, side: THREE.DoubleSide
    })));
    m.visible = false; m.frustumCulled = false; m.userData.a = a;
    world.add(m);
    return m;
  });
  var catcher = new THREE.Mesh(keep(new THREE.PlaneGeometry(80, 50)), keep(new THREE.ShaderMaterial({
    uniforms: THREE.UniformsUtils.merge([THREE.UniformsLib.lights, { uColor: { value: col(C.stageShadow) }, uAmt: { value: 0 } }]),
    vertexShader: TOON_VS, fragmentShader: CATCH_FS, lights: true, transparent: true, depthWrite: false
  })));
  catcher.frustumCulled = false; catcher.receiveShadow = true; catcher.visible = false;
  world.add(catcher);

  /* ----- 배치 ----- */
  var L = null;       // 지금 배치
  var view = { w: 1, h: 1, ppu: 100 };
  var STAGE_Z = 6.2;

  function layoutSpec(wide) {
    if (wide) return { wide: true, rows: arrange(wide), P: 1.8, D: 1.3, h0: 0.62, dh: 1.52, kx: 0.41, ky: 0.287 };
    return { wide: false, rows: arrange(wide), P: 1.42, D: 1.08, h0: 0.62, dh: 1.56, kx: 0.3, ky: 0.39 };
  }
  // 줄 나누기: 앱 수에서 나온다. 가로 화면은 한 줄 다섯까지(9 이면 5, 4), 세로 화면은 세 칸씩.
  // 출시 앱이 데이터 순서대로 뒤(위) 줄부터 채우고, 천은 그 줄 양 끝에 번갈아 선다(왼쪽부터)
  function arrange(wide) {
    var n = items.length, R = wide ? Math.max(1, Math.ceil(n / 5)) : Math.max(1, Math.ceil(n / 3));
    var per = Math.ceil(n / R);
    var seq = released.concat(veiled).map(function (it) { return it.i; }), rows = [];
    for (var r = 0; r < R; r++) {
      var row = seq.slice(r * per, (r + 1) * per);
      var cl = row.filter(function (i) { return items[i].cloth; }), rest = row.filter(function (i) { return !items[i].cloth; });
      var left = [], right = [];
      cl.forEach(function (i, k) { (k % 2 ? right : left).push(i); });
      if (row.length) rows.push(left.concat(rest, right.reverse()));
    }
    return rows;
  }
  function toView(x, y, z) { return { x: x - OBL.kx * z, y: y - OBL.ky * z }; }
  // 사선 투영에서 깊이 z 에 있는 것을 화면에서 타일 한가운데 아래(위)로 맞추는 x
  function alignX(it, z) { return it.seat.x + OBL.kx * (z - it.seat.z); }
  function toPx(x, y, z) {
    var v = toView(x, y, z);
    return { x: (v.x - camera.left) / (camera.right - camera.left) * view.w, y: (camera.top - v.y) / (camera.top - camera.bottom) * view.h };
  }
  function worldAt(px, py, z) {
    var vx = camera.left + px / view.w * (camera.right - camera.left);
    var vy = camera.top - py / view.h * (camera.top - camera.bottom);
    return new THREE.Vector3(vx + OBL.kx * z, vy + OBL.ky * z, z);
  }

  function build() {
    var wide = view.w / view.h >= 1.08;
    if (L && L.wide === wide && L.built) { frameCamera(); placeLabels(); return; }
    if (layoutGroup) { world.remove(layoutGroup); }
    layoutTrash.forEach(function (x) { x.dispose(); }); layoutTrash = [];
    L = layoutSpec(wide);
    OBL.kx = L.kx; OBL.ky = L.ky;
    shared.obl.value.set(OBL.kx, OBL.ky);
    layoutGroup = new THREE.Group(); world.add(layoutGroup);
    var R = L.rows.length, maxN = 0;
    L.rows.forEach(function (r) { maxN = Math.max(maxN, r.length); });
    L.R = R; L.W = maxN * L.P + (L.wide ? 0.5 : 0.36);
    L.h = function (j) { return L.h0 + j * L.dh; };
    L.wallZ = -(R - 1) * L.D;
    function lk(g) { layoutTrash.push(g); return g; }
    // 층(앞 j=0 이 가장 낮다)
    for (var j = 0; j < R; j++) {
      var tier = withHull(lk(roundedBox(L.W, L.h(j), L.D, 0.026)), M.shelf, M.hull, true);
      tier.position.set(0, 0, -j * L.D + L.D / 2);
      layoutGroup.add(tier);
    }
    wall.position.set(0, 10, L.wallZ - 0.03);
    floor.position.set(0, 0, L.wallZ + 15);
    // 앱 자리
    L.rows.forEach(function (row, r) {
      var j = R - 1 - r;
      row.forEach(function (ai, k) {
        var it = items[ai];
        it.row = r; it.tier = j;
        it.seat.set((k - (row.length - 1) / 2) * L.P, L.h(j), -j * L.D + L.D / 2);
      });
    });
    // 받침
    items.forEach(function (it) {
      if (it.plinth) { it.plinth.parent && it.plinth.parent.remove(it.plinth); }
      if (it.cloth) { it.plinth = null; return; }
      it.plinth = withHull(plinthGeo, M.plinth, M.hull, true);
      it.plinth.position.copy(it.seat);
      layoutGroup.add(it.plinth);
    });
    // 조명: 맨 윗줄 위 레일과 등, 벽의 부채꼴. 아랫줄은 뒤 층 앞면에 빛 자국.
    var top = R - 1, topY = L.h(top), lampZ = L.wallZ + 0.3;
    var tileTopView = toView(0, topY + PL.h + TILE_H, L.wallZ + L.D / 2).y;
    var lampVY = tileTopView + (L.wide ? 0.92 : 0.84);
    var lampY = lampVY + OBL.ky * lampZ;
    L.lampY = lampY;
    var rail = withHull(lk(roundedBox(L.W - 0.2, 0.055, 0.06, 0.014)), M.lamp, M.hull, false);
    rail.position.set(0, lampY + 0.2, lampZ - 0.05);
    layoutGroup.add(rail);
    var canGeo = lk(addOutlineNormals(new THREE.CylinderGeometry(0.075, 0.105, 0.21, 32, 1)));
    var discGeo = lk(new THREE.CircleGeometry(0.088, 32));
    var stemGeo = lk(roundedBox(0.032, 0.16, 0.032, 0.008));
    items.forEach(function (it) {
      it.fan = null; it.lamp = null;
      if (it.cloth) return;
      var isTop = it.tier === top;
      var fanMat = toon({ flat: isTop ? C.wallLit : C.riserLit, transparent: true, opacity: 0, glow: '#FFFFFF', polygonOffset: -2, nospot: isTop });
      trash.pop(); layoutTrash.push(fanMat);
      var shape, fan;
      if (isTop) {
        shape = scallop(0.13, Math.tan(20 * PI / 180), lampY - 0.1 + OBL.ky * 0.3, topY - 0.25, 99);
        fan = mesh(lk(new THREE.ShapeGeometry(shape, 24)), fanMat, false);
        fan.position.set(alignX(it, L.wallZ - 0.026), 0, L.wallZ - 0.026);
        // 등: 줄기와 기울인 통(여는 쪽이 앞 아래를 본다)
        var lamp = new THREE.Group();
        lamp.position.set(alignX(it, lampZ), lampY, lampZ);
        var stem = withHull(stemGeo, M.lamp, M.hull, false); stem.position.y = 0.06; lamp.add(stem);
        var can = new THREE.Group(); can.rotation.x = -0.62; lamp.add(can);
        can.add(withHull(canGeo, M.lamp, M.hull, false));
        var discMat = toon({ flat: '#3A3A40', glow: C.lampOn }); trash.pop(); layoutTrash.push(discMat);
        var disc = mesh(discGeo, discMat, false); disc.rotation.x = PI / 2; disc.position.y = -0.106; can.add(disc);
        layoutGroup.add(lamp);
        it.lamp = { group: lamp, disc: discMat };
      } else {
        var ztop = L.h(it.tier + 1);
        shape = scallop(0.2, Math.tan(20 * PI / 180), ztop + 0.5, L.h(it.tier) - 0.2, ztop - 0.003);
        fan = mesh(lk(new THREE.ShapeGeometry(shape, 24)), fanMat, false);
        fan.position.set(alignX(it, -it.tier * L.D), 0, -it.tier * L.D + 0.004);
      }
      layoutGroup.add(fan);
      it.fan = fan; it.fanMat = fanMat; it.fanWall = isTop;
    });
    // 아랫줄은 늘어난 꼭대기가 윗줄 받침 윗면 아래에 머무는 높이에서 떨어진다(윗줄 앞을 스치지 않게)
    items.forEach(function (it) {
      if (it.tier === top) { it.fallH = BEAT.fallFrom; return; }
      var up = L.h(it.tier + 1) + PL.h - OBL.ky * (-(it.tier + 1) * L.D + L.D / 2);
      var tall = it.cloth ? it.cp.H * BEAT.cloth.fallS[1] : PL.h + TILE_H * BEAT.fallS[1];
      it.fallH = Math.max(0.25, up - 0.05 - (it.seat.y - OBL.ky * it.seat.z) - tall);
    });
    L.built = true;
    frameCamera();
    placeLabels();
    // 받침 자리와 천 자락 한계
    items.forEach(function (it) { if (it.cloth) { it.cp.room = L.D / 2 - 0.03; it.cp.B = Math.min(0.31, L.D / 2 - 0.24); it.clothDirty = true; } });
  }
  // 벽 조명 자국: 등에서 원뿔이 벽에 닿는 쌍곡선(위가 둥근 V) 아래를 한 톤으로
  function scallop(d, T, y0, yb, yClip) {
    var ya = y0 - d / T, top = Math.min(ya, yClip), pts = [], N = 40, i;
    function w(y) { var v = T * T * (y0 - y) * (y0 - y) - d * d; return v > 0 ? Math.sqrt(v) : 0; }
    for (i = 0; i <= N; i++) { var u = i / N, y = top - (top - yb) * u * u; pts.push([w(y), y]); }
    var s = new THREE.Shape();
    s.moveTo(-pts[N][0], pts[N][1]);
    for (i = N; i >= 0; i--) s.lineTo(-pts[i][0], pts[i][1]);
    for (i = 0; i <= N; i++) s.lineTo(pts[i][0], pts[i][1]);
    return s;
  }

  // 명판: 종이 라벨(먹선 테두리, 이름). 출시 전은 빈 라벨에 버밀리언 봉인 점.
  function placeLabels() {
    labelTrash.forEach(function (x) { x.dispose(); }); labelTrash = [];
    items.forEach(function (it) {
      if (it.label) { it.label.parent && it.label.parent.remove(it.label); }
      var j = it.tier, ppu = view.ppu;
      var lh = Math.max(L.wide ? 0.27 : 0.3, 23 / ppu);
      var fontPx = lh * ppu * 0.47;
      var ctx = document.createElement('canvas').getContext('2d');
      ctx.font = '600 ' + fontPx + 'px ' + FONT;
      var tw = it.cloth ? lh * ppu * 1.6 : ctx.measureText(it.app.name).width;
      var lw = Math.min(L.P - 0.12, (tw + fontPx * 1.5) / ppu);
      var shape = roundRectShape(lw, lh, Math.min(0.035, lh * 0.18));
      var geo = splitCaps(new THREE.ExtrudeGeometry(shape, { depth: 0.01, bevelEnabled: true, bevelThickness: 0.006, bevelSize: 0.006, bevelSegments: 2, curveSegments: 6, steps: 1, UVGenerator: capUV(-lw / 2, -lh / 2, lw, lh) }));
      labelTrash.push(geo);
      var tex = labelTexture(it, lw, lh, fontPx);
      labelTrash.push(tex);
      var fm = toon({ map: tex }); trash.pop(); labelTrash.push(fm);
      var g = withHull(geo, [fm, M.paper, M.paper], M.hull, true);
      var z = -j * L.D + L.D + 0.012;
      var y = j === 0 ? L.h(0) * 0.5 : L.h(j) - 0.1 - lh / 2;
      g.position.set(alignX(it, z), y, z);
      layoutGroup.add(g);
      it.label = g; it.labelBox = { w: lw, h: lh, y: y, z: z };
    });
    placeHits();
    placeBlobs();
    if (spot.it) shared.spotBox.value.copy(spotBoxOf(spot.it));
    layoutStage();
    requestRender();
  }
  function labelTexture(it, lw, lh, fontPx) {
    var c = document.createElement('canvas');
    var W = Math.max(8, Math.round(lw * view.ppu * DPR)), H = Math.max(8, Math.round(lh * view.ppu * DPR));
    c.width = W; c.height = H;
    var x = c.getContext('2d');
    x.fillStyle = '#FFFFFF'; x.fillRect(0, 0, W, H);
    if (it.cloth) {
      x.fillStyle = C.verm; x.beginPath(); x.arc(W / 2, H / 2, H * 0.16, 0, PI * 2); x.fill();
    } else {
      x.fillStyle = C.ink; x.textAlign = 'center'; x.textBaseline = 'middle';
      x.font = '600 ' + (fontPx * DPR) + 'px ' + FONT;
      x.fillText(it.app.name, W / 2, H / 2 + H * 0.03);
    }
    var t = new THREE.CanvasTexture(c);
    t.colorSpace = THREE.SRGBColorSpace; t.generateMipmaps = false; t.minFilter = THREE.LinearFilter;
    return t;
  }

  // 사선 투영 화면 상자에 장면을 맞춘다
  function frameCamera() {
    var R = L.R, pts = [], x0 = -L.W / 2, x1 = L.W / 2;
    var zb = L.wallZ, zf = L.D;
    [x0, x1].forEach(function (x) {
      pts.push(toView(x, 0, zf + 0.35), toView(x, L.h(R - 1), zb));
    });
    pts.push(toView(0, L.lampY + 0.3, L.wallZ + 0.3));
    var minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
    pts.forEach(function (p) { minX = Math.min(minX, p.x); maxX = Math.max(maxX, p.x); minY = Math.min(minY, p.y); maxY = Math.max(maxY, p.y); });
    var bw = maxX - minX, bh = maxY - minY;
    var padX = L.wide ? 0.07 : 0.045, padY = L.wide ? 0.1 : 0.14;
    var ppu = Math.min(view.w * (1 - 2 * padX) / bw, view.h * (1 - 2 * padY) / bh);
    view.ppu = ppu;
    var cx = (minX + maxX) / 2, cy = (minY + maxY) / 2 + (L.wide ? 0 : -0.1);
    var hw = view.w / ppu / 2, hh = view.h / ppu / 2;
    camera.left = cx - hw; camera.right = cx + hw; camera.top = cy + hh; camera.bottom = cy - hh;
    applyProjection();
    shared.inkW.value = (L.wide ? Math.max(1.6, Math.min(2.2, ppu / 58)) : 1.5) * DPR;
    // 그림자 카메라: 장면 상자를 빛 공간에 맞춘다
    fitShadow(sun, LS, new THREE.Box3(new THREE.Vector3(x0 - 0.6, 0, zb), new THREE.Vector3(x1 + 0.6, L.lampY + 0.5, zf + 1.2)));
    var a = worldAt(0, 0, STAGE_Z), b = worldAt(view.w, view.h, STAGE_Z);
    // 무대 그림자가 화면에서 오른쪽 아래로 딱 떨어지게 빛 방향을 거꾸로 푼다.
    // 받이까지 깊이 dz 만큼 물러나면 사선 투영이 (kx, ky) 곱하기 dz 만큼 오른쪽 위로 민다. 그만큼 빛으로 되돌린다.
    var dz = 1.2, off = 10 / ppu, offY = -13 / ppu;
    LSTAGE.set(OBL.kx - off / dz, OBL.ky - offY / dz, 1).normalize();
    fitShadow(stageLight, LSTAGE, new THREE.Box3(new THREE.Vector3(Math.min(a.x, b.x) - 1, Math.min(a.y, b.y) - 1, STAGE_Z - 2.4), new THREE.Vector3(Math.max(a.x, b.x) + 1, Math.max(a.y, b.y) + 1, STAGE_Z + 1.6)));
    catcher.position.set((a.x + b.x) / 2, (a.y + b.y) / 2, STAGE_Z - 1.45);
  }
  function fitShadow(light, dir, box) {
    var c = box.getCenter(new THREE.Vector3());
    light.position.copy(c).addScaledVector(dir, 30);
    light.target.position.copy(c);
    light.updateMatrixWorld(); light.target.updateMatrixWorld();
    var m = new THREE.Matrix4().lookAt(light.position, c, new THREE.Vector3(0, 1, 0));
    var inv = new THREE.Matrix4().makeTranslation(light.position.x, light.position.y, light.position.z).multiply(m).invert();
    var mn = new THREE.Vector3(Infinity, Infinity, Infinity), mx = new THREE.Vector3(-Infinity, -Infinity, -Infinity), p = new THREE.Vector3();
    for (var i = 0; i < 8; i++) {
      p.set(i & 1 ? box.max.x : box.min.x, i & 2 ? box.max.y : box.min.y, i & 4 ? box.max.z : box.min.z).applyMatrix4(inv);
      mn.min(p); mx.max(p);
    }
    var cam = light.shadow.camera;
    cam.left = mn.x - 0.2; cam.right = mx.x + 0.2; cam.bottom = mn.y - 0.2; cam.top = mx.y + 0.2;
    cam.near = Math.max(0.1, -mx.z - 2); cam.far = -mn.z + 2;
    cam.updateProjectionMatrix();
    light.shadow.needsUpdate = true;
  }

  /* ----- 무대(시그니처) 배치: 화면 픽셀로 정하고 월드로 옮긴다 ----- */
  var SL = null;
  function layoutStage() {
    var W = view.w, H = view.h, s = {};
    if (W / H >= 1.05) {
      var ch = Math.min(H * 0.6, 470), cw = ch * CARD_AR, gap = cw * 0.1;
      var ts = Math.min(H * 0.36, W * 0.23, 300);
      var total = ts + ts * 0.34 + 3 * cw + 2 * gap, x0 = (W - total) / 2, cy = H * 0.47;
      s.tile = { x: x0 + ts / 2, y: cy - 6, size: ts };
      s.cards = [0, 1, 2].map(function (k) { return { x: x0 + ts * 1.34 + cw / 2 + k * (cw + gap), y: cy + [4, -6, 4][k], w: cw, rot: [0.03, 0, -0.03][k], dz: 0 }; });
      s.more = { x: s.cards[1].x, y: cy + ch / 2 + 30 };
    } else {
      var ts2 = Math.min(W * 0.5, H * 0.24);
      var cw2 = Math.min(W * 0.37, H * 0.42 * CARD_AR), ch2 = cw2 / CARD_AR;
      var ty = Math.max(H * 0.2, 70 + ts2 / 2);
      var cy2 = ty + ts2 / 2 + 26 + ch2 / 2;
      s.tile = { x: W / 2, y: ty, size: ts2 };
      s.cards = [-1, 0, 1].map(function (o) { return { x: W / 2 + o * cw2 * 0.7, y: cy2 + Math.abs(o) * ch2 * 0.035, w: cw2, rot: -o * 0.07, dz: o === 0 ? 0.12 : 0 }; });
      s.more = { x: W / 2, y: cy2 + ch2 / 2 + 36 };
    }
    var S = s.tile.size / view.ppu / TILE_W;
    var c = worldAt(s.tile.x, s.tile.y, STAGE_Z);
    s.S = S;
    s.tileCenter = c;
    s.tilePivot = new THREE.Vector3(c.x, c.y - 0.54 * S, c.z);
    s.cardW = s.cards.map(function (cd) { return cd.w / view.ppu; });
    s.cardPos = s.cards.map(function (cd) { return worldAt(cd.x, cd.y, STAGE_Z - 0.25 + cd.dz); });
    s.cardFrom = worldAt(s.tile.x, s.tile.y, STAGE_Z - 0.5);
    SL = s;
    moreEl.style.left = s.more.x + 'px'; moreEl.style.top = s.more.y + 'px';
    var r = s.tile.size * 0.62;
    spinEl.style.left = (s.tile.x - r) + 'px'; spinEl.style.top = (s.tile.y - r) + 'px';
    spinEl.style.width = spinEl.style.height = (2 * r) + 'px';
    requestRender();
  }

  /* ----- 포즈 ----- */
  var current = null;
  function flyPose(it, s, out) {
    var e = Ease.settle(s), eo = Ease.outCubic(s), em = lerp(eo, e, 0.55);
    var from = it.seat, to = SL.tilePivot;
    out.x = lerp(from.x, to.x, em);
    out.z = lerp(from.z, to.z, em);
    out.y = lerp(it.restY + it.flyFromY * (1 - eo), to.y, em) + 0.7 * Math.sin(PI * clamp01(s / 0.46));
    out.s = lerp(1, SL.S, lerp(eo, e, 0.8));
    out.ry = PI * e;                                     // 180°: 넘쳤다 흔들려 뒷면에 선다
    var c = Ease.outCubic(clamp01(s / 0.2));             // 움츠림에서 풀려난다
    var k1 = Math.sin(PI * clamp01(s / 0.3)), k2 = Math.sin(PI * clamp01((s - 0.26) / 0.3));
    out.sx = lerp(BEAT.crouchS[0], 1, c) * (1 - 0.07 * k1 + 0.05 * k2);
    out.sy = lerp(BEAT.crouchS[1], 1, c) * (1 + 0.16 * k1 - 0.07 * k2);
    return out;
  }
  var tmpPose = {};
  function applyItem(it) {
    var st = it.st, p = it.pivot;
    p.visible = st.shown;
    if (!st.shown) return;
    it.restY = it.seat.y + (it.plinth ? PL.h * it.ps.sy : 0);
    var x = it.seat.x, y = it.restY + st.y, z = it.seat.z, sc = 1, ry = st.spin, sx = st.sx, sy = st.sy, sz = st.sz;
    if (st.fly > 0 && SL) {
      var f = flyPose(it, st.fly, tmpPose);
      x = f.x; y = f.y + st.y; z = f.z; sc = f.s; ry += f.ry; sx *= f.sx; sy *= f.sy; sz *= f.sx;
    }
    p.position.set(x, y, z);
    p.rotation.set(0, ry, 0);
    p.scale.set(sc * sx, sc * sy, sc * sz);
    if (it.plinth) it.plinth.scale.set(it.ps.sx, it.ps.sy, it.ps.sz);
    if (it.cloth && it.clothDirty) { drapeCloth(it.cl, it.cp); updateHem(it); it.clothDirty = false; }
  }
  function cardPose(cd) {
    var g = cd.group, c = cd.c;
    g.visible = c > 0.002 && !!SL;
    if (!g.visible) return;
    var e = Ease.settle(c), eo = Ease.outCubic(c), em = lerp(eo, e, 0.7);
    var a = SL.cardFrom, b = SL.cardPos[cd.k], w = SL.cardW[cd.k];
    g.position.set(lerp(a.x, b.x, em), lerp(a.y, b.y, em), lerp(a.z, b.z, eo));
    var sc = lerp(0.28, 1, lerp(eo, e, 0.9)) * w;
    var k1 = Math.sin(PI * clamp01(c / 0.42));
    var horiz = Math.abs(b.x - a.x) > Math.abs(b.y - a.y);
    var sx = horiz ? 1 + 0.2 * k1 : 1 - 0.07 * k1, sy = horiz ? 1 - 0.07 * k1 : 1 + 0.2 * k1;
    g.scale.set(sc * sx, sc * sy, sc);
    g.rotation.set(0, 0, lerp(-0.22, SL.cards[cd.k].rot, e));
  }
  var ghostClock = -1, ghostItem = null;
  function applyGhosts() {
    ghosts.forEach(function (g, k) {
      if (ghostClock < 0 || !ghostItem) { g.visible = false; return; }
      var tt = ghostClock - BEAT.ghosts[k];
      var s = tt <= 0 ? 1 : 1 - clamp01(tt / BEAT.flyBack);
      var f = flyPose(ghostItem, s, tmpPose);
      g.visible = s > 0.02;
      g.position.set(f.x, f.y, f.z);
      g.rotation.set(0, f.ry, 0);
      g.scale.set(f.s * f.sx, f.s * f.sy, f.s);
      var gu = g.material.uniforms;
      gu.uMap.value = ghostItem.engraveTex || ghostItem.iconTex;
      gu.uOpacity.value = g.userData.a * Math.min(1, s * 3) * clamp01(ghostClock / 0.06);
    });
  }
  function applyAll() {
    items.forEach(function (it) {
      it.fadeU.value = it === current ? 0 : shared.fade.value;
      applyItem(it);
      if (it.fanMat) {
        // 벽 조명 자국은 투명한 벽 위의 흰 빛이라, 쉬면 옅게, 호버면 진하게, 다른 자리가 밝아지면 조금 옅게
        var fo = it.fanOn;
        if (it.fanWall) fo *= lerp(BEAT.spot.fanRest, 1, it.fanH) * (1 - 0.45 * shared.spotAmt.value * (1 - it.fanH));
        it.fanMat.uniforms.uOpacity.value = fo;
        it.fanMat.uniforms.uGlow.value = it.fanH * 0.75;
      }
      if (it.lamp) it.lamp.disc.uniforms.uGlow.value = Math.min(1, it.fanOn) * (0.85 + 0.15 * it.fanH);
    });
    cards.forEach(cardPose);
    applyGhosts();
    var amt = shared.fade.value / FADE;
    if (veilEl) veilEl.style.opacity = shared.fade.value.toFixed(3);
    catcher.visible = amt > 0.001;
    catcher.material.uniforms.uAmt.value = 0.3 * amt;
    if (amt > 0.001 || current) stageLight.shadow.needsUpdate = true;
  }

  /* ----- 누름 자리(DOM 단추) ----- */
  var hits = items.map(function (it) {
    var b = document.createElement('button');
    b.type = 'button';
    b.className = 'c-toon-shelf__hit' + (it.cloth ? ' is-veiled' : '');
    b.setAttribute('aria-label', it.cloth ? UI.veiled : it.app.name + ', ' + it.app.subtitle);
    if (it.cloth) b.setAttribute('aria-disabled', 'true');
    b.dataset.i = it.i;
    hitsEl.appendChild(b);
    it.hit = b;
    on(b, 'pointerenter', function (e) { if (e.pointerType === 'mouse') hoverIn(it); });
    on(b, 'pointerleave', function (e) { if (e.pointerType === 'mouse' && !b.matches(':focus-visible')) hoverOut(it); });
    on(b, 'focus', function () { if (b.matches(':focus-visible')) hoverIn(it); });
    on(b, 'blur', function () { if (!b.matches(':hover')) hoverOut(it); });
    on(b, 'click', function () { if (it.cloth) poke(it); else select(it); });
    return b;
  });
  function placeHits() {
    items.forEach(function (it) {
      var topY = it.seat.y + PL.h + TILE_H + BEAT.hover.y + 0.05, z = it.seat.z, lb = it.labelBox;
      var a = toPx(it.seat.x - 0.62, topY, z);
      var b = toPx(alignX(it, lb.z) + 0.62, lb.y - lb.h / 2 - 0.04, lb.z);
      var el = it.hit;
      el.style.left = a.x + 'px'; el.style.top = a.y + 'px';
      el.style.width = Math.max(44, b.x - a.x) + 'px'; el.style.height = Math.max(44, b.y - a.y) + 'px';
      // 초점 테: 타일 둘레
      // 초점 = 호버라서 타일은 떠오른 자리에 있다
      var ty = it.seat.y + PL.h + (it.cloth || reduced ? 0 : BEAT.hover.y), th = it.cloth ? it.cp.H + 0.06 : TILE_H, tw = it.cloth ? 0.7 : 0.54;
      // 사선 투영이라 뒷면이 오른쪽 위로 밀려 보인다. 앞면의 왼쪽 아래와 뒷면의 오른쪽 위를 함께 감싸야
      // 테가 타일 먹선과 겹치지 않고 사방으로 같은 틈을 둔다.
      var fx0, fy0, fx1, fy1;
      if (it.cloth) {
        // 천은 쉬는 모양의 꼭짓점을 그대로 화면에 찍어 실루엣을 감싼다(자락이 선반에 고인 끝까지)
        if (it.clothDirty) { drapeCloth(it.cl, it.cp); updateHem(it); it.clothDirty = false; }
        var P = it.cl.geo.attributes.position.array;
        fx0 = fy0 = Infinity; fx1 = fy1 = -Infinity;
        for (var q = 0; q < P.length; q += 9) {
          var sp = toPx(it.seat.x + P[q], it.seat.y + P[q + 1], z + P[q + 2]);
          if (sp.x < fx0) fx0 = sp.x; if (sp.x > fx1) fx1 = sp.x; if (sp.y < fy0) fy0 = sp.y; if (sp.y > fy1) fy1 = sp.y;
        }
      } else {
        var f0 = toPx(it.seat.x - tw, ty + th, z + TILE_D / 2), f1 = toPx(it.seat.x + tw, ty, z + TILE_D / 2);
        var k0 = toPx(it.seat.x - tw, ty + th, z - TILE_D / 2), k1 = toPx(it.seat.x + tw, ty, z - TILE_D / 2);
        fx0 = Math.min(f0.x, k0.x); fy0 = Math.min(f0.y, k0.y); fx1 = Math.max(f1.x, k1.x); fy1 = Math.max(f1.y, k1.y);
      }
      el.style.setProperty('--fx', (fx0 - a.x - 5) + 'px'); el.style.setProperty('--fy', (fy0 - a.y - 5) + 'px');
      el.style.setProperty('--fw', (fx1 - fx0 + 10) + 'px'); el.style.setProperty('--fh', (fy1 - fy0 + 10) + 'px');
    });
  }

  /* ----- 입장 ----- */
  function seatNow(it) {
    it.st.shown = true; it.st.y = 0; it.st.sx = it.st.sy = it.st.sz = 1; it.state = 'seated';
    if (!it.cloth) it.fanOn = 1;
  }
  function lampOn(it) {
    if (!it.fanMat) return;
    sfx('lamp');
    drive(BEAT.lamp, function (t) { it.fanOn = t < 0.34 ? 1 : t < 0.68 ? 0.35 : 1; });
  }
  function plinthPunch(it, k) {
    if (!it.plinth) return;
    var ps = it.ps, amt = k == null ? 1 : k;
    squashSeq(ps, BEAT.plinth.map(function (s) { return [s[0], [lerp(1, s[1][0], amt), lerp(1, s[1][1], amt)], s[2]]; }), 'p' + it.i);
  }
  // 같은 낙하 속도: 길이는 높이의 제곱근에 비례(맨 윗줄은 표의 값 그대로)
  function fallDur(full, h) { return Math.max(BEAT.fallLowMin, full * Math.sqrt(Math.min(1, h / BEAT.fallFrom))); }
  function dropTile(it) {
    var st = it.st, H = it.fallH || BEAT.fallFrom;
    st.shown = true; it.state = 'dropping';
    return drive(fallDur(BEAT.fall, H), function (t) {
      var e = Ease.inQuad(t);
      st.y = H * (1 - e); st.sx = st.sz = lerp(1, BEAT.fallS[0], e); st.sy = lerp(1, BEAT.fallS[1], e);
    }).then(function () {
      sfx('thud'); lampOn(it); plinthPunch(it);
      var hh = BEAT.hopH * TILE_H;
      drive(BEAT.hop[1], function (t) { st.y = hh * Ease.outQuad(t); }, { delay: BEAT.hop[0] }).then(function () {
        return drive(BEAT.hop[2], function (t) { st.y = hh * (1 - Ease.inQuad(t)); });
      }).then(function () { sfx('tick'); });
      return squashSeq(st, BEAT.land);
    }).then(function () { st.y = 0; it.state = 'seated'; if (it.hovered) hoverIn(it); });
  }
  function dropCloth(it) {
    var st = it.st, H = it.fallH || BEAT.fallFrom, cb = BEAT.cloth, cp = it.cp;
    st.shown = true; it.state = 'dropping';
    return drive(fallDur(cb.fall, H), function (t) {
      var e = Ease.inQuad(t);
      st.y = H * (1 - e); st.sx = st.sz = lerp(1, cb.fallS[0], e); st.sy = lerp(1, cb.fallS[1], e);
      cp.flare = -0.35 * e; it.clothDirty = true;
    }).then(function () {
      sfx('soft');
      st.y = 0;
      return drive(cb.hit, function (t) {
        var e = Ease.outQuad(t);
        st.sx = st.sz = lerp(cb.fallS[0], cb.hitS[0], e); st.sy = lerp(cb.fallS[1], cb.hitS[1], e);
        cp.flare = lerp(-0.35, 1, e); cp.fold = lerp(0.1, 0.16, e); it.clothDirty = true;
      });
    }).then(function () {
      return drive(cb.settle, function (t) {
        var e = Ease.settle(t);
        st.sx = st.sz = lerp(cb.hitS[0], 1, e); st.sy = lerp(cb.hitS[1], 1, e);
        cp.flare = lerp(1, 0, e); cp.fold = lerp(0.16, 0.1, e); it.clothDirty = true;
      });
    }).then(function () { it.state = 'seated'; });
  }
  function intro() {
    return claim().then(function (release) {
      return iconsReady.then(function () {
        if (dead) return;
        if (reduced) { items.forEach(seatNow); requestRender(); return; }
        return wait(0.3).then(function () {
          var order = released.concat(veiled), at = enterTimes(released.length, veiled.length);
          return Promise.all(order.map(function (it, k) {
            return wait(at[k]).then(function () { return it.cloth ? dropCloth(it) : dropTile(it); });
          }));
        });
      }).then(release, release);
    });
  }

  /* ----- 호버와 초점: 예비로 살짝 눌렸다가 떠오르고 settle ----- */
  function spotDur() { return reduced ? BEAT.spot.reduced : BEAT.spot.dur; }
  function spotEase() { return reduced ? Ease.lin : Ease[BEAT.spot.ease]; }
  function fanHover(it, v) {
    if (!it.fanMat) return;
    var a = it.fanH, f = spotEase();
    drive(spotDur(), function (t) { it.fanH = lerp(a, v, f(t)); }, { key: 'f' + it.i });
  }
  // 호버 조명: 그 자리를 감싸는 화면 상자(타일 꼭대기와 떠오른 높이부터 명판 아래까지)
  var spot = { it: null };
  function spotBoxOf(it) {
    var top = toView(it.seat.x, it.seat.y + PL.h + TILE_H + BEAT.hover.y + 0.04, it.seat.z);
    var lb = it.labelBox, bot = toView(alignX(it, lb.z), lb.y - lb.h / 2 - 0.06, lb.z);
    var hw = L.wide ? 0.66 : L.P * 0.44;
    return new THREE.Vector4(top.x, (top.y + bot.y) / 2, hw, (top.y - bot.y) / 2);
  }
  // 켜고 끄고 옮기기 모두 같은 곡선 하나. 뒤 번짐도 같은 박자로 진해지고(그 앱) 살짝 옅어진다(나머지)
  function spotTo(it) {
    if (spot.it === it && it) return;
    spot.it = it;
    var f = spotEase(), a0 = shared.spotAmt.value, a1 = it ? 1 : 0;
    var b0 = shared.spotBox.value.clone(), b1 = it ? spotBoxOf(it) : b0.clone();
    if (a0 < 0.002) b0.copy(b1);
    blobs.forEach(function (b) { b.o0 = b.o; b.o1 = !it ? b.base : b.it === it ? Math.min(1, b.base * BEAT.spot.blobUp) : b.base * BEAT.spot.blobDown; });
    drive(spotDur(), function (t) {
      var e = f(t);
      shared.spotBox.value.lerpVectors(b0, b1, e);
      shared.spotAmt.value = lerp(a0, a1, e);
      blobs.forEach(function (b) { b.o = lerp(b.o0, b.o1, e); b.el.style.opacity = b.o.toFixed(3); });
    }, { key: 'spot' });
  }
  function hoverIn(it) {
    it.hovered = true;
    if (it.state !== 'seated' || current) return;
    fanHover(it, 1);
    if (!it.cloth) spotTo(it);
    var tok = ++it.hTok, st = it.st, B = BEAT.hover, key = 'h' + it.i;
    if (reduced) return;
    if (it.cloth) {
      var cp = it.cp, l0 = cp.lift;
      drive(B.press, function (t) { cp.lift = lerp(l0, -0.03, Ease.outQuad(t)); it.clothDirty = true; }, { key: key }).then(function () {
        if (tok !== it.hTok) return;
        sfx('tap');
        return drive(B.rise, function (t) { var e = Ease.settle(t); cp.lift = lerp(-0.03, 0.08, e); cp.fold = lerp(0.1, 0.125, e); it.clothDirty = true; }, { key: key });
      });
      return;
    }
    var ax = st.sx, ay = st.sy;
    drive(B.press, function (t) { var e = Ease.outQuad(t); st.sx = st.sz = lerp(ax, B.pressS[0], e); st.sy = lerp(ay, B.pressS[1], e); }, { key: key }).then(function () {
      if (tok !== it.hTok) return;
      var y0 = st.y;
      return drive(B.rise, function (t) {
        var e = Ease.settle(t), k = Math.sin(PI * clamp01(t / 0.35));
        st.y = lerp(y0, B.y, e);
        st.sx = st.sz = lerp(B.pressS[0], 1, e) * (1 - 0.025 * k); st.sy = lerp(B.pressS[1], 1, e) * (1 + 0.045 * k);
      }, { key: key });
    });
  }
  function hoverOut(it) {
    it.hovered = false;
    fanHover(it, 0);
    if (spot.it === it) spotTo(null);
    if (it.state !== 'seated' || reduced) return;
    var tok = ++it.hTok, st = it.st, B = BEAT.hover, key = 'h' + it.i;
    if (it.cloth) {
      var cp = it.cp, l0 = cp.lift, f0 = cp.fold;
      drive(0.36, function (t) { var e = Ease.settle(t); cp.lift = lerp(l0, 0, e); cp.fold = lerp(f0, 0.1, e); it.clothDirty = true; }, { key: key });
      return;
    }
    var y0 = st.y, ax = st.sx, ay = st.sy;
    if (y0 < 0.01) { squashSeq(st, [[0.2, [1, 1], 'settle']], key, tok, it); return; }
    drive(B.drop * Math.sqrt(y0 / B.y), function (t) {
      var e = Ease.inQuad(t);
      st.y = y0 * (1 - e); st.sx = st.sz = lerp(ax, 0.975, e); st.sy = lerp(ay, 1.04, e);
    }, { key: key }).then(function () {
      if (tok !== it.hTok) return;
      st.y = 0; sfx('tap');
      return squashSeq(st, B.land, key, tok, it);
    });
  }
  // 출시 전 천: 톡 튀어 자락이 출렁인다(이름은 끝까지 없다)
  function poke(it) {
    say(UI.soon);
    if (reduced || it.state !== 'seated') return;
    var tok = ++it.hTok, st = it.st, cp = it.cp, key = 'h' + it.i;
    var a = [st.sx, st.sy];
    drive(0.1, function (t) { var e = Ease.outCubic(t); st.sx = st.sz = lerp(a[0], 1.06, e); st.sy = lerp(a[1], 0.88, e); }, { key: key }).then(function () {
      if (tok !== it.hTok) return;
      return drive(0.17, function (t) { var e = Ease.outQuad(t); st.y = 0.3 * e; st.sx = st.sz = lerp(1.06, 0.92, e); st.sy = lerp(0.88, 1.12, e); cp.flare = -0.4 * e; it.clothDirty = true; }, { key: key });
    }).then(function () {
      if (tok !== it.hTok) return;
      return drive(0.15, function (t) { var e = Ease.inQuad(t); st.y = 0.3 * (1 - e); cp.flare = lerp(-0.4, -0.2, e); it.clothDirty = true; }, { key: key });
    }).then(function () {
      if (tok !== it.hTok) return;
      st.y = 0; sfx('soft');
      return drive(0.5, function (t) {
        var e = Ease.settle(t);
        st.sx = st.sz = lerp(1.1, 1, e); st.sy = lerp(0.84, 1, e);
        cp.flare = lerp(0.9, 0, e); cp.lift = lerp(cp.lift, 0, t); it.clothDirty = true;
      }, { key: key });
    });
  }

  /* ----- 시그니처: 움츠림 → 솟아 앞으로 오며 180° → 카드 셋이 계단 박자로 → settle ----- */
  function cardTextures(it) {
    if (cardTex[it.app.slug]) return cardTex[it.app.slug];
    var list = it.app.shots.slice(0, 3).map(function (src) { return texFrom(src); });
    list.ready = Promise.all(list.map(function (t) { return t.userData.ready; }));
    cardTex[it.app.slug] = list;
    return list;
  }
  function engraving(it) {
    if (it.engraved) return;
    it.engraved = true;
    var N = 1024, c = document.createElement('canvas'); c.width = c.height = N;
    var x = c.getContext('2d'), t = tonesOf(it.base);
    var lum = srgb(it.base); lum = 0.2126 * lum.r + 0.7152 * lum.g + 0.0722 * lum.b;
    var dark = lum < 0.62;
    x.fillStyle = hexOf(t[1]); x.fillRect(0, 0, N, N);
    var cut = dark ? hexOf(it.base.clone().lerp(WHITE, 0.86)) : hexOf(shadeOf(it.base, 0.52, '#3A3650', 0.2));
    // 각인 글자 대비는 WCAG AA(4.5:1) 아래로 내려가지 않게 바탕에서 멀어지는 쪽으로 민다
    cut = enoughContrast(cut, hexOf(t[1]), dark);
    var lip = dark ? hexOf(shadeOf(it.base, 0.55, '#000000', 0)) : '#FFFFFF';
    function engrave(draw) {
      x.save(); x.translate(0, dark ? 2.5 : 3.5); x.fillStyle = lip; x.strokeStyle = lip; draw(); x.restore();
      x.fillStyle = cut; x.strokeStyle = cut; draw();
    }
    // 안쪽 테(초타원)
    engrave(function () {
      x.lineWidth = 5; x.beginPath();
      squirclePts(N * 0.84, N * 0.84, 128).forEach(function (p, k) { var px = N / 2 + p.x, py = N / 2 + p.y; if (k) x.lineTo(px, py); else x.moveTo(px, py); });
      x.closePath(); x.stroke();
    });
    var fam = ' ' + FONT;
    var nameSize = 132;
    x.font = '700 ' + nameSize + fam;
    while (x.measureText(it.app.name).width > N * 0.7 && nameSize > 60) { nameSize -= 4; x.font = '700 ' + nameSize + 'px' + fam; }
    x.font = '700 ' + nameSize + 'px' + fam;
    x.textAlign = 'center'; x.textBaseline = 'alphabetic';
    // 한 줄 소개: 낱말 단위로 두세 줄
    var subSize = 70;
    x.font = '500 ' + subSize + 'px' + fam;
    var words = it.app.subtitle.split(' '), lines = [], cur = '';
    words.forEach(function (w) { var tryL = cur ? cur + ' ' + w : w; if (x.measureText(tryL).width > N * 0.66 && cur) { lines.push(cur); cur = w; } else cur = tryL; });
    if (cur) lines.push(cur);
    var lineH = subSize * 1.34, blockH = nameSize + 64 + lines.length * lineH;
    var y0 = N / 2 - blockH / 2 + nameSize * 0.82;
    engrave(function () {
      x.font = '700 ' + nameSize + 'px' + fam; x.fillText(it.app.name, N / 2, y0);
      x.fillRect(N / 2 - 46, y0 + 40, 92, 6);
      x.font = '500 ' + subSize + 'px' + fam;
      lines.forEach(function (l, k) { x.fillText(l, N / 2, y0 + 64 + subSize + k * lineH); });
    });
    var tex = keep(new THREE.CanvasTexture(c));
    tex.colorSpace = THREE.SRGBColorSpace; tex.anisotropy = Math.min(8, renderer.capabilities.getMaxAnisotropy());
    tex.minFilter = THREE.LinearMipmapLinearFilter;
    it.engraveTex = tex;
    var bm = toon({ map: tex, fade: it.fadeU, recvU: it.recvU });
    it.pivot.children[0].userData.body.material[2] = bm;
  }
  var openByKey = false;
  function select(it) {
    if (current || it.cloth || dead || it.state !== 'seated') return;
    openByKey = !!lastKey && Date.now() - lastKey < 300;
    return claim().then(function (release) {
      var done = function () { release(); };
      if (dead || current || it.state !== 'seated') { release(); return; }
      current = it; it.state = 'flying';
      ++it.hTok; stopKey('h' + it.i);
      engraving(it);
      var tx = cardTextures(it);
      cards.forEach(function (cd, k) { cd.mat.uniforms.uMap.value = tx[k] || null; cd.c = 0; });
      hitsEl.inert = true;
      say(it.app.name + '. ' + it.app.subtitle);
      // 이 언어에 소개 페이지가 없으면 자세히 보기를 숨긴다
      moreEl.hidden = !it.app.href;
      moreEl.href = it.app.href || '#';
      moreEl.setAttribute('aria-label', UI.moreLabel.replace('{name}', it.app.name));
      spotTo(null);
      var st = it.st;
      if (reduced) {
        return tx.ready.then(function () {
          return crossfade(function () {
            it.flyFromY = 0; st.y = 0; st.sx = st.sy = st.sz = 1; st.fly = 1; it.recvU.value = 0;
            cards.forEach(function (cd) { cd.c = 1; });
            shared.fade.value = FADE; it.fanH = 0;
          });
        }).then(function () { it.state = 'stage'; openUI(); }).then(done, done);
      }
      sfx('crouch');
      var ax = st.sx, ay = st.sy;
      return drive(BEAT.crouch, function (t) {
        var e = Ease.outCubic(t);
        st.sx = st.sz = lerp(ax, BEAT.crouchS[0], e); st.sy = lerp(ay, BEAT.crouchS[1], e);
      }).then(function () { return Promise.race([tx.ready, wait(0.4)]); }).then(function () {
        if (dead) return;
        it.flyFromY = st.y; st.y = 0; st.sx = st.sy = st.sz = 1; it.recvU.value = 0;
        sfx('whoosh');
        var f0 = shared.fade.value;
        drive(BEAT.veil, function (t) { shared.fade.value = lerp(f0, FADE, Ease.outCubic(t)); });
        fanHover(it, 0);
        var fly = drive(BEAT.fly, function (t) { st.fly = t; });
        var cs = cards.map(function (cd, k) {
          return drive(BEAT.card, function (t) { cd.c = t; }, { delay: BEAT.cards[k], onStart: function () { sfx('card', k); } });
        });
        return Promise.all([fly].concat(cs));
      }).then(function () { if (dead) return; it.state = 'stage'; openUI(); }).then(done, done);
    });
  }
  function openUI() {
    wrap.classList.add('is-open');
    moreEl.tabIndex = 0; closeEl.tabIndex = 0;
    if (openByKey) moreEl.focus({ preventScroll: true });
  }
  function closeUI() {
    wrap.classList.remove('is-open');
    moreEl.tabIndex = -1; closeEl.tabIndex = -1;
  }
  function restore() {
    if (!current) return;
    return claim().then(function (release) {
      var it = current;
      if (!it || dead) { release(); return; }
      var st = it.st, viaKey = lastKey && Date.now() - lastKey < 1200;
      closeUI();
      var finishUp = function () {
        it.state = 'seated'; current = null;
        hitsEl.inert = false;
        if (viaKey) {
          // 마우스로 열고 Esc 로 닫으면 단추가 이미 초점을 쥐고 있어 focus 가 다시 오지 않는다.
          // 초점 테는 떠오른 타일 자리에 서므로, 초점 = 호버 반응을 여기서 직접 건다.
          var tok0 = it.hTok;
          it.hit.focus({ preventScroll: true });
          if (it.hTok === tok0 && it.hit.matches(':focus-visible')) hoverIn(it);
        }
        requestRender();
        release();
      };
      if (reduced) {
        return crossfade(function () {
          st.fly = 0; st.spin = 0; it.flyFromY = 0; st.y = 0; it.recvU.value = 1;
          cards.forEach(function (cd) { cd.c = 0; });
          shared.fade.value = 0;
        }).then(finishUp, finishUp);
      }
      sfx('rewind');
      // 스핀은 가까운 반 바퀴로 접어 둔다(되감을 때 한 바퀴 더 돌지 않게)
      var sp0 = Math.atan2(Math.sin(st.spin), Math.cos(st.spin));
      st.spin = sp0;
      // 카드: 역순, 점점 빨라지는 계단으로 빨려 들어간다
      var cs = [2, 1, 0].map(function (k, j) {
        return drive(BEAT.cardBack, function (t) { cards[k].c = 1 - t; }, { delay: BEAT.cardsBack[j] });
      });
      // 타일: 같은 곡선을 s 1 → 0 으로, 빠르게. 옅은 잔상 셋이 늦게 따라온다.
      ghostItem = it; ghostClock = 0;
      var gT = BEAT.flyBack + BEAT.ghosts[2] + 0.02;
      var gh = drive(gT, function (t) { ghostClock = t * gT; }, { delay: BEAT.flyBackAt });
      var fly = drive(BEAT.flyBack, function (t) { st.fly = 1 - t; st.spin = sp0 * (1 - t); }, { delay: BEAT.flyBackAt });
      var f0 = shared.fade.value;
      drive(BEAT.veil, function (t) { shared.fade.value = f0 * (1 - Ease.inQuad(t)); }, { delay: BEAT.flyBackAt + 0.08 });
      return fly.then(function () {
        if (dead) return;
        st.fly = 0; st.spin = 0; st.y = it.flyFromY; it.flyFromY = 0; it.recvU.value = 1;
        st.sx = st.sz = BEAT.crouchS[0]; st.sy = BEAT.crouchS[1];
        sfx('thud'); plinthPunch(it, 0.7);
        var y0 = st.y;
        var down = y0 > 0.01 ? drive(0.12, function (t) { st.y = y0 * (1 - Ease.inQuad(t)); }) : Promise.resolve();
        return Promise.all([down, squashSeq(st, BEAT.touch), gh].concat(cs));
      }).then(function () {
        ghostClock = -1; ghostItem = null; st.y = 0;
        shared.fade.value = 0;
        if (it.hovered && !viaKey) { it.state = 'seated'; }
      }).then(finishUp, finishUp);
    });
  }
  // 동작 줄이기: 지금 장면을 떠서 덮고, 장면을 바꾼 뒤 뜬 그림만 걷는다(빈 화면을 거치지 않게)
  function crossfade(apply) {
    return new Promise(function (res) {
      applyAll(); renderer.render(scene, camera);
      snapEl.width = canvas.width; snapEl.height = canvas.height;
      var x = snapEl.getContext('2d');
      x.drawImage(canvas, 0, 0);
      snapEl.style.opacity = '1';
      apply();
      applyAll(); renderer.render(scene, camera);
      drive(BEAT.snapFade, function (t) { snapEl.style.opacity = (1 - t).toFixed(3); }, { key: 'snap' }).then(res);
    });
  }

  /* ----- 무대에서 타일 돌리기(끌면 돌고, 놓으면 가까운 면으로 settle. 탭하면 한 번 뒤집힌다) ----- */
  var drag = null;
  on(spinEl, 'pointerdown', function (e) {
    if (!current || current.state !== 'stage') return;
    spinEl.setPointerCapture(e.pointerId);
    stopKey('spin');
    drag = { id: e.pointerId, x: e.clientX, s0: current.st.spin, moved: false };
  });
  on(spinEl, 'pointermove', function (e) {
    if (!drag || e.pointerId !== drag.id || !current) return;
    var dx = e.clientX - drag.x;
    if (Math.abs(dx) > 4) drag.moved = true;
    current.st.spin = drag.s0 + dx * PI / Math.max(160, SL.tile.size * 1.1);
    requestRender();
  });
  function endSpin(e) {
    if (!drag || e.pointerId !== drag.id || !current) { drag = null; return; }
    var st = current.st, s0 = st.spin, target;
    if (!drag.moved) target = Math.round(s0 / PI) * PI + PI;
    else target = Math.round(s0 / PI) * PI;
    drag = null;
    if (reduced) { st.spin = target; requestRender(); return; }
    sfx('tap');
    drive(BEAT.spin, function (t) { st.spin = lerp(s0, target, Ease.settle(t)); }, { key: 'spin' });
  }
  on(spinEl, 'pointerup', endSpin);
  on(spinEl, 'pointercancel', endSpin);

  /* ----- 입력 ----- */
  var lastKey = 0;
  on(document, 'keydown', function (e) {
    lastKey = Date.now();
    if (e.key === 'Escape' && current) { e.preventDefault(); restore(); }
  });
  on(backEl, 'click', function () { restore(); });
  on(closeEl, 'click', function () { restore(); });
  on(moreEl, 'click', function (e) { if (moreEl.getAttribute('href') === '#') e.preventDefault(); });
  on(soundEl, 'click', function () {
    if (!AC && !audioInit()) return;
    soundOn = !soundOn;
    if (AC.state === 'suspended') AC.resume();
    soundEl.setAttribute('aria-pressed', soundOn ? 'true' : 'false');
    wrap.classList.toggle('is-sound', soundOn);
    if (soundOn) sfx('on');
  });
  function say(t) { liveEl.textContent = ''; later(function () { liveEl.textContent = t; }, 30); }

  /* ----- 크기, 보임 ----- */
  function resize() {
    var r = wrap.getBoundingClientRect();
    var w = Math.max(1, Math.round(r.width)), h = Math.max(1, Math.round(r.height));
    if (w === view.w && h === view.h && L) return;
    view.w = w; view.h = h;
    DPR = Math.min(window.devicePixelRatio || 1, 2);
    renderer.setPixelRatio(DPR);
    renderer.setSize(w, h, false);
    shared.res.value.set(w * DPR, h * DPR);
    shared.edge.value = Math.min(96, w * 0.08) * DPR;
    build();
    requestRender();
  }
  var ro = new ResizeObserver(function () { resize(); });
  ro.observe(wrap);
  var io = new IntersectionObserver(function (es) { inView = es[0].isIntersecting; if (inView) kick(); });
  io.observe(wrap);
  on(document, 'visibilitychange', function () { visible = !document.hidden; if (visible) kick(); });

  resize();
  // 첫 그림을 미리 컴파일해 첫 동작에서 멈칫하지 않게
  // 숨어 있는 무대 물건(카드, 잔상, 그림자 받이)도 같이 컴파일해 둔다
  try {
    cards.forEach(function (cd) { cd.group.visible = true; });
    ghosts.forEach(function (g) { g.visible = true; g.material.uniforms.uMap.value = released[0].iconTex; });
    catcher.visible = true;
    renderer.compile(scene, camera);
  } catch (e) { /* 건너뛴다 */ }
  cards.forEach(function (cd) { cd.group.visible = false; });
  ghosts.forEach(function (g) { g.visible = false; });
  catcher.visible = false;
  requestRender();
  // 대기 중에는 아무것도 저절로 움직이지 않는다(시그니처 2절). 시안의 천 들썩임은 뺐다
  intro();

  /* ----- 시험용 손잡이(촬영 스크립트가 쓴다) ----- */
  var api = {
    destroy: destroy,
    _t: {
      state: function () { return { current: current ? current.app.slug : null, states: items.map(function (it) { return it.state; }), motions: motions.length, spot: shared.spotAmt.value, lit: spot.it ? spot.it.app.slug : null }; },
      select: function (i) { return select(items[i]); },
      restore: function () { return restore(); }
    }
  };
  return api;

  function destroy() {
    if (dead) return;
    dead = true;
    if (raf) cancelAnimationFrame(raf); raf = 0;
    timers.forEach(function (id) { clearTimeout(id); }); timers.clear();
    offs.forEach(function (f) { f(); }); offs = [];
    ro.disconnect(); io.disconnect();
    motions = [];
    layoutTrash.forEach(function (x) { x.dispose(); }); layoutTrash = [];
    labelTrash.forEach(function (x) { x.dispose(); }); labelTrash = [];
    trash.forEach(function (x) { if (x && x.dispose) x.dispose(); }); trash = [];
    sun.shadow.map && sun.shadow.map.dispose();
    stageLight.shadow.map && stageLight.shadow.map.dispose();
    renderer.dispose();
    if (renderer.forceContextLoss) renderer.forceContextLoss();
    if (AC) { try { AC.close(); } catch (e) { /* 이미 닫힘 */ } AC = null; }
    if (bgEl) bgEl.innerHTML = '';
    root.innerHTML = '';
  }
}
