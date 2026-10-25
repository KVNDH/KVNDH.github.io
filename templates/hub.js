(function(){
  // 허브 화첩: 지금 보는 앱 번호(오른쪽 위 버밀리언 점은 여기 한 곳)와 크게 보기
  var D=JSON.parse(document.getElementById('canvas-data').textContent),P=D.plates,U=D.ui;
  var body=document.body,root=document.documentElement,now=document.querySelector('.now'),v=document.querySelector('.viewer'),last=null;
  var pieces=[].slice.call(document.querySelectorAll('.piece'));
  function esc(s){return String(s).replace(/[&<>"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})}
  var cur=-2;
  function mark(){
    var vh=innerHeight,best=-1,d=1e9;
    if(scrollY>vh*.5)pieces.forEach(function(p,i){var r=p.querySelector('.slot').getBoundingClientRect(),c=Math.abs(r.top+r.height/2-vh/2);if(c<d){d=c;best=i}});
    if(best===cur)return;cur=best;now.dataset.on=best>=0?'1':'0';
    if(best>=0){var a=P[best];now.querySelector('b').textContent=a.no+' / '+U.total+'  '+a.name}
  }
  addEventListener('scroll',mark,{passive:true});addEventListener('resize',mark);mark();
  function open(i){
    var a=P[i],img=v.querySelector('.vslot img');last=document.activeElement;
    v.querySelector('.vsheet').scrollTop=0; // 앞서 본 앱에서 내린 자리가 남으면 닫기 단추가 위로 숨는다
    img.src=a.big;img.alt='';
    v.querySelector('.vno').textContent='No. '+a.no+' / '+U.total;
    v.querySelector('h2').textContent=a.name;v.querySelector('.sub').textContent=a.sub;v.querySelector('.hook').textContent=a.hook;
    v.querySelector('ul').innerHTML=a.bullets.map(function(b){return '<li>'+esc(b)+'</li>'}).join('');
    v.querySelector('.acts').innerHTML='<a class="btn" href="'+esc(a.store)+'" aria-label="'+esc(a.storeLabel)+'">App Store ↗</a>'+
      (a.href?'<a class="lnk" href="'+esc(a.href)+'">'+esc(U.more)+'</a><a class="lnk" href="'+esc(a.support)+'">'+esc(U.support)+'</a>':'');
    v.setAttribute('aria-label',a.name);
    body.dataset.active=i;body.classList.add('viewing');root.classList.add('lock');v.removeAttribute('inert');v.setAttribute('aria-hidden','false');
    v.querySelector('.vclose').focus({preventScroll:true});
  }
  function close(){if(!body.classList.contains('viewing'))return;body.classList.remove('viewing');root.classList.remove('lock');v.setAttribute('aria-hidden','true');v.setAttribute('inert','');if(last)last.focus({preventScroll:true})}
  [].forEach.call(document.querySelectorAll('[data-open]'),function(b){b.addEventListener('click',function(){open(+b.dataset.open)})});
  v.addEventListener('click',function(e){if(e.target===v)close()});
  v.querySelector('.vclose').addEventListener('click',close);
  addEventListener('keydown',function(e){
    if(!body.classList.contains('viewing'))return;
    if(e.key==='Escape'){e.preventDefault();close();return}
    if(e.key==='Tab'){ // 크게 보기 안에서만 초점이 돈다
      var f=[].slice.call(v.querySelectorAll('button,a[href]')),a0=f[0],a1=f[f.length-1];
      if(e.shiftKey&&document.activeElement===a0){e.preventDefault();a1.focus()}
      else if(!e.shiftKey&&document.activeElement===a1){e.preventDefault();a0.focus()}
      else if(f.indexOf(document.activeElement)<0){e.preventDefault();a0.focus()}
    }
  });
  window.__open=open;window.__close=close;
})();
