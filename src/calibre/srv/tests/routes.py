#!/usr/bin/env python2
# vim:fileencoding=utf-8
from __future__ import (unicode_literals, division, absolute_import,
                        print_function)

__license__ = 'GPL v3'
__copyright__ = '2015, Kovid Goyal <kovid at kovidgoyal.net>'

from calibre.srv.tests.base import BaseTest

class TestRouter(BaseTest):

    def test_route_construction(self):
        ' Test route construction '
        from calibre.srv.routes import Route, endpoint, RouteError
        def makeroute(route, func=lambda c,d:None, **kwargs):
            return Route(endpoint(route, **kwargs)(func))

        r = makeroute('/')
        self.ae(r.matchers, [])
        self.assertFalse(r.required_names)
        r = makeroute('/slash/')
        self.ae(r.endpoint.route, '/slash')

        def emr(route):
            self.assertRaises(RouteError, makeroute, route)
        emr('no_start')
        emr('/{xxx')
        emr('/{+all}/{other}')
        emr('/{t=}}')
        emr('/{+all=1}')
        emr('/{d=1}/no')
        emr('/x/{a=1}')
        self.assertRaises(RouteError, makeroute, '/a/b', lambda c,d,b,a:None)

    def test_route_finding(self):
        'Test route finding'
        from calibre.srv.routes import Router, endpoint, HTTPNotFound
        router = Router()

        def find(path):
            path = filter(None, path.split('/'))
            ep, args = router.find_route(path)
            args = list(args)
            return ep, args

        @endpoint('/')
        def root(ctx, data):
            pass

        @endpoint('/defval/{a=1}')
        def defval(ctx, data, a):
            pass

        @endpoint('/varpath/{a}/{b}')
        def varpath(ctx, data, a, b):
            pass

        @endpoint('/soak/{+rest}')
        def soak(ctx, dest, rest):
            pass

        @endpoint('/soak_opt/{+rest="xxx"}')
        def soak_opt(ctx, dest, rest):
            pass

        for x in locals().itervalues():
            if getattr(x, 'is_endpoint', False):
                router.add(x)
        router.finalize()

        ep, args = find('/')
        self.ae(ep, root), self.assertFalse(args)
        ep, args = find('/defval')
        self.ae(ep, defval), self.ae(args, [1])
        ep, args = find('/defval/2')
        self.ae(ep, defval), self.ae(args, [2])
        self.assertRaises(HTTPNotFound, find, '/defval/a')  # a must be an integer
        self.assertRaises(HTTPNotFound, find, '/varpath')
        self.assertRaises(HTTPNotFound, find, '/varpath/x')
        self.assertRaises(HTTPNotFound, find, '/varpath/x/y/z')
        self.assertRaises(HTTPNotFound, find, '/soak')
        ep, args = find('/varpath/x/y')
        self.ae(ep, varpath), self.ae(args, ['x', 'y'])
        ep, args = find('/soak/x')
        self.ae(ep, soak), self.ae(args, ['x'])
        self.ae(router.routes['/soak'].soak_up_extra, 'rest')
        ep, args = find('/soak/x/y/z')
        self.ae(ep, soak), self.ae(args, ['x/y/z'])
        ep, args = find('/soak_opt')
        self.ae(ep, soak_opt), self.ae(args, ['xxx'])
        ep, args = find('/soak_opt/a/b')
        self.ae(ep, soak_opt), self.ae(args, ['a/b'])
