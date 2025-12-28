from s4.platform.connection import Connection


class ConnectedModel(object):
    def __init__(self, connection: Connection):
        self.connection = connection


class GraphModel(object):
    def __init__(self, iri: str):
        self.iri = iri
