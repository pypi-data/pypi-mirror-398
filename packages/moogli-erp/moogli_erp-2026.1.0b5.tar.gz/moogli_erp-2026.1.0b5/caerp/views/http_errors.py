def not_found_view(request):
    request.response.status_code = 404
    return {"title": "Page non trouvée (erreur 404)"}


def includeme(config):
    config.add_notfound_view(
        view=not_found_view,
        renderer="http_404.mako",
    )
