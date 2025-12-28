from django.conf import settings

ADMIN_LINK_ONLY_SUPERUSER = getattr(settings, 'ADMIN_LINK_ONLY_SUPERUSER', False)
ADMIN_LINK_USE_STYLES = getattr(settings, 'ADMIN_LINK_USE_STYLES', True)
