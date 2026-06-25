from django.db import connections
from django.test.runner import DiscoverRunner


class LiveTcrdTestRunner(DiscoverRunner):
    """
    Test runner that uses the live 'tcrd' MySQL database as-is, skipping the
    normal CREATE DATABASE / DROP DATABASE lifecycle for that alias.

    Suitable for local development where the full TIN-X stack is available via
    Docker Compose.  The tcrd database is read-only by design (the router
    raises on any write attempt), so there is no risk of test runs mutating
    production data.
    """

    SKIP_DB_ALIASES = frozenset({"tcrd"})

    def setup_databases(self, **kwargs):
        # Before Django's setup_databases runs, patch create_test_db on each
        # skipped connection so it becomes a no-op that leaves the real
        # database name in place.
        originals = {}
        for alias in self.SKIP_DB_ALIASES:
            conn = connections[alias]
            real_name = conn.settings_dict["NAME"]
            # Ensure TEST["NAME"] matches the real DB name so Django does not
            # attempt to create a "test_<name>" database.
            conn.settings_dict.setdefault("TEST", {})["NAME"] = real_name
            # Replace create_test_db with a no-op.
            originals[alias] = conn.creation.create_test_db
            conn.creation.create_test_db = lambda *a, _name=real_name, **kw: _name

        old_config = super().setup_databases(**kwargs)

        # Restore the original methods (keeps the object clean after setup).
        for alias, original in originals.items():
            connections[alias].creation.create_test_db = original

        return old_config

    def teardown_databases(self, old_config, **kwargs):
        # Remove skipped aliases from the teardown list so Django never calls
        # destroy_test_db (which would DROP the live database).
        safe_config = [
            entry for entry in old_config if entry[0].alias not in self.SKIP_DB_ALIASES
        ]
        super().teardown_databases(safe_config, **kwargs)
