import os
import bottle
from bottle import *


class Route(bottle.Route):
    """
    Custom Route class that handles the Binder proxy path.
    """
    def __init__(
        self,
        app,
        rule,
        method,
        callback,
        name=None,
        plugins=None,
        skiplist=None,
        **config
    ):
        if name is None:
            name = callback.__name__

        def decorator(*args, **kwargs):
            bottle.request.environ['SCRIPT_NAME'] = os.environ.get(
                'BOTTLE_ROOT',
                ''
            )
            return callback(*args, **kwargs)

        super().__init__(
            app,
            rule,
            method,
            decorator,
            name,
            plugins,
            skiplist,
            **config
        )


def template(*args, **kwargs):
    return bottle.template(
        *args,
        **kwargs,
        url=bottle.url
    )


bottle.Route = Route