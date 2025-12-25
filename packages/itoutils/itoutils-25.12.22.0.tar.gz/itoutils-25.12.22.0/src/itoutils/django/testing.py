import re

import sqlparse
from django.db import DEFAULT_DB_ALIAS, connections
from django.test.utils import CaptureQueriesContext


class _AssertSnapshotQueriesContext(CaptureQueriesContext):
    def __init__(self, snapshot, connection):
        self.snapshot = snapshot
        super().__init__(connection)

    def normalize_sql(self, sql):
        if re.match(r'^SAVEPOINT +".+?" *$', sql):
            # 'SAVEPOINT "s124109847980928_x70"'
            return 'SAVEPOINT "<snapshot>"'
        if re.match(r'^RELEASE +SAVEPOINT +".+?" *$', sql):
            # 'RELEASE SAVEPOINT "s124109847980928_x69"'
            return 'RELEASE SAVEPOINT "<snapshot>"'
        if re.match(r'^ROLLBACK TO SAVEPOINT +".+?" *$', sql):
            # 'ROLLBACK TO SAVEPOINT "s128384493710208_x1309"'
            return 'ROLLBACK TO SAVEPOINT "<snapshot>"'

        return sqlparse.format(
            sql,
            keyword_case="upper",
            reindent=True,
            reindent_align=True,
            use_space_around_operators=True,
        )

    def build_snapshot(self, queries):
        return {
            "num_queries": len(queries),
            "queries": [
                {
                    "sql": self.normalize_sql(query["raw_sql"]),
                    "origin": query["origin"],
                }
                for query in queries
            ],
        }

    def __exit__(self, exc_type, exc_value, traceback):
        super().__exit__(exc_type, exc_value, traceback)
        if exc_type is not None:
            return
        new_snapshot = self.build_snapshot(self.captured_queries)
        assert new_snapshot == self.snapshot
        for item in new_snapshot["queries"]:
            assert item["origin"], f"origin is mandatory and missing for {item}"


def assertSnapshotQueries(snapshot, func=None, *args, using=DEFAULT_DB_ALIAS, **kwargs):
    conn = connections[using]

    context = _AssertSnapshotQueriesContext(snapshot, conn)
    if func is None:
        return context

    with context:
        func(*args, **kwargs)
