import sys
import logging
import traceback
from importlib.metadata import entry_points
from decorator import decorator

logger = logging.getLogger(__name__)
ENI = Exception("Not implemented.")


class Cookies():
    def __init__(self, framework):
        self.f = framework

    def get(self, key):
        return self.f.get_cookie(key)

    def set(self, *args, **kwargs):
        return self.f.set_cookie(*args, **kwargs)


class Request():
    def __init__(self, framework):
        self.f = framework
        self._json = None
        self._environ = None
        self._headers = None
        self._args = None
        self._files = None
        self._form = None

    def _get_json(self):
        return self._json or self.f.request_json()

    # Let unit tests set some json
    def _set_json(self, json):
        self._json = json

    json = property(_get_json, _set_json)

    def _get_environ(self):
        return self._environ or self.f.request_environ()

    # Let unit tests set environ
    def _set_environ(self, environ):
        self._environ = environ

    environ = property(_get_environ, _set_environ)

    def _get_headers(self):
        return self._headers or self.f.request_headers()

    # Let unit tests set environ
    def _set_headers(self, headers):
        self._headers = headers

    headers = property(_get_headers, _set_headers)

    def _get_args(self):
        return self._args or self.f.request_args()

    # Let unit tests set environ
    def _set_args(self, args):
        self._args = args

    args = property(_get_args, _set_args)

    def _get_files(self):
        return self._files or self.f.request_files()

    # Let unit tests set files
    def _set_files(self, files):
        self._files = files

    files = property(_get_files, _set_files)

    def _get_form(self):
        return self._form or self.f.request_form()

    # Let unit tests set form
    def _set_form(self, form):
        self._form = form

    form = property(_get_form, _set_form)


def validate(vargs):
    def helper(func, *args, **kwargs):
        if hasattr(args[0].framework, 'validate_query'):
            args[0].framework.validate_query(vargs)
        return func(*args, **kwargs)
    return decorator(helper)


class Framework():

    request_class = Request
    cookies_class = Cookies

    def __init__(self, application, config):
        self.application = application
        self.config = config
        self.first_version = int((self.config or {}).get(application, {}).get(
            'first_version', '0'))
        if self.first_version:
            logger.debug("Config set 'first_version' to %s." %
                         self.first_version)
        self.versioning_use_prefix = (self.config or {}).get(
            application, {}).get('versioning', 'headers').lower() == 'prefix'
        if self.versioning_use_prefix:
            logger.debug("Config set versioning to 'prefix' mode.")
        self.routes = {}
        self.controllers = {}
        self.request = self.request_class(self)
        setattr(sys.modules['encadre'], 'request', self.request)
        self.cookies = self.cookies_class(self)
        setattr(sys.modules['encadre'], 'cookies', self.cookies)

    def add_controller(self, ctrl, methods):
        ctrl_cls, ctrl_name, ctrl_version = ctrl
        self.controllers.setdefault(ctrl_name, {})
        self.controllers[ctrl_name][ctrl_version] = {
            'doc': (ctrl_cls.__doc__ or '').strip(),
            'cls': ctrl_cls,
            'methods': {}}
        for method_name, method, args, verbs in methods:
            self.controllers[ctrl_name][ctrl_version]['methods'].setdefault(
                method_name, {})
            for verb in verbs:
                self.controllers[ctrl_name][ctrl_version]['methods'][
                    method_name][verb] = {
                        'fct': method,
                        'doc': (method.__doc__ or '').strip(),
                        'args': args}

    def setup_application(self, instance):
        self.instance = instance
        self.before_call_chain = []
        if hasattr(instance, 'before_call'):
            self.before_call_chain.append(self.instance_before_call)
        self.after_call_chain = []
        if hasattr(instance, 'after_call'):
            self.after_call_chain.append(self.instance_after_call)
        if hasattr(instance, 'validate_query'):
            self.validate_query = instance.validate_query

    def instance_before_call(self):
        getattr(self.instance, 'before_call')()

    def instance_after_call(self, response):
        getattr(self.instance, 'after_call')()
        return response

    def not_implemented(self):
        raise ENI

    request_json = request_environ = request_headers = \
        request_args = request_files = \
            get_cookie = set_cookie = send_bytes = \
                request_form = not_implemented

    def format_exception(self, e):
        ret = None
        code = 500
        logger.exception(traceback.format_exc())
        if hasattr(self.instance, "format_exception"):
            ret, code = self.instance.format_exception(e)
        else:
            ha = (self.config or {}).get(self.application, {}).get(
                'on_exception', '').lower()
            if ha == 'traceback':
                ret = traceback.format_exc()
            if ha == 'str':
                ret = str(e)
        if ret is None:
            raise e
        return ret, code


class DumpRoutes(Framework):

    def __repr__(self):
        ret = []
        for c in sorted(self.controllers):
            ret.append("* Controller: %s" % (c))
            for v in self.controllers[c]:
                ret.append("** Version: %s: %s" %
                           (v, self.controllers[c][v]['doc']))
                for m in self.controllers[c][v]['methods']:
                    for _v in self.controllers[c][v]['methods'][m]:
                        ret.append(
                            "- [%s] %s%s: %s" %
                            (_v, m,
                             self.controllers[c][v]['methods'][m][_v]['args'],
                             self.controllers[c][v]['methods'][m][_v]['doc']))
        return "\n".join(ret)


def framework_from_config(application, config):
    fw_name = (config.get(application) or {}).get('framework')
    assert fw_name, "No framework configured."
    eps = entry_points()
    app_group = '%s.frameworks' % application
    for group in (app_group, 'encadre.frameworks'):
        group_eps = eps.get(group, [])
        for ep in group_eps:
            if ep.name == fw_name:
                return ep.load()(application, config)
    raise Exception("No framework available")
