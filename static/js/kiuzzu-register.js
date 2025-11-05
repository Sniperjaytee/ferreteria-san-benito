(function(){
  var tp=document.getElementById('togglePassword');
  var tcp=document.getElementById('toggleConfirmPassword');
  var p=document.getElementById('password');
  var cp=document.getElementById('confirmPassword');
  // login page toggles (if present)
  var tlp = document.getElementById('toggleLoginPassword');
  var lp = document.getElementById('loginPassword');
  function toggle(input,icon){
    if(!input||!icon) return;
    var i=icon.querySelector('i');
    icon.addEventListener('click',function(e){
      e.preventDefault();
      if(input.type==='password'){
        input.type='text';
        if(i){i.classList.remove('fa-eye');i.classList.add('fa-eye-slash');}
      }else{
        input.type='password';
        if(i){i.classList.remove('fa-eye-slash');i.classList.add('fa-eye');}
      }
      input.focus();
    });
  }
  toggle(p,tp);
  toggle(cp,tcp);
  // support login toggle
  toggle(lp, tlp);

  // Hacer clickeable todo el grupo para enfocar el input
  document.querySelectorAll('.auth-page .input-group').forEach(function(g){
    g.addEventListener('click', function(){
      var input=g.querySelector('.input-field');
      if(input){ input.focus(); }
    });
  });
})();
