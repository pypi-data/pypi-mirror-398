from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils import timezone


def now_date():
    return timezone.now().date()


def is_user_admin(user):
    fn = getattr(settings, "RETOUR_CLIENT_IS_ADMIN_FN", None)
    return fn(user) if fn else bool(getattr(user, "is_staff", False))


def get_current_user(request):
    return getattr(request, "user", None)


def image_upload_to(instance, filename):
    fn = getattr(settings, "RETOUR_CLIENT_IMAGE_UPLOAD_TO", None)
    return fn(instance, filename) if fn else f"retour_client/{filename}"


def send_mail_html(subject, to, body_html):
    fn = getattr(settings, "RETOUR_CLIENT_SEND_MAIL_FN", None)
    if fn:
        return fn(subject, to, body_html)
    mail = EmailMultiAlternatives(subject, body_html, to=to)
    mail.attach_alternative(body_html, "text/html")
    mail.send()


def get_lucy_collaborateur_email(siren):
    fn = getattr(settings, "RETOUR_CLIENT_GET_COLLAB_EMAIL_FN", None)
    return fn(siren) if fn else None
