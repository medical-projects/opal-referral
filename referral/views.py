"""
Views for the OPAL referral portal plugin
"""
from django.views.generic import View, TemplateView

from opal.models import Patient
from opal.core.views import LoginRequiredMixin, _build_json_response, _get_request_data

class ReferralIndexView(LoginRequiredMixin, TemplateView):
    """
    Main entrypoint into the referral portal service. 
    
    Lists our referral routes.
    """
    template_name = 'referral/index.html'


class ReferralTemplateView(TemplateView):
    def dispatch(self, *args, **kwargs):
        self.name = kwargs['name']
        return super(ReferralTemplateView, self).dispatch(*args, **kwargs)

    def get_template_names(self, *args, **kwargs):
        return ['referral/'+self.name]

    def get_context_data(self, *args, **kwargs):
        context = super(ReferralTemplateView, self).get_context_data(**kwargs)
        from referral import ReferralRoute
        context['referral_routes'] = ReferralRoute.list()
        return context
