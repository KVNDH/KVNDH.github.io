// 허브 선반 입구. 허브 HTML 의 #shelf 와 #shelf-data 를 읽어 선반을 올린다.
// 허브의 로더(render.py SHELF_LOADER)가 WebGL 을 확인하고 벤토를 숨겨 자리를 잡아 둔 뒤(shelf-wait)에만 온다.
// 아이콘까지 준비되면 선반을 보이고(shelf-on), 올리다 실패하거나 늦거나 그림이 깨지면 벤토로 돌아간다.
import css from './shelf.css';
import { mount } from './shelf.js';

(function () {
  var body = document.body;
  var host = document.getElementById('shelf');
  var dataEl = document.getElementById('shelf-data');
  if (!host || !dataEl || host.dataset.on || host.dataset.off || !body.classList.contains('shelf-wait')) return;
  function off() {
    if (host.off) host.off();
    else { host.hidden = true; host.dataset.off = '1'; body.classList.remove('shelf-wait'); }
  }
  var data;
  try { data = JSON.parse(dataEl.textContent); } catch (e) { off(); return; }
  if (!data || !data.apps || !data.apps.length) { off(); return; }

  var style = document.createElement('style');
  style.textContent = css;
  document.head.appendChild(style);
  var bg = document.createElement('div');
  bg.className = 'shelf-bg';
  bg.setAttribute('aria-hidden', 'true');
  body.insertBefore(bg, body.firstChild);
  var inst = null;
  // 벤토로 돌아간다(선반은 다시 오지 않는다)
  function fallBack() {
    if (inst) { try { inst.destroy(); } catch (e) { /* 이미 정리됨 */ } inst = null; }
    host.innerHTML = '';
    bg.remove(); style.remove();
    body.classList.remove('shelf-on');
    delete host.dataset.on;
    if (__SHELF_TEST__) window.__shelf = null;
    off();
  }
  try { inst = mount(host, data, bg, { onLost: fallBack }); } catch (e) { inst = null; if (window.console) console.warn(e); }
  if (!inst) { fallBack(); return; }
  host.dataset.on = '1';
  if (__SHELF_TEST__) window.__shelf = inst;
  var late = new Promise(function (r) { setTimeout(function () { r(false); }, 4000); });
  Promise.race([inst.ready, late]).then(function (ok) {
    if (!inst) return;
    if (!ok || host.dataset.off) { fallBack(); return; }
    body.classList.add('shelf-on');
    body.classList.remove('shelf-wait');
    inst.start();
  });
})();
