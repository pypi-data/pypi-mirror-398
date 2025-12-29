import os
import sys
import re
import logging
from flask import Flask, request, send_file, abort
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from encadre import Framework

logger = logging.getLogger(__name__)


class FlaskFramework(Framework):
    def __init__(self, application, config):
        Framework.__init__(self, application, config)
        self.versions = {}
        self._endpoints = set()
        self.application = application
        self.flask_app = Flask(application)
        self.flask_app.url_map.strict_slashes = False
        self.flask_app.register_error_handler(404, self.handle_exception)
        for k, v in (self.config.get('flask') or {}).items():
            _v = v
            if v.lower() == 'false':
                _v = False
            if v.lower() == 'true':
                _v = True
            if v.isdigit():
                _v = int(v)
            self.flask_app.config[k.upper()] = _v
        if not (self.config.get('flask') or {}).get('external_cors'):
            logger.debug("We handle CORS.")
            CORS(self.flask_app, supports_credentials=True)
        else:
            logger.debug("CORS must be handheld upstream.")
        if (self.config.get('flask') or {}).get('JWT_SECRET_KEY'.lower()):
            self.jwt_manager = JWTManager(self.flask_app)

    def setup_application(self, instance):
        Framework.setup_application(self, instance)
        for fct in self.before_call_chain:
            self.flask_app.before_request(fct)
        for fct in self.after_call_chain:
            self.flask_app.after_request(fct)
        self.flask_app.after_request(self._set_cookies)

    def _add_method(self, ctrl_name, method_name):
        def accessor(**args):
            import flask
            v = None
            if self.versioning_use_prefix:
                v = flask.request.environ.get('PATH_INFO').lstrip('/').split(
                    '/')[0]
                logger.debug("Got version '%s' from URL." % v)
            else:
                # flask handle case and underscores
                h = 'X-%s-Version' % self.application
                v = flask.request.headers.get(h)
                logger.debug("Got version '%s' from header '%s'." % (v, h))
            if v and not v.isdigit():
                flask.abort(405)
            v = int(v) if v else sys.maxsize
            v = v if v in self.controllers[ctrl_name] else max(
                self.controllers[ctrl_name].keys())
            verb = flask.request.environ['REQUEST_METHOD']
            cls = self.controllers[ctrl_name][v]['cls']
            try:
                m = self.controllers[ctrl_name][v]['methods'][method_name][
                    verb]['fct'].__name__
            except KeyError:
                logger.error("Cannot found method for: controller: '%s', "
                             "method: '%s', version: '%s', verb: '%s'" %
                             (ctrl_name, method_name, v, verb))
                flask.abort(405)
            self._cookies = []
            try:
                ret = getattr(cls(), m)(**args)
            except Exception as e:
                ret = self.handle_exception(e)
            return ret

        setattr(self, '_m_%s_%s' % (ctrl_name, method_name), accessor)

    def handle_exception(self, e):
        message, code = self.format_exception(e)
        if not message:
            abort(code)
        return message, code

    def _mk_endpoint(self, ctrl_name, method_name, args, version):
        ep = "/%s/%s%s" % (ctrl_name.lower(),
                           method_name if method_name != 'index__' else '',
                           ('/' + '/'.join(['<%s>' % a
                                            for a in args]) if args else ''))
        return '/%s%s' % (version, ep) if version else ep

    def _setup_routes(self):
        """ Add routes to flask """
        endpoints = {}
        methods = {}
        for c in sorted(self.controllers):
            for v in self.controllers[c]:
                for m in self.controllers[c][v]['methods']:
                    for _v in self.controllers[c][v]['methods'][m]:
                        fct = self.controllers[c][v]['methods'][m][_v]['fct']
                        args = self.controllers[c][v]['methods'][m][_v]['args']
                        e = self._mk_endpoint(
                            c,
                            m,
                            args,
                            version=v if self.versioning_use_prefix else None)
                        endpoints.setdefault(e, set())
                        if isinstance(fct.__defaults__, tuple):
                            url = re.search(r'^(.*[\\\/])', e).group()
                            endpoints.setdefault(url, set())
                            endpoints[url].add(_v)
                            methods[url] = (c, m)
                        endpoints[e].add(_v)
                        methods[e] = (c, m)
        for e, verbs in endpoints.items():
            self._add_method(*methods[e])
            logger.debug("Adding endpoint: '%s' allowing with verbs: '%s'." %
                         (e, verbs))
            route = e
            if route.startswith('/__root__'):
                route = e.replace('/__root__', '', 1)
            self.flask_app.add_url_rule(route,
                                        route,
                                        getattr(self, '_m_%s_%s' % methods[e]),
                                        methods=verbs)

    def serve(self, **kwargs):
        self._setup_routes()
        SSL_CERT_FILE = os.getenv('SSL_CERT_FILE')
        SSL_KEY_FILE = os.getenv('SSL_KEY_FILE')
        if SSL_CERT_FILE and SSL_KEY_FILE:
            kwargs['ssl_context'] = (
                os.getenv('SSL_CERT_FILE'),
                os.getenv('SSL_KEY_FILE'))
        self.flask_app.run(
            host=self.flask_app.config.get('HOST', '0.0.0.0'),
            port=self.flask_app.config.get('PORT', 5001),
            debug=self.flask_app.config.get('DEBUG', True),
            threaded=self.flask_app.config.get('THREADED', False),
            **kwargs)

    def get_wsgi_app(self):
        self._setup_routes()
        return self.flask_app

    def _set_cookies(self, response):
        for args, kwargs in getattr(self, '_cookies', {}):
            response.set_cookie(*args, **kwargs)
        return response

    def request_json(self):
        return request.json

    def request_environ(self):
        return request.environ

    def request_headers(self):
        return request.headers

    def request_args(self):
        return request.args

    def request_form(self):
        return request.form

    def request_files(self):
        return request.files

    def get_cookie(self, key):
        return request.cookies.get(key)

    def set_cookie(self, *args, **kwargs):
        self._cookies.append((args, kwargs))

    def send_bytes(self, bytes_like, **kwargs):
        return send_file(bytes_like, **kwargs)
