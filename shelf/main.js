// 허브 선반 입구. 허브 HTML 의 #shelf 와 #shelf-data 를 읽어 선반을 올린다.
// WebGL 이 없거나 올리다 실패하면 아무것도 바꾸지 않는다(벤토가 그대로 남는다).
import css from './shelf.css';
import { mount } from './shelf.js';

(function () {
  var host = document.getElementById('shelf');
  var dataEl = document.getElementById('shelf-data');
  if (!host || !dataEl || host.dataset.on) return;
  var data;
  try { data = JSON.parse(dataEl.textContent); } catch (e) { return; }
  if (!data || !data.apps || !data.apps.length || !webgl()) return;

  var style = document.createElement('style');
  style.textContent = css;
  document.head.appendChild(style);
  var bg = document.createElement('div');
  bg.className = 'shelf-bg';
  bg.setAttribute('aria-hidden', 'true');
  document.body.insertBefore(bg, document.body.firstChild);
  host.hidden = false;
  document.body.classList.add('shelf-on');
  var inst = null;
  try { inst = mount(host, data, bg); } catch (e) { inst = null; if (window.console) console.warn(e); }
  if (!inst) {
    host.hidden = true;
    host.innerHTML = '';
    document.body.classList.remove('shelf-on');
    bg.remove(); style.remove();
    return;
  }
  host.dataset.on = '1';
  window.__shelf = inst;

  function webgl() {
    try {
      var c = document.createElement('canvas');
      var gl = c.getContext('webgl2') || c.getContext('webgl');
      if (!gl) return false;
      var lose = gl.getExtension('WEBGL_lose_context');
      if (lose) lose.loseContext();
      return true;
    } catch (e) { return false; }
  }
})();
