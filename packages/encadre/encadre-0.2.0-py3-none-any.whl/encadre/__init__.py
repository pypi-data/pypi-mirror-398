import sys
import configparser
import traceback
import logging
import logging.config
from encadre.controllers import Controller, load_controllers
from encadre.framework import Framework, DumpRoutes
from encadre.framework import framework_from_config, validate

logger = logging.getLogger(__name__)


class NotReady:
    def __init__(self, diagnostic):
        self.diagnostic = diagnostic

    def __getattr__(self, attribute):
        raise AttributeError("Cannot access %r: %s" %
                             (attribute, self.diagnostic))

    def __getitem__(self, item):
        raise AttributeError("Cannot find %r: %s" % (item, self.diagnostic))

    def __bool__(self):
        return False


request = cookies = NotReady("Encadre is not setup yet.")


class Encadre():

    config = {}

    def __init__(self, config_filename):
        self.application = getattr(self, 'application',
                                   self.__class__.__name__.lower())
        logger.debug("Starting encadre application '%s'." % self.application)
        self.config_filename = config_filename
        if self.config_filename:
            self.config.update(self.read_config(self.config_filename))
            try:
                logging.config.fileConfig(self.config_filename)
            except Exception:
                print("You'd better configure logging in '%s':\n%s" %
                      (self.config_filename, traceback.format_exc()))
        setattr(sys.modules['encadre'], 'config', self.config)
        self.framework = framework_from_config(self.__class__.__name__.lower(),
                                               self.config)
        self.framework.setup_application(self)
        load_controllers(self.framework, self.application)

    def read_config(self, filename):
        config = {self.__class__.__name__.lower(): {}}
        p = configparser.ConfigParser()
        p.read(filename)
        for n, s in p.items():
            if s:
                config[n] = dict(s)
        return config

    def serve(self):
        assert self.config, "Missing config."
        self.framework.serve()

    def dump_routes(self):
        assert self.config, "Missing config."
        routes = DumpRoutes(self.__class__.__name__.lower(), self.config)
        load_controllers(routes, self.application)
        print(routes)

    def get_wsgi_app(self):
        config = self.read_config(self.config_filename)
        assert config, "Missing config."
        return self.framework.get_wsgi_app()


__all__ = ['Encadre', 'Framework', 'Controller', 'validate']
