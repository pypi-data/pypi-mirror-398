import traceback
import types
import logging
import unittest
from importlib.metadata import entry_points
from encadre.framework import Framework

logger = logging.getLogger(__name__)


class Controller():

    version = 0

    @classmethod
    def setup(cls, framework, root):
        methods = []
        cls.framework = framework
        ctrl_name = cls.__name__.lower()
        version = ctrl_name.split('_')[-1]
        if version.isdigit():
            ctrl_name = ctrl_name[:-(len(version) + 1)]
            version = int(version)
        else:
            version = framework.first_version
        for name in [a for a in dir(cls) if a[0] != '_']:
            attr = getattr(cls, name)
            if isinstance(attr, types.FunctionType) and \
               not name.startswith('test_'):
                verbs = ''.join([c for c in name if c.isupper() or c == '_'
                                 ]).lstrip('_').split('_')
                if verbs != ['']:
                    name = name[:name.find("_%s" % verbs[0])]
                if name == 'index__':
                    if root:
                        if name == 'index__':
                            framework.root_id = id(attr)
                    else:
                        root_id = getattr(framework, 'root_id', None)
                        # Prevent inheritance of index__
                        if root_id == id(attr):
                            continue
                # dig into decorator
                if hasattr(attr, '__wrapped__'):
                    methods.append(
                        (name, attr,
                         attr.__wrapped__.__code__.co_varnames[
                             1:attr.__wrapped__.__code__.co_argcount],
                         verbs if verbs != [''] else ['GET']))
                else:
                    methods.append(
                        (name, attr,
                         attr.__code__.co_varnames[1:attr.__code__.co_argcount],
                         verbs if verbs != [''] else ['GET']))
        framework.add_controller((cls, '__root__' if root else ctrl_name,
                                  version), methods)


def setup_controllers(cls, f, level=0):
    logger.debug("Setup controller '%s' (children: '%s')." % (
        cls, cls.__subclasses__()))
    if cls.__name__ != 'Controller':  # exclude abstract
        if not cls.__name__.startswith('_'):
            cls.setup(f, root=level < 2)
    for sub in cls.__subclasses__():
        setup_controllers(sub, f, level + 1)


def load_controllers(f, application):
    eps = entry_points()
    app_group = '%s.controllers' % application
    for group in (app_group, 'encadre.controllers'):
        for ep in eps.get(group, []):
            try:
                ep.load()
                logger.debug("Loaded controller '%s'" % ep)
            except ModuleNotFoundError:
                logger.error("Error importing '%s': %s" % (
                    ep, traceback.format_exc()))
    setup_controllers(Controller, f)


class EncadreTestCase(unittest.TestCase):
    def setUp(self):
        self.framework._json = {}
        self.framework._environ = {}
        self.framework._headers = {}
        self.framework._args = {}
        self.framework._cookies = {}

    def tearDown(self):
        pass


class TestFramework(Framework):
    def request_json(self):
        return self._json

    def request_environ(self):

        return self._environ

    def request_headers(self):
        return self._headers

    def request_args(self):
        return self._args

    def get_cookie(self, key):
        return self._cookies.get(key)

    def set_cookie(self, key, value):  # pylint: disable=W0221
        self._cookies[key] = value

    def send_bytes(self, bytes_like, **kwargs):  # pylint: disable=W0613
        return bytes_like.read()


def get_controllers_tsts(app):
    f = TestFramework(app.application, None)
    load_controllers(f, app.application)

    def missing_test(self):
        raise Exception("Missing test")

    for c in f.controllers:
        for v in f.controllers[c]:
            cls = f.controllers[c][v]['cls']
            attributes = {}
            for name in [a for a in dir(cls) if a[0] != '_']:
                attr = getattr(cls, name)
                if not name.startswith('test_'):
                    attributes[name] = attr
                if isinstance(attr, types.FunctionType) and \
                   not name.startswith('test_'):
                    test_name = 'test_%s' % name
                    test_long_name = 'test_%s_%s' % (cls.__name__, name)
                    test_fct = getattr(cls, test_name, missing_test)
                    attributes[test_long_name] = test_fct
            test_cls = type("Test%s" % cls.__name__,
                            (getattr(cls, 'testcase_cls', EncadreTestCase), ),
                            attributes)
            yield (test_cls.__name__, test_cls)
