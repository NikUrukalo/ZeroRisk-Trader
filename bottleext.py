"""
Bottle helpers.

url()      - build links that also work behind the Binder proxy
redirect() - the same, for the Location header
template() - bottle.template with url() and path already available
"""

import os

import bottle
from bottle import *          # noqa: F401,F403


# '' locally, '/user/<id>/proxy/8080' on Binder (set by binder/start).
ROOT = os.environ.get('BOTTLE_ROOT', '').rstrip('/')


def url(path='/'):
    """Link for a template. Use this for every href, action and src."""
    if not path.startswith('/'):
        path = '/' + path
    return ROOT + path if ROOT else path


def absolute_url(path='/'):
    """Full https://host/... address, used for redirects."""
    env = bottle.request.environ

    # Binder puts two proxies in front of us and each appends to these
    # headers, so the value is "https,http" - take the first entry.
    scheme = (env.get('HTTP_X_FORWARDED_PROTO')
              or env.get('wsgi.url_scheme') or 'http').split(',')[0].strip()
    host = (env.get('HTTP_X_FORWARDED_HOST')
            or env.get('HTTP_HOST') or '').split(',')[0].strip()

    if not host:
        host = env.get('SERVER_NAME', '127.0.0.1')
        port = str(env.get('SERVER_PORT', ''))
        if port and port not in ('80', '443'):
            host = host + ':' + port

    return scheme + '://' + host + url(path)


def redirect(path='/'):
    """
    Redirect to a bare path, e.g. redirect('/overview').

    Do not wrap the path in url(): jupyter-server-proxy >= 4.5 already
    prepends the proxy prefix to relative Location headers, so it would land
    there twice. Absolute URLs are passed through untouched.
    """
    bottle.redirect(absolute_url(path))


def template(*args, **kwargs):
    kwargs.setdefault('url', url)
    kwargs.setdefault('path', bottle.request.path)
    return bottle.template(*args, **kwargs)
