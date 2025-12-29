import unittest
from encadre import Encadre
from encadre.framework import framework_from_config
from encadre.controllers import load_controllers


class EncadreFlask(Encadre):

    application = 'encadre_test_app'

    def __init__(self):
        Encadre.__init__(self, None)
        self.framework = framework_from_config(self.application,
                                               {self.application:
                                                {'framework': 'flask'}})
        load_controllers(self.framework, self.application)


class TestEncadreFlask(unittest.TestCase):

    def setUp(self):
        self.encadre = EncadreFlask()

    def test_setup_routes(self):
        self.encadre.framework._setup_routes()
