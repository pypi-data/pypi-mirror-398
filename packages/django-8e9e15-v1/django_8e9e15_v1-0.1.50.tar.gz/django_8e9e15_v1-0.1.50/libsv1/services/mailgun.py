import requests
from django.conf import settings
from django.template.loader import render_to_string
import os


class MailgunService:

    @staticmethod
    def send(email, subject, template_view, template_context, from_email=None, request=None):
        html_content = render_to_string(template_view, template_context)

        mailgun_endpoint = getattr(settings, 'MAILGUN_ENDPOINT', os.getenv('MAILGUN_ENDPOINT', ''))
        mailgun_domain = getattr(settings, 'MAILGUN_DOMAIN', os.getenv('MAILGUN_DOMAIN', ''))
        project_name = getattr(settings, 'PROJECT_NAME', os.getenv('PROJECT_NAME', ''))

        api_url = f"https://{mailgun_endpoint}/v3/{mailgun_domain}/messages"
        auth = ("api", getattr(settings, 'MAILGUN_SECRET', os.getenv('MAILGUN_SECRET', '')))
        if not from_email:
            from_email = f"{project_name} <noreply@{mailgun_domain}>"

        email_data = {
            "from": from_email,
            "to": [email],
            "subject": subject,
            "html": html_content,
        }

        try:
            response = requests.post(api_url, auth=auth, data=email_data)
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            if request is not None:
                try:
                    from libsv1.apps.global_system_log.services import GlobalSystemLogAdd
                    from libsv1.utils.base import BaseUtils
                    GlobalSystemLogAdd(request=request, additional_log={'MailgunService': BaseUtils.log_response_error(locals().get('response'), e)})
                except Exception as e:
                    print(f"MailgunService: {e}")

        return False

"""

MailgunService.send(email='bearablyk@gmail.com', subject='test', template_view='emails/test-email.html', template_context={'name': 'User Name'}, request=request)

"""