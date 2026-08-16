"""Views of the foodgram backend that are not part of the API."""

from django.http import Http404
from django.shortcuts import redirect

from recipes.models import ShortLink


def short_link_redirect(request, short_id):
    """Redirect a short link to the recipe page.

    The redirect is a backend concern, not a REST API one: the API only
    generates the short link, while the redirect itself serves the frontend.
    """
    try:
        short_link = ShortLink.objects.get(short_id=short_id)
    except ShortLink.DoesNotExist:
        raise Http404('Короткая ссылка не найдена.')
    return redirect('/recipes/' + str(short_link.recipe_id) + '/')
