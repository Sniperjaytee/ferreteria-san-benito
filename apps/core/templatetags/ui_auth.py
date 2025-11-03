from django import template
from django.urls import reverse

register = template.Library()


@register.inclusion_tag('includes/auth_cta.html', takes_context=True)
def auth_cta(context, style='default'):
    """Renderiza los botones de login/registro o logout según el estado de autenticación.

    Uso en templates:
      {% load ui_auth %}
      {% auth_cta %}
    """
    request = context.get('request')
    next_url = ''
    if request:
        # Mantener next solo si viene explícito o si NO estamos en login/registro
        explicit_next = request.GET.get('next', '')
        current_path = getattr(request, 'path', '') or ''
        try:
            login_path = reverse('login')
        except Exception:
            login_path = '/accounts/login/'
        try:
            registro_path = reverse('core:registro')
        except Exception:
            registro_path = '/registro/'
        try:
            acceso_path = reverse('core:acceso_requerido')
        except Exception:
            acceso_path = '/acceso/'

        on_auth_pages = current_path.startswith(login_path) or current_path.startswith(registro_path) or current_path.startswith(acceso_path)
        if explicit_next:
            next_url = explicit_next
        elif not on_auth_pages:
            # En páginas normales, conserva la ruta actual como next
            try:
                next_url = request.get_full_path()
            except Exception:
                next_url = ''
    return {
        'user': context.get('user'),
        'next': next_url,
        'style': style,
    }
