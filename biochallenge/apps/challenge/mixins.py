from challenge.models import Release
from django.http import Http404


class ReleaseMixin(object):

    def get_release(self, *args, **kwargs):
        try:
            release_pk = self.kwargs.get('release_pk')
            self.release = Release.objects.get(pk=release_pk)
        except Exception as e:
            raise Http404
        
    def get_form_kwargs(self, *args, **kwargs):
        kwargs = super(ReleaseMixin, self).get_form_kwargs(*args, **kwargs)
        kwargs['release'] = self.release
        return kwargs

    def get_context_data(self, *args, **kwargs):
        context = super(ReleaseMixin, self).get_context_data(
            *args, **kwargs)
        context['release'] = self.release
        return context

    def get(self, request, *args, **kwargs):
        self.get_release()
        return super(ReleaseMixin, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.get_release()
        return super(ReleaseMixin, self).post(request, *args, **kwargs)
