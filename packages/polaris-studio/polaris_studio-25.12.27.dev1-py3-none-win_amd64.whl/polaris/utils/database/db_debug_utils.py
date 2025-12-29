# Copyright (c) 2025, UChicago Argonne, LLC
# BSD OPEN SOURCE LICENSE. Full license can be found in LICENSE.md

import os
import gc
import sqlite3
from pathlib import Path


def real(p):
    return os.path.realpath(str(p))


def open_fds_pointing_to(path):
    path = real(path)
    hits = []
    for fd in os.listdir("/proc/self/fd"):
        try:
            target = os.readlink(f"/proc/self/fd/{fd}")
            if real(target) == path:
                hits.append(int(fd))
        except Exception:
            continue
    return hits


def find_sqlite3_connections():
    conns = []
    for obj in gc.get_objects():
        try:
            if isinstance(obj, sqlite3.Connection):
                conns.append(obj)
        except Exception:
            # some objects may error on isinstance - ignore
            continue
    return conns


def describe_open_connections(where):
    py_conns = find_sqlite3_connections()
    print(f"Found {len(py_conns)} sqlite3.Connection objects at {where}")
    for c in py_conns:
        print(describe_sqlite_conn(c))


def describe_sqlite_conn(conn):
    try:
        in_tx = getattr(conn, "in_transaction", None)
        if callable(in_tx):
            in_tx = in_tx()
        filename = Path(conn.execute("PRAGMA database_list").fetchall()[0][2]).absolute()
        return {
            "repr": repr(conn),
            "in_transaction": in_tx,
            "timeout": getattr(conn, "timeout", None),
            "isolation_level": getattr(conn, "isolation_level", None),
            "filename": str(filename),
        }
    except Exception as e:
        return {"repr": repr(conn), "error": str(e)}
