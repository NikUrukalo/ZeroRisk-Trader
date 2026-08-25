"""
bottleext.py - the thin layer between the app and Bottle.

This file was the reason the app only worked on localhost, and the reason
login returned a 500. Two problems, both in url().

1) url() took a route NAME and resolved it against the WRONG application
   -----------------------------------------------------------------------
   The old version re-exported `bottle.url`. That function is defined as

       url = make_default_app_wrapper('get_url')      # bottle.py

   i.e. it looks the name up on Bottle's *default* application. app.py does
   `app = Bottle()`, which creates a NEW application and never pushes it onto
   Bottle's app stack - so the default app has no routes at all, and every
   call raises

       bottle.RouteBuildError: ('No route with that name.', 'login')

   That is a 500 on: any visit to a protected page while logged out
   (cookie_required -> url('login')), a successful login (url('overview')),
   and logout (url('login')).

2) It never added the Binder prefix
   -----------------------------------------------------------------------
   On Binder the app is not served from the root of the domain. It sits behind
   jupyter-server-proxy at

       https://hub.mybinder.org/user/<random-id>/proxy/8080/

   A template that writes href="/trade" is resolved by the browser against the
   HOST, so the browser asks the Binder hub for /trade - not the app. Every
   link, every form action and the stylesheet 404. That is exactly what "works
   on localhost, not on Binder" looks like from the outside.

   The old Route subclass set request.environ['SCRIPT_NAME'], which changes
   what Bottle *thinks* its mount point is, but does nothing to links that are
   already hard-coded in the HTML.

The fix is one small function: url() takes a PATH and prepends BOTTLE_ROOT.
binder/start exports that variable; locally it is empty and url() is a no-op.

    template:    <a href="{{ url('/trade') }}">Trade</a>
    localhost:   /trade
    Binder:      /user/ab12cd/proxy/8080/trade
"""

import os

import bottle
from bottle import *          # noqa: F401,F403  (Bottle, run, request, ...)


# The prefix the app is mounted under. Empty when running locally.
ROOT = os.environ.get('BOTTLE_ROOT', '').rstrip('/')


def url(path='/'):
    """
    Build a link from a PATH (not a route name), with the Binder prefix.

        url('/login')   ->  '/login'                          locally
                        ->  '/user/ab12/proxy/8080/login'     on Binder
    """
    if not path.startswith('/'):
        path = '/' + path
    return ROOT + path if ROOT else path


def absolute_url(path='/'):
    """
    The same link as url(), but as a full https://host/... address.

    Only needed for redirects - see redirect() below.

    Two details that are wrong if you build this by hand:

    * The scheme has to come from X-Forwarded-Proto, because the app itself is
      only ever spoken to over plain HTTP by the proxy. On Binder there are two
      proxies in front of us, and each appends to that header, so its value is
      the string "https,http". Taking .split(',')[0] gives the scheme the
      BROWSER actually used. (Bottle does not do this - it uses the whole
      header, which is why its error pages on Binder say
      'https,http://hub.mybinder.org/...'.)

    * The host likewise comes from X-Forwarded-Host, and gets the same
      comma treatment.
    """
    env = bottle.request.environ

    scheme = (env.get('HTTP_X_FORWARDED_PROTO')
              or env.get('wsgi.url_scheme')
              or 'http')
    scheme = scheme.split(',')[0].strip()

    host = (env.get('HTTP_X_FORWARDED_HOST')
            or env.get('HTTP_HOST')
            or '')
    host = host.split(',')[0].strip()

    if not host:                                   # direct, no proxy, no Host
        host = env.get('SERVER_NAME', '127.0.0.1')
        port = str(env.get('SERVER_PORT', ''))
        if port and port not in ('80', '443'):
            host = host + ':' + port

    return scheme + '://' + host + url(path)


def redirect(path='/'):
    """
    Redirect to a PATH, in a way that survives the Binder proxy.

    This shadows bottle.redirect on purpose, so app.py keeps calling
    `redirect('/overview')` and gets the corrected behaviour.

    Why this is not just bottle.redirect(url('/overview'))
    ------------------------------------------------------
    jupyter-server-proxy treats the HTML body and the Location header
    differently, and the difference is easy to miss:

      * it does NOT touch the response body, so every link inside the HTML
        must already carry the /user/<id>/proxy/8080 prefix - that is what
        url() is for;

      * but since version 4.5.0 it DOES rewrite the Location header of any
        301/302/303/307/308, prepending that same prefix, because it assumes
        the proxied app knows nothing about it (handlers.py,
        _rewrite_location_header).

    So sending Location: /user/<id>/proxy/8080/overview gets it prefixed a
    SECOND time. The browser then asks for

        /user/<id>/proxy/8080/user/<id>/proxy/8080/overview

    the proxy strips one copy and hands the app the other, and Bottle answers

        Error: 404 Not Found - Not found: '/user/<id>/proxy/8080/overview'

    which is exactly the page you saw after logging in.

    The way out is an ABSOLUTE url. _rewrite_location_header starts with

        if parsed.scheme or parsed.netloc:   # absolute URL - leave as is
            return location

    so a Location of https://hub.mybinder.org/user/<id>/proxy/8080/overview is
    passed through untouched. It is also correct on older proxy versions that
    do no rewriting at all, and on localhost, where it is simply
    http://localhost:8080/overview.
    """
    bottle.redirect(absolute_url(path))


def template(*args, **kwargs):
    """bottle.template() with our url() always available inside templates."""
    kwargs.setdefault('url', url)
    return bottle.template(*args, **kwargs)
