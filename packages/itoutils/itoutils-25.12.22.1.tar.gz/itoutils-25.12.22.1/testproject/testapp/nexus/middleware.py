from itoutils.django.nexus.middleware import BaseAutoLoginMiddleware
from itoutils.urls import add_url_params


class AutoLoginMiddleware(BaseAutoLoginMiddleware):
    def get_proconnect_authorize_url(self, user, next_url):
        return add_url_params("/proconnect/authorize", {"email": user.email, "next_url": next_url})

    def get_no_user_url(self, email, next_url):
        return add_url_params("/register", {"email": email, "next_url": next_url})
