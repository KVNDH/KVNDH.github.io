(function(){
  // 언어 고르기: Esc 와 바깥 누르기로 닫는다
  var lang=document.querySelector('.lang');
  if(lang){
    addEventListener('keydown',function(e){if(e.key==='Escape'&&lang.open){lang.open=false;lang.querySelector('summary').focus()}});
    addEventListener('click',function(e){if(lang.open&&!lang.contains(e.target))lang.open=false});
  }
  // 목차: 넓은 화면(901px 부터)에서는 늘 펼치고 좁은 화면에서는 접어 둔다
  var toc=document.querySelector('.toc details');
  if(toc){var wide=matchMedia('(min-width:901px)'),fit=function(){toc.open=wide.matches};fit();wide.addEventListener('change',fit)}
  // 지원 답 주소: #q7 로 오면 7번 답을 연다
  function reveal(){var d=location.hash&&document.getElementById(decodeURIComponent(location.hash.slice(1)));if(d&&d.tagName==='DETAILS')d.open=true}
  reveal();addEventListener('hashchange',reveal);
  // 인쇄: 닫힌 지원 답을 모두 펼쳤다가 인쇄가 끝나면 그 답만 다시 닫는다
  var shut=[];
  addEventListener('beforeprint',function(){shut=[].filter.call(document.querySelectorAll('.faq details'),function(d){return !d.open});shut.forEach(function(d){d.open=true})});
  addEventListener('afterprint',function(){shut.forEach(function(d){d.open=false});shut=[]});
})();
