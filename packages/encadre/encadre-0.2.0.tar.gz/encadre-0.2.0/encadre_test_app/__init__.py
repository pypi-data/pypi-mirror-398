import sys

import fastjsonschema
from encadre import Encadre


class Encadre_Test_App(Encadre):

    def validate_query(self, schema):
        from encadre import request
        fastjsonschema.compile(schema)(request.json)


def serve():
    if len(sys.argv) != 2:
        print("Usage: %s config.ini")
        sys.exit(1)
    Encadre_Test_App(sys.argv[1]).serve()


def dump_routes():
    if len(sys.argv) != 2:
        print("Usage: %s config.ini")
        sys.exit(1)
    Encadre_Test_App(sys.argv[1]).dump_routes()
