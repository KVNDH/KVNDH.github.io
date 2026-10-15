// kvndh 화첩 판. 고정 WebGL 장면이 DOM 의 자리([data-plate])를 따라 두께 있는 아이콘 판을 놓는다.
// 허브: 첫 화면에서 판들이 위에서 1-2-3-4 로 쌓인 둥근 더미로 돌다가, 스크롤하면 흩어져 각자 자리로 내려간다.
//       맨 위 판(출시된 첫 앱)만 천천히 첫 자리로 내려오고, 나머지는 제목 위를 지나지 않게 먼저 빠진다.
// 소개, 지원, 개인정보: 판 하나가 자리에 떠서 마우스로 기울고 끌면 돈다.
// 페이지 머리의 로더(render.py CANVAS_LOADER)가 동작 줄이기와 WebGL 을 확인한 뒤(gl-wait)에만 온다.
// 실패하면 gl-off 로 돌아가 DOM 의 멈춘 그림(같은 배치)이 보인다.
import {
  WebGLRenderer, Scene, PerspectiveCamera, Mesh, Shape, ExtrudeGeometry, PlaneGeometry,
  MeshPhysicalMaterial, MeshBasicMaterial, Texture, CanvasTexture, SRGBColorSpace, Color,
  DirectionalLight, PMREMGenerator, Group, MathUtils
} from 'three';
import { RoomEnvironment } from 'three/examples/jsm/environments/RoomEnvironment.js';

const root = document.documentElement;
const qs = new URLSearchParams(location.search);

function fallback(why) {
  root.classList.remove('gl-wait', 'gl-on');
  root.classList.add('gl-off');
  root.dataset.gl = why;
}

let data = null;
try { data = JSON.parse(document.getElementById('canvas-data').textContent); } catch (e) { data = null; }
// 로더가 이미 포기했으면(gl-off) 아무것도 하지 않는다
if (!root.classList.contains('gl-wait') || root.classList.contains('gl-off')) data = null;
else if (!data || !data.plates || !data.plates.length) fallback('nodata');
else { try { start(data); } catch (e) { console.error(e); fallback('error'); } }

function squircle(n = 5, pts = 72) {
  const s = new Shape();
  for (let i = 0; i <= pts; i++) {
    const t = (i / pts) * Math.PI * 2, c = Math.cos(t), si = Math.sin(t);
    const x = 0.5 * Math.sign(c) * Math.pow(Math.abs(c), 2 / n);
    const y = 0.5 * Math.sign(si) * Math.pow(Math.abs(si), 2 / n);
    i ? s.lineTo(x, y) : s.moveTo(x, y);
  }
  return s;
}

function plateGeometry(mobile) {
  const depth = 0.1, bt = 0.035, bs = 0.03;
  const g = new ExtrudeGeometry(squircle(5, mobile ? 48 : 72), {
    depth, bevelEnabled: true, bevelThickness: bt, bevelSize: bs, bevelSegments: mobile ? 2 : 4, curveSegments: 4
  });
  g.translate(0, 0, -(depth / 2));          // 판 가운데가 0
  // 그룹 0 = 뚜껑(앞뒤), 그룹 1 = 옆면. 뚜껑 앞 절반이 뒷면, 뒤 절반이 앞면이다.
  const caps = g.groups[0], side = g.groups[1], half = caps.count / 2;
  const pos = g.attributes.position, uv = g.attributes.uv;
  for (let i = caps.start + half; i < caps.start + caps.count; i++) uv.setXY(i, pos.getX(i) + 0.5, pos.getY(i) + 0.5);
  for (let i = caps.start; i < caps.start + half; i++) uv.setXY(i, 0.5 - pos.getX(i), pos.getY(i) + 0.5);
  uv.needsUpdate = true;
  g.clearGroups();
  g.addGroup(caps.start, half, 2);           // 뒷면: 원화 뒷면 도장
  g.addGroup(caps.start + half, half, 1);    // 앞면: 아이콘
  g.addGroup(side.start, side.count, 0);     // 옆면과 모서리: 유약 몸
  return g;
}

function shadowTexture() {
  const c = document.createElement('canvas'); c.width = c.height = 128;
  const x = c.getContext('2d'), gr = x.createRadialGradient(64, 64, 4, 64, 64, 62);
  gr.addColorStop(0, 'rgba(26,26,26,.55)'); gr.addColorStop(.55, 'rgba(26,26,26,.18)'); gr.addColorStop(1, 'rgba(26,26,26,0)');
  x.fillStyle = gr; x.fillRect(0, 0, 128, 128);
  return new CanvasTexture(c);
}

// 판 뒷면: 몸 색 위에 원화 뒷면처럼 번호와 이름을 찍는다(출시 전 앱은 이름 없이)
function backTexture(color, no, name) {
  const c = document.createElement('canvas'); c.width = c.height = 256;
  const x = c.getContext('2d'); x.fillStyle = color; x.fillRect(0, 0, 256, 256);
  const col = new Color(color), lum = 0.2126 * col.r + 0.7152 * col.g + 0.0722 * col.b;
  x.fillStyle = lum > 0.45 ? 'rgba(26,26,26,.62)' : 'rgba(255,255,255,.75)';
  x.strokeStyle = x.fillStyle; x.lineWidth = 2;
  x.textAlign = 'center';
  x.font = '800 30px -apple-system,system-ui,sans-serif'; x.fillText('kvndh', 128, 112);
  x.font = '600 15px ui-monospace,Menlo,monospace';
  if (no) x.fillText('No. ' + no, 128, 146);
  if (name) x.fillText(name.length > 18 ? name.slice(0, 17) + '…' : name, 128, 168);
  x.strokeRect(72, 76, 112, 108);
  const t = new CanvasTexture(c); t.colorSpace = SRGBColorSpace; return t;
}

function loadImage(src) {
  return new Promise((ok, bad) => { const im = new Image(); im.onload = () => ok(im); im.onerror = bad; im.src = src; });
}

// 판 옆면 색: 아이콘 가장자리 띠의 평균. 출시 전 앱은 흑백으로 바꿔 종이 쪽으로 흐리고 번지게 한다
function prepare(im, soon) {
  const s = document.createElement('canvas'); s.width = s.height = 64;
  const sx = s.getContext('2d', { willReadFrequently: true }); sx.drawImage(im, 0, 0, 64, 64);
  const px = sx.getImageData(0, 0, 64, 64).data;
  let r = 0, g = 0, b = 0, n = 0;
  for (let y = 0; y < 64; y++) for (let x = 0; x < 64; x++) {
    if (Math.min(x, y, 63 - x, 63 - y) >= 4) continue;
    const k = (y * 64 + x) * 4; r += px[k]; g += px[k + 1]; b += px[k + 2]; n++;
  }
  let edge = new Color(r / n / 255, g / n / 255, b / n / 255);
  let src = im;
  if (soon) {
    // 아이콘 속 글자(앱 이름)가 읽히지 않을 만큼 작게 줄였다가 두 번에 나눠 키운다
    const small = document.createElement('canvas'); small.width = small.height = 12;
    const smx = small.getContext('2d', { willReadFrequently: true }); smx.imageSmoothingQuality = 'high'; smx.drawImage(im, 0, 0, 12, 12);
    const d = smx.getImageData(0, 0, 12, 12), p = d.data;
    for (let k = 0; k < p.length; k += 4) {
      const l = 0.2126 * p[k] + 0.7152 * p[k + 1] + 0.0722 * p[k + 2];
      p[k] = l * 0.4 + 236 * 0.6; p[k + 1] = l * 0.4 + 235 * 0.6; p[k + 2] = l * 0.4 + 231 * 0.6;
    }
    smx.putImageData(d, 0, 0);
    const mid = document.createElement('canvas'); mid.width = mid.height = 48;
    const mx2 = mid.getContext('2d'); mx2.imageSmoothingQuality = 'high'; mx2.drawImage(small, 0, 0, 48, 48);
    const big = document.createElement('canvas'); big.width = big.height = 256;
    const bx = big.getContext('2d'); bx.imageSmoothingQuality = 'high'; bx.drawImage(mid, 0, 0, 256, 256);
    src = big;
    const l = 0.2126 * edge.r + 0.7152 * edge.g + 0.0722 * edge.b;
    edge = new Color(l, l, l).lerp(new Color('#ECEBE7'), 0.55);
  }
  return { src, edge };
}

const ease = t => t < 0 ? 0 : t > 1 ? 1 : t * t * (3 - 2 * t);
const clamp = (v, a, b) => Math.min(b, Math.max(a, v));
const pad = (v, n) => String(v).padStart(n, '0');

function start(data) {
  const hubPage = data.page === 'hub';
  const mobile = matchMedia('(max-width: 720px)').matches;
  const canvas = document.getElementById('gl');
  const renderer = new WebGLRenderer({ canvas, antialias: true, alpha: true, powerPreference: 'high-performance', preserveDrawingBuffer: qs.has('shot') });
  renderer.setPixelRatio(Math.min(devicePixelRatio || 1, mobile ? 1.5 : 2));
  renderer.setClearColor(0x000000, 0);
  renderer.outputColorSpace = SRGBColorSpace;

  const scene = new Scene();
  const pm = new PMREMGenerator(renderer);
  scene.environment = pm.fromScene(new RoomEnvironment(), 0.04).texture;
  pm.dispose();
  const key = new DirectionalLight(0xffffff, 1.1); key.position.set(-0.6, 1, 1.2); scene.add(key);

  const camera = new PerspectiveCamera(30, 1, 10, 20000);
  let vw = 0, vh = 0;
  function resize() {
    vw = innerWidth; vh = innerHeight;
    renderer.setSize(vw, vh, false);
    camera.aspect = vw / vh;
    camera.position.set(0, 0, (vh / 2) / Math.tan(MathUtils.degToRad(15)));
    camera.updateProjectionMatrix();
  }
  resize(); addEventListener('resize', resize);

  const geo = plateGeometry(mobile);
  const shadowGeo = new PlaneGeometry(1, 1), shTex = shadowTexture();
  const plates = data.plates;
  const slots = plates.map((_, i) => document.querySelector('[data-plate="' + i + '"]'));
  if (slots.some(s => !s)) throw new Error('plate slot missing');
  const vslot = document.querySelector('.vslot');
  const hub = document.querySelector('.cluster');
  const readouts = plates.map((_, i) => document.querySelector('[data-readout="' + i + '"]'));
  const maxAniso = Math.min(8, renderer.capabilities.getMaxAnisotropy());

  Promise.all(plates.map(a => loadImage(a.icon))).then(images => {
    const items = plates.map((a, i) => {
      const { src, edge } = prepare(images[i], a.soon);
      const t = new Texture(src); t.colorSpace = SRGBColorSpace; t.anisotropy = maxAniso; t.needsUpdate = true;
      const body = new MeshPhysicalMaterial({ color: edge.clone().lerp(new Color('#F4F2EE'), 0.18), roughness: 0.32, clearcoat: 1, clearcoatRoughness: 0.12, envMapIntensity: 0.9 });
      const face = new MeshPhysicalMaterial({ color: 0x1c1c1c, map: t, emissive: 0xffffff, emissiveMap: t, emissiveIntensity: a.soon ? 0.98 : 0.93, roughness: 0.5, clearcoat: 0.55, clearcoatRoughness: 0.08, envMapIntensity: 0.22 });
      const bodyHex = '#' + body.color.getHexString(SRGBColorSpace);
      const back = new MeshPhysicalMaterial({ map: backTexture(bodyHex, a.no || '', a.soon ? '' : a.name), roughness: 0.38, clearcoat: 0.8, clearcoatRoughness: 0.15, envMapIntensity: 0.8 });
      const g = new Group();
      g.add(new Mesh(geo, [body, face, back]));
      const sh = new Mesh(shadowGeo, new MeshBasicMaterial({ map: shTex, transparent: true, depthWrite: false, opacity: 0 }));
      scene.add(sh); scene.add(g);
      return { g, sh, i, soon: !!a.soon, pose: null, hover: 0, hoverT: 0, spin: 0, spinV: 0 };
    });

    // 입력: 마우스 기울기, 터치 끌기(스크롤은 막지 않는다), 끌어 돌리기
    let mx = 0, my = 0, tmx = 0, tmy = 0, lastTouch = null;
    addEventListener('pointermove', e => { if (e.pointerType === 'mouse') { tmx = e.clientX / vw * 2 - 1; tmy = e.clientY / vh * 2 - 1; } }, { passive: true });
    addEventListener('touchstart', e => { const t = e.touches[0]; lastTouch = { x: t.clientX, y: t.clientY }; }, { passive: true });
    addEventListener('touchmove', e => {
      const t = e.touches[0]; if (!lastTouch) return;
      tmx = clamp(tmx + (t.clientX - lastTouch.x) / vw * 3, -1, 1); tmy = clamp(tmy + (t.clientY - lastTouch.y) / vh * 1.5, -1, 1);
      lastTouch = { x: t.clientX, y: t.clientY };
    }, { passive: true });
    addEventListener('touchend', () => { lastTouch = null; }, { passive: true });
    slots.forEach((s, i) => {
      if (items[i].soon) return;
      s.addEventListener('pointerenter', () => { items[i].hoverT = 1; });
      s.addEventListener('pointerleave', () => { items[i].hoverT = 0; });
    });
    let drag = null;
    const viewerOpen = () => document.body.classList.contains('viewing');
    const active = () => items[+document.body.dataset.active || 0];
    function draggable(el, target) {
      el.addEventListener('pointerdown', e => { if (e.button) return; drag = { x: e.clientX, el, moved: 0 }; try { el.setPointerCapture(e.pointerId); } catch (_) {} });
      el.addEventListener('pointermove', e => {
        if (!drag || drag.el !== el) return;
        const p = target(), dx = e.clientX - drag.x;
        p.spinV = dx * 0.012; p.spin += p.spinV; drag.x = e.clientX; drag.moved += Math.abs(dx);
      });
      const end = () => { if (drag && drag.el === el) { el.dataset.dragged = drag.moved > 6 ? '1' : ''; drag = null; } };
      el.addEventListener('pointerup', end); el.addEventListener('pointercancel', end);
    }
    if (hubPage && vslot) draggable(vslot, active);
    if (!hubPage) draggable(slots[0], () => items[0]);

    root.classList.remove('gl-wait'); root.classList.add('gl-on');
    let last = performance.now(), time = 0;
    const N = items.length;
    // 더미의 줄: 위에서부터 1, 2, 3, 4 ... 맨 위가 출시된 첫 앱
    const rowOf = i => Math.floor((Math.sqrt(8 * i + 1) - 1) / 2);
    const ROWS = rowOf(N - 1) + 1;

    function plateShadow(p, P, strength) {
      const lift = clamp(P.z / 400, 0, 1);
      p.sh.visible = p.g.visible;
      p.sh.position.set(P.x + P.s * (0.05 + lift * 0.2), P.y - P.s * (0.08 + lift * 0.3), 0);
      p.sh.scale.set(P.s * (1.25 + lift * 0.6), P.s * (1.25 + lift * 0.6), 1);
      p.sh.material.opacity = (0.55 - lift * 0.35) * strength;
    }
    function place(p, P) {
      p.g.position.set(P.x, P.y, P.z);
      p.g.rotation.set(P.rx, P.ry, P.rz);
      p.g.scale.setScalar(P.s);
    }
    function readout(i, P) {
      const el = readouts[i]; if (!el) return;
      el.textContent = 'ROT ' + pad((Math.round(P.ry * 180 / Math.PI) % 360 + 360) % 360, 3) + '°  Z ' + pad(Math.max(0, Math.round(P.z)), 3);
    }

    function frameHub(dt) {
      const k = 1 - Math.exp(-dt * 10);
      // 첫 화면은 조금 내려도 그대로 두고(0.12 화면), 그 뒤에 흩어진다
      const sY = scrollY, heroP = clamp((sY - vh * 0.12) / (vh * 0.85), 0, 1.4);
      const hr = hub.getBoundingClientRect();
      const hcx = hr.left + hr.width / 2, hcy = hr.top + hr.height / 2;
      const heroSize = Math.min(hr.width * 0.2, hr.height / (ROWS + 0.4), mobile ? 76 : 116);
      const open = viewerOpen(), act = +document.body.dataset.active;

      items.forEach((p, i) => {
        const isAct = open && act === i;
        const r = (isAct ? vslot : slots[i]).getBoundingClientRect();
        const size = r.width;
        // 자리 자세: 화면 가운데에 오면 바로 서고, 아래에서 올라올 때는 깊은 곳에서 돌며 떠오른다
        const c = (r.top + r.height / 2 - vh / 2) / vh;
        const enter = ease(clamp((c - 0.04) / 0.62, 0, 1)), leave = ease(clamp(-c / 0.8, 0, 1));
        p.hover += (p.hoverT - p.hover) * k;
        const slot = {
          x: r.left + r.width / 2 - vw / 2,
          y: vh / 2 - (r.top + r.height / 2),
          z: enter * 170 + leave * 50 + p.hover * 40 + size * 0.06,
          rx: -enter * 0.7 + leave * 0.35 + my * 0.22 + (isAct ? 0 : 0.08),
          ry: enter * Math.PI * 0.72 * (i % 2 ? -1 : 1) + mx * 0.32 + p.hover * 0.12,
          rz: enter * 0.25 * (i % 2 ? 1 : -1),
          s: size
        };
        if (isAct) { p.spinV *= 0.94; if (!drag) p.spin += dt * 0.25 + p.spinV; slot.ry += p.spin; slot.rx = my * 0.18 + 0.05; slot.z = 30; }
        else { p.spin *= 0.9; }
        // 첫 화면: 아이콘 판을 얼음집 벽돌처럼 쌓은 둥근 더미. 천천히 좌우로 돈다
        const row = rowOf(i), first = row * (row + 1) / 2, cnt = Math.min(row + 1, N - first);
        const fromBottom = ROWS - 1 - row;
        const Rc = heroSize * 2.1, step = heroSize * 1.1 / Rc;
        const G = Math.sin(time * 0.35) * 0.28 + mx * 0.35;
        const a0 = (i - first - (cnt - 1) / 2) * step, aa = a0 + G;
        const hero = {
          x: hcx - vw / 2 + Math.sin(aa) * Rc * (1 - fromBottom * 0.05),
          y: vh / 2 - hcy + ((ROWS - 1) / 2 - row) * heroSize * 0.98 + Math.sin(time * 1.1 + i * 1.7) * 3,
          z: (Math.cos(aa) - 1) * Rc - fromBottom * heroSize * 0.12 + 40,
          rx: -fromBottom * 0.16 + my * 0.2, ry: aa, rz: 0, s: heroSize
        };
        // 맨 위 판(첫 앱)만 천천히 내려가고, 나머지는 첫 앱 글이 화면에 들어오기 전에 화면 밖 자기 자리로 빠진다
        const m = open ? 1 : i === 0 ? ease(clamp(heroP * 1.25, 0, 1)) : ease(clamp(heroP * 2.6 - (i - 1) * 0.04, 0, 1));
        const T = {};
        for (const key of ['x', 'y', 'z', 'rx', 'ry', 'rz', 's']) T[key] = hero[key] + (slot[key] - hero[key]) * m;
        if (!p.pose) p.pose = { ...T };
        const P = p.pose, kk = isAct ? 1 - Math.exp(-dt * 8) : 1 - Math.exp(-dt * 15);
        for (const key in T) P[key] += (T[key] - P[key]) * kk;
        p.g.visible = !(open && !isAct) && Math.abs(P.y) < vh * 1.2;
        place(p, P);
        plateShadow(p, P, 0.35 + 0.65 * m);
        if (Math.abs(c) < 1.2) readout(i, P);
      });
    }

    // 판 하나: 처음엔 깊은 곳에서 돌며 떠올라 자리에 서고, 스크롤하면 살짝 기울며 자리를 따라간다
    function frameSingle(dt) {
      const p = items[0], r = slots[0].getBoundingClientRect(), size = r.width;
      const c = (r.top + r.height / 2 - vh / 2) / vh;
      const intro = 1 - ease(clamp(time / 1.3, 0, 1));
      p.spinV *= 0.94; if (!drag) p.spin += p.spinV; p.spin *= drag ? 1 : 0.985;
      const T = {
        x: r.left + r.width / 2 - vw / 2,
        y: vh / 2 - (r.top + r.height / 2),
        z: intro * 220 + size * 0.06 + 20,
        rx: -intro * 0.6 + my * 0.2 + c * 0.35 + 0.06,
        ry: intro * Math.PI * 0.8 + mx * 0.35 - c * 0.5 + Math.sin(time * 0.5) * 0.1 + p.spin,
        rz: intro * 0.2,
        s: size
      };
      if (!p.pose) p.pose = { ...T };
      const P = p.pose, kk = 1 - Math.exp(-dt * 15);
      for (const key in T) P[key] += (T[key] - P[key]) * kk;
      p.g.visible = Math.abs(P.y) < vh * 1.2;
      place(p, P);
      plateShadow(p, P, 1);
      readout(0, P);
    }

    function frame(now) {
      const dt = Math.min(0.05, (now - last) / 1000); last = now;
      time += dt;
      const k = 1 - Math.exp(-dt * 10);
      mx += (tmx - mx) * k; my += (tmy - my) * k;
      if (lastTouch === null) { tmx *= 0.985; tmy *= 0.985; }
      if (hubPage) frameHub(dt); else frameSingle(dt);
      renderer.render(scene, camera);
      requestAnimationFrame(frame);
    }
    requestAnimationFrame(frame);
  }).catch(e => { console.error(e); fallback('error'); });
}
