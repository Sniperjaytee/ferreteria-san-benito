document.addEventListener('DOMContentLoaded', function() {
  try {
    // Buscar el contenedor de herramientas donde está el botón "Add"
    var objectTools = document.querySelector('.object-tools');
    if (!objectTools) return;

    // Crear el botón azul "Crear reporte"
    var btn = document.createElement('a');
    btn.href = '#';
    btn.id = 'crear-reporte-btn';
    btn.className = 'button';
    btn.style.background = '#0d6efd';
    btn.style.color = 'white';
    btn.style.marginRight = '8px';
    btn.textContent = 'Crear reporte';

    // Insertar antes del enlace "Add" si existe, si no, al final
    var addLink = objectTools.querySelector('.addlink');
    if (addLink) {
      objectTools.insertBefore(btn, addLink);
    } else {
      objectTools.appendChild(btn);
    }

    btn.addEventListener('click', function(e) {
      e.preventDefault();

      // Encontrar checkboxes seleccionados en la lista
      var checkboxes = document.querySelectorAll('input.action-select');
      var any = false;
      checkboxes.forEach(function(ch) {
        if (ch.checked) any = true;
      });

      if (!any) {
        alert('Selecciona al menos un pedido para generar el reporte.');
        return;
      }

      // Establecer la acción en el select y enviar el formulario
      var actionSelect = document.querySelector('select[name="action"]');
      if (!actionSelect) {
        alert('No se encontró el selector de acciones del admin.');
        return;
      }

      actionSelect.value = 'crear_reporte_pdf';

      // Enviar el formulario de cambios (changelist form)
      var form = document.getElementById('changelist-form');
      if (!form) {
        // En versiones antiguas el formulario puede tener otro id; buscar por name
        form = document.querySelector('form[action]');
      }
      if (!form) {
        alert('No se encontró el formulario de la lista para enviar la acción.');
        return;
      }

      form.submit();
    });
  } catch (err) {
    // No bloquear la página si hay error
    console.error('admin-pedidos-reporte error', err);
  }
});
