import logging

from django.contrib.auth import get_user_model, logout
from django.http import HttpResponseRedirect
from django.utils.deprecation import MiddlewareMixin

from itoutils.django.nexus.token import decode_token

logger = logging.getLogger(__name__)


class BaseAutoLoginMiddleware(MiddlewareMixin):
    def get_queryset(self):
        return get_user_model().objects.all()

    def get_proconnect_authorize_url(self, user, next_url):
        raise NotImplementedError

    def get_no_user_url(self, email, next_url):
        raise NotImplementedError

    def process_request(self, request):
        if "auto_login" not in request.GET:
            return

        query_params = request.GET.copy()
        auto_login = query_params.pop("auto_login")
        email = None

        new_url = f"{request.path}?{query_params.urlencode()}" if query_params else request.path

        if len(auto_login) != 1:
            logger.info("Nexus auto login: Multiple tokens found -> ignored")
            return HttpResponseRedirect(new_url)
        else:
            [token] = auto_login

        try:
            decoded_data = decode_token(token)
            email = decoded_data.get("email")
        except ValueError:
            logger.info("Invalid auto login token")

        if email is None:
            logger.info("Nexus auto login: Missing email in token -> ignored")
            return HttpResponseRedirect(new_url)

        if request.user.is_authenticated:
            if request.user.email == email:
                logger.info("Nexus auto login: user is already logged in")
                return HttpResponseRedirect(new_url)
            else:
                logger.info("Nexus auto login: wrong user is logged in -> logging them out")
                # We should probably also logout the user from ProConnect but it requires to redirect to ProConnect
                # and the flow becomes a lot more complicated
                logout(request)

        try:
            user = self.get_queryset().get(email=email)
            logger.info("Nexus auto login: %s was found and forwarded to ProConnect", user)
            return HttpResponseRedirect(self.get_proconnect_authorize_url(user, new_url))
        except get_user_model().DoesNotExist:
            logger.info("Nexus auto login: no user found for jwt=%s", token)
            return HttpResponseRedirect(self.get_no_user_url(email, new_url))
