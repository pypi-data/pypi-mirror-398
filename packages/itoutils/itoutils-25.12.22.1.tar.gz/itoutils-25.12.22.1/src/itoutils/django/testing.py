import inspect
import linecache
import os.path
import re
from collections import defaultdict
from contextlib import contextmanager

import sqlparse
from django.conf import settings
from django.db import DEFAULT_DB_ALIAS, connections
from django.db.backends.base import base as base_db_module
from django.db.backends.utils import CursorDebugWrapper
from django.db.backends.utils import debug_transaction as origin_debug_transaction
from django.template.base import Node
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


# List of functions that help identify the query origin
_other_packeges_allowlist = [
    ("django/core/paginator.py", "count"),
    ("django/contrib/admin/options.py", "get_object"),
    ("django/contrib/sessions/backends/db.py", "_get_session_from_db"),
    ("django/contrib/sessions/backends/db.py", "save"),
    ("django/db/models/base.py", "save"),
    ("django/db/models/query.py", "first"),
    ("django/db/transaction.py", "__enter__"),
    ("django/db/transaction.py", "__exit__"),
    ("django/forms/models.py", "initial_form_count"),
    ("django/views/generic/detail.py", "get_object"),
] + settings.ASSERT_SNAPSHOT_QUERIES_EXTRA_PACKAGES_ALLOWLIST

OTHER_PACKAGES_ALLOWLIST = defaultdict(list)
for path, function in _other_packeges_allowlist:
    OTHER_PACKAGES_ALLOWLIST[function].append(path)
OTHER_PACKAGES_ALLOWLIST = {function: tuple(paths) for function, paths in OTHER_PACKAGES_ALLOWLIST.items()}


def normalized_frame_filename(frame_info, debug):
    """If the frame needs to be included, return its normalized filename, or None otherwise"""
    frame_filename = frame_info.filename
    if frame_filename.startswith(settings.APPS_DIR):
        return os.path.relpath(frame_filename, settings.APPS_DIR)
    if (
        (allowed_filepaths := OTHER_PACKAGES_ALLOWLIST.get(frame_info.function))
        and frame_filename.endswith(allowed_filepaths)
        or debug
    ):
        if "site-packages" in frame_filename:
            return f"<site-packages>{frame_filename.split('site-packages', 1)[1]}"
        elif debug:
            return frame_filename


def get_template_source_from_exception_info(node: Node, context) -> tuple[int, str]:
    # Taken from django-debug-toolbar
    if context.template.origin == node.origin:
        exception_info = context.template.get_exception_info(Exception("DDT"), node.token)
    else:
        exception_info = context.render_context.template.get_exception_info(Exception("DDT"), node.token)
    return exception_info["line"], exception_info["name"]


def _detect_origin(debug=False):
    parts = []
    # Ignore first 3 frames:
    # - tests/utils/test.py::_detect_origin
    # - tests/utils/test.py::debug_sql
    # - <python>::contextlib.py::__exit__
    for frame_info in inspect.stack()[3:]:
        frame_filename = frame_info.filename

        if frame_info.function == "pytest_pyfunc_call" and "_pytest" in frame_filename:
            # We are now in pytest machinery, no need to inspect frames anymore
            break

        template_origin = None
        template_debug_info = None
        if frame_info.function == "render" and "django/template" in frame_filename:
            try:
                frame_self = frame_info.frame.f_locals["self"]
            except KeyError:
                pass
            else:
                if isinstance(frame_self, Node):
                    try:
                        frame_context = frame_info.frame.f_locals["context"]
                    except KeyError:
                        pass
                    else:
                        class_name = type(frame_self).__name__
                        if hasattr(frame_self, "origin"):
                            template_origin = f"{class_name}[{frame_self.origin.template_name}]"
                        else:
                            template_origin = class_name
                        # This requires the engine to be in debug mode
                        if debug:
                            template_debug_info = get_template_source_from_exception_info(frame_self, frame_context)

        if template_origin is not None:
            parts.append(template_origin)
            if debug and template_debug_info:
                parts.append(
                    f"  Line: {template_debug_info[0]} - "
                    + linecache.getline(template_debug_info[1], template_debug_info[0]).strip()
                )
        elif normalized_filename := normalized_frame_filename(frame_info, debug):
            if not debug and "get_response(request)" in linecache.getline(frame_filename, frame_info.lineno):
                # Middleware passing the request to the next: useless as an origin
                continue
            if "self" in frame_info.frame.f_locals:
                class_name = type(frame_info.frame.f_locals["self"]).__name__
                function = f"{class_name}.{frame_info.function}"
            else:
                function = frame_info.function
            parts.append(f"{function}[{normalized_filename}]")
            if debug:
                parts.append(
                    f"  Line: {frame_info.lineno} - " + linecache.getline(frame_filename, frame_info.lineno).strip()
                )
    return parts


origin_debug_sql = CursorDebugWrapper.debug_sql


@contextmanager
def debug_sql(self, sql=None, params=None, use_last_executed_query=False, many=False):
    with origin_debug_sql(self, sql, params, use_last_executed_query, many):
        yield
    # Enrich last query
    last_query = self.db.queries_log[-1]
    if not isinstance(sql, str):
        raw_sql = sql.as_string(self.cursor)
    else:
        raw_sql = sql
    last_query["raw_sql"] = raw_sql
    last_query["origin"] = _detect_origin(debug=bool(os.getenv("DEBUG_SQL_SNAPSHOT")))


CursorDebugWrapper.debug_sql = debug_sql


@contextmanager
def debug_transaction(connection, sql):
    with origin_debug_transaction(connection, sql):
        yield
    if connection.queries_log:
        last_query = connection.queries_log[-1]
        last_query["raw_sql"] = sql
        last_query["origin"] = _detect_origin(debug=bool(os.getenv("DEBUG_SQL_SNAPSHOT")))


base_db_module.debug_transaction = debug_transaction
