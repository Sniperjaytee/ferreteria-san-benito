(function(){
  var tp=document.getElementById('togglePassword');
  var tcp=document.getElementById('toggleConfirmPassword');
  var p=document.getElementById('password');
  var cp=document.getElementById('confirmPassword');
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

  // Hacer clickeable todo el grupo para enfocar el input
  document.querySelectorAll('.auth-page .input-group').forEach(function(g){
    g.addEventListener('click', function(){
      var input=g.querySelector('.input-field');
      if(input){ input.focus(); }
    });
  });

  // Mostrar animación para mensajes de validación: aparecer, esperar 5s y desaparecer
  function animateValidationMessages(){
    var messages = document.querySelectorAll('.auth-page .validation-message');
    var translations = {
      "The two password fields didn't match.": "Las dos contraseñas no coinciden.",
      "This password is too short. It must contain at least 8 characters.": "La contraseña es demasiado corta. Debe contener al menos 8 caracteres.",
      "This password is too common.": "Esta contraseña es demasiado común.",
      "This password is entirely numeric.": "Esta contraseña es totalmente numérica.",
      "Enter a valid email address.": "Introduce una dirección de correo electrónico válida.",
      "This field is required.": "Este campo es obligatorio.",
      "The password is too similar to the email address.": "La contraseña es demasiado similar al correo electrónico.",
      "The password is too similar to the username.": "La contraseña es demasiado similar al nombre de usuario.",
      "The password is too similar to the first name.": "La contraseña es demasiado similar al nombre.",
      "The password is too similar to the last name.": "La contraseña es demasiado similar al apellido.",
      // generic start of the sentence (in case the library composes it differently)
      "The password is too similar to the": "La contraseña es demasiado similar a "
    };

    function normalizeSpacing(s){
      if(!s) return s;
      return s.replace(/\.([A-Za-zÀ-ÖØ-öø-ÿÑñ])/g, '. $1');
    }

    function translate(t){
      if(!t) return t;
      var out = normalizeSpacing(t);
      Object.keys(translations).forEach(function(k){ if(out.indexOf(k)!==-1) out = out.replace(k, translations[k]); });
      return out;
    }

    messages.forEach(function(msg){
      // si el elemento tiene texto (será renderizado por el servidor cuando haya errores)
      if(msg && msg.textContent && msg.textContent.trim().length>0){
        // translate text if needed
        var t = msg.textContent.trim();
        var tr = translate(t);
        if(tr !== t){ msg.textContent = tr; }
        // add class to trigger CSS animation
        msg.classList.add('show');
        // remove the element after the animation completes (5s delay + 1s animation)
        setTimeout(function(){ try{ msg.classList.remove('show'); }catch(e){} }, 6000);
      }
    });
  }
  // Run on DOM ready
  if(document.readyState==='loading'){
    document.addEventListener('DOMContentLoaded', animateValidationMessages);
  }else{
    animateValidationMessages();
  }
})();
