"""Petits objets simulés réutilisables dans les exemples de repository."""


class FakeCursor:
    """Imite uniquement les méthodes psycopg2 utilisées par l'application."""

    def __init__(self, rows=None, rowcount=0):
        self.rows = rows or []
        self.rowcount = rowcount
        self.query = None
        self.params = None

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def execute(self, query, params=None):
        self.query = query
        self.params = params

    def fetchone(self):
        return self.rows[0] if self.rows else None

    def fetchall(self):
        return self.rows


class FakeConnection:
    """Retourne les curseurs préparés dans l'ordre des requêtes SQL."""

    def __init__(self, *cursors):
        self.cursors = list(cursors)
        self.used_cursors = []

    def cursor(self):
        cursor = self.cursors.pop(0)
        self.used_cursors.append(cursor)
        return cursor
