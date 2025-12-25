import logging
from django.conf import settings
from django.template.loader import render_to_string
from django.templatetags.static import static

logger = logging.getLogger(__name__)

# Fallback si anymail n'est pas installé
try:
    from anymail.message import AnymailMessage

    _HAS_ANYMAIL = True
except Exception:
    from django.core.mail import EmailMultiAlternatives

    _HAS_ANYMAIL = False


class AnymailModuleRetourUtils:

    @staticmethod
    def compress_html(html_content):
        if not html_content:
            return ""
        return " ".join(" ".join(html_content.splitlines()).split())

    @staticmethod
    def render_template(template_name, context):
        """
        template_name: ex. "retour_client/mails/recap-journalier-client.tpl"
        """
        alyse_societe = getattr(settings, "ALYSE_SOCIETE", None)
        url_protocol = getattr(settings, "URL_PROTOCOL", "")
        url_domain = getattr(settings, "URL_DOMAIN", "")

        if alyse_societe == "APA":
            logo_url = static("images/logo/logo-APA.jpg")
        else:
            logo_url = static("images/logo/logo-ALP.jpg")

        # Si protocol + domain sont fournis, on fait une URL absolue
        if url_protocol and url_domain:
            logo_abs = f"{url_protocol}://{url_domain}{logo_url}"
        else:
            logo_abs = logo_url

        ctx = {**context, "logo": logo_abs}
        return render_to_string(template_name, ctx)

    @staticmethod
    def send_mail(subject, recipients, body_html=None):
        email_feature = getattr(settings, "EMAIL_FEATURE", True)
        from_email = getattr(settings, "EMAIL_EXPEDITEUR", None)
        brevo_api_key = getattr(settings, "BREVO_API_KEY", None)

        if not email_feature:
            logger.debug("EMAIL_FEATURE=False, envoi mail désactivé.")
            return

        if not recipients:
            logger.warning("Aucun destinataire fourni pour l'email '%s'.", subject)
            return

        body_html = AnymailModuleRetourUtils.compress_html(body_html or "")

        if _HAS_ANYMAIL:
            msg = AnymailMessage(
                subject=subject,
                body=body_html,
                from_email=from_email,
                to=recipients,
            )
            if brevo_api_key:
                try:
                    msg.esp_extra = {"api_key": brevo_api_key}
                except Exception:
                    pass
        else:
            msg = EmailMultiAlternatives(
                subject=subject,
                body=body_html,
                from_email=from_email,
                to=recipients,
            )
            msg.attach_alternative(body_html, "text/html")

        try:
            msg.send()
        except Exception as e:
            logger.error("Erreur envoi email (%s): %s", type(e).__name__, e)
