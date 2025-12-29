import unittest
import random
from encadre import Controller, validate


class Hello(Controller):
    """ A very polite controller """

    def index__(self):
        """ Says hello ! """
        return "Hello world"

    def test_index__(self):
        self.assertTrue(self.index__() == "Hello world")

    def config(self):
        """ Dump the config """
        from encadre import config
        return config

    def test_config(self):
        from encadre import config
        k = 'test_%s' % random.randint(0, 1000)
        v = random.randint(0, 1000)
        config.update({k: v})
        self.assertTrue(self.config()[k] == v)

    @validate({
        'title': 'Dummy test',
        'type': 'object',
        'properties': {
            'numbers': {
                'description': "We want an array of numbers",
                'type': 'array',
                'items': {
                    'type': 'integer'
                },
                'minItems': 1
            }
        },
        'required': ['numbers']
    })
    def i_am_validated_POST(self):
        from encadre import request
        return request.json

    def test_i_am_validated_POST(self):
        from encadre import request
        request.json = {'numbers': [1, 2]}
        self.assertTrue(self.i_am_validated_POST() == {
            'numbers': [1, 2]})

    @validate({
        'title': 'Dummy test',
        'type': 'object',
        'properties': {
            'numbers': {
                'description': "We want an array of numbers",
                'type': 'array',
                'items': {
                    'type': 'integer'
                },
                'minItems': 1
            }
        },
        'required': ['numbers']
    })
    def i_will_not_pass_validation_POST(self):
        from encadre import request
        return request.json

    def test_i_will_not_pass_validation_POST(self):
        from encadre import request
        request.json = {'xnumbers': [1, 2]}
        self.i_am_validated_POST()
        self.assertRaises(Exception)


class Hello_2(Controller):
    """ A very polite controller (version 2) """

    def index__(self):
        """ Says hello ! """
        return "Hello world (2)"

    def test_index__(self):
        self.assertTrue(self.index__() == "Hello world (2)")

    def to(self, who):
        """ Says hello to whom ask for """
        return "Hello %s !" % who

    def test_to(self):
        assert True

    def foo(self):
        return "Foo"

    def test_foo(self):
        assert True

    def foo_(self):
        return "Foo with an '_' at the end !"

    def test_foo_(self):
        assert True

    def bar_GET(self):
        return "Bar"

    def test_bar_GET(self):
        assert True

    def baz_POST(self):
        from encadre import request
        return request.json

    def test_baz_POST(self):
        from encadre import request
        k = 'test_%s' % random.randint(0, 1000)
        v = random.randint(0, 1000)
        request.json = {k: v}
        self.assertTrue(self.baz_POST()[k] == v)

    def qux_GET_POST(self):
        return "Qux"

    def test_qux_GET_POST(self):
        assert True

    def args(self):
        from encadre import request
        return request.args.get('qwe', "no 'qwe' arg")

    def test_args(self):
        from encadre import request
        v = 'test_%s' % random.randint(0, 1000)
        request.args['qwe'] = v
        self.assertTrue(self.args() == v)


class Hello_3(Hello_2):
    """ A very polite controller """

    def index__(self):
        """ Says hello ! """
        return "Hello world (3)"

    def test_index__(self):
        self.assertTrue(self.index__() == "Hello world (3)")

    def bar_GET(self):
        """ Better 'bar' """
        return "Better Bar"

    def test_bar_GET(self):
        assert True

    def bar_POST(self):
        """ That one handle POST too ! """
        return "Handle POST too."

    def test_bar_POST(self):
        assert True

    def send_bytes(self):
        return self.framework.send_bytes(
            open("/etc/passwd", "rb"),
            as_attachment=True,
            attachment_filename='etc-passwd.txt',
            mimetype='text/plain')

    def test_send_bytes(self):
        self.assertTrue(b'root' in self.send_bytes())

    def dividebyzero(self):
        return 1 / 0


class StrangeTestCase(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass


class Hello_4(Hello_3):

    testcase_cls = StrangeTestCase
