from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.safestring import SafeText
from urllib3.exceptions import RequestError
from netpicker_client.exceptions import UnauthorizedException

from netpicker.utilities import get_settings

API_ERROR = ('Error occurred while communicating with Netpicker API. Make sure '
             '<a href="{}">your settings</a> are set correctly.')

UNAUTHORIZED_ERROR = ('Unauthorized access to Netpicker API. Please check your '
                      '<a href="{}">API settings</a> and ensure your API key '
                      'is valid.')

NOT_SET = ('In order to use the Netpicker plugin, '
           'information about the Netpicker API server needs to be provided')


class RequireSettingsMixin:
    force_redirect: bool = True

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if not get_settings(request) and self.force_redirect:
                messages.warning(request, NOT_SET)
                return redirect('plugins:netpicker:netpickersetting')
        try:
            return super().dispatch(request, *args, **kwargs)
        except UnauthorizedException:
            txt = SafeText(UNAUTHORIZED_ERROR.format(reverse('plugins:netpicker:netpickersetting')))
            messages.error(request, txt)
            return redirect(request.META.get('HTTP_REFERER'))
        except RequestError:
            txt = SafeText(API_ERROR.format(reverse('plugins:netpicker:netpickersetting')))
            messages.error(request, txt)
            return redirect(request.META.get('HTTP_REFERER'))
