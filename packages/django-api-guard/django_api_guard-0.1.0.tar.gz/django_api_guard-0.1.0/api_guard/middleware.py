from django.conf import settings
from django.http import HttpResponseForbidden
from django.http import HttpResponseRedirect
from django.urls import reverse

class APIBrowserFilterMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.config = getattr(settings, 'API_GUARD_CONFIG', {})
        self.enabled = self.config.get('ENABLED', True)
        self.api_prefixes = self.config.get('API_PREFIXES', ['/api/'])
        self.redirect_url = self.config.get('REDIRECT_URL', '/')
        self.exempt_urls = self.config.get('EXEMPT_URLS', [])
        
    def __call__(self, request):
        if not self.enabled:
            return self.get_response(request)

        path = request.path
        accept_header = request.headers.get("Accept", "")
        
        is_api_request = any(path.startswith(prefix) for prefix in self.api_prefixes)
        is_browser_request = 'text/html' in accept_header
        
        if is_api_request and is_browser_request:
            if path not in self.exempt_urls:
                if self.redirect_url:
                    return HttpResponseRedirect(self.redirect_url)
                else:
                    return HttpResponseForbidden()
                
        return self.get_response(request)