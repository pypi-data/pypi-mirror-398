from django.contrib.auth.models import User
from django.template import Library
from django.utils.translation import gettext
from .. import ADMIN_LINK_ONLY_SUPERUSER, ADMIN_LINK_USE_STYLES

register = Library()


@register.inclusion_tag('admin_link/includes/admin_link.html', takes_context=True)
def admin_link(context):
    user: User = context['user']
    condition = user.is_authenticated and ((user.is_staff and not ADMIN_LINK_ONLY_SUPERUSER) or user.is_superuser)
    return dict(user=user, condition=condition, use_styles=ADMIN_LINK_USE_STYLES, text=gettext("Admin panel"))
