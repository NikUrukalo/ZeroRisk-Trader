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


def template(*args, **kwargs):
    """bottle.template() with our url() always available inside templates."""
    kwargs.setdefault('url', url)
    return bottle.template(*args, **kwargs)
