(function(){
  // 언어 고르기: Esc 와 바깥 누르기로 닫는다
  var lang=document.querySelector('.lang');
  if(lang){
    addEventListener('keydown',function(e){if(e.key==='Escape'&&lang.open){lang.open=false;lang.querySelector('summary').focus()}});
    addEventListener('click',function(e){if(lang.open&&!lang.contains(e.target))lang.open=false});
  }
})();
