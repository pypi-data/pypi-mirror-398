# Copyright (c) 2025, UChicago Argonne, LLC
# BSD OPEN SOURCE LICENSE. Full license can be found in LICENSE.md
import logging
from datetime import datetime, timezone
from typing import Any, Dict, NamedTuple

import pandas as pd
from polaris.hpc.eqsql.eq_db import CANCELLED, CANCELLING, QUEUED, RUNNING, tasks_table
from polaris.hpc.eqsql.utils import clear_idle_pg_connection
from polaris.hpc.eqsql.utils import from_cursor_result, from_id, from_row, update_from_db, update_to_db
from polaris.utils.str_utils import outdent
from sqlalchemy import func, text


class Task(NamedTuple):
    task_id: int
    task_type: int
    worker_id: str
    exp_id: str
    priority: int
    definition: Dict[str, Any]
    input: str
    output: str
    status: str
    message: str
    running_on: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    @clear_idle_pg_connection()
    def from_id(cls, engine, task_id):
        return from_id(cls, engine, task_id)

    @classmethod
    @clear_idle_pg_connection()
    def from_exp_id(cls, engine, exp_id):
        with engine.connect() as conn:
            stmt = tasks_table.select().filter(tasks_table.c.exp_id == exp_id).order_by(tasks_table.c.task_id.desc())
            return from_cursor_result(cls, conn.execute(stmt))

    @classmethod
    def by_exp_id(cls, engine, exp_id):
        with engine.connect() as conn:
            stmt = tasks_table.select().filter(tasks_table.c.exp_id == exp_id).order_by(tasks_table.c.task_id.desc())
            return [from_row(cls, row) for row in conn.execute(stmt)]

    @classmethod
    def last(cls, engine, limit=1):
        with engine.connect() as conn:
            stmt = tasks_table.select().order_by(tasks_table.c.task_id.desc()).limit(limit)
            rows = conn.execute(stmt).fetchall()
            rv = [from_row(cls, row) for row in rows] if rows else []
            return rv[0] if limit == 1 and rv else rv

    @classmethod
    def query(cls, engine, **kwargs):
        """Used to query tasks based on arbitrary criteria.
        Syntax is to pass keyword arguments corresponding to column names and criteria for filtering as the argument
        Supported formats:
            - single value: equality filtering
            - list of values: 'in' filtering
            - tuple: (condition: str, value: Any)
        Condition operators supported for tuple format:
            - '==', '!=', '<', '<=', '>', '>='
        Special keywords:
            - as_df: bool (default True) - return a pandas DataFrame if True, else a list of Task objects
            - limit: int - limit the number of returned records
        """
        as_df = kwargs.pop("as_df") if "as_df" in kwargs else True

        with engine.connect() as conn:
            stmt = tasks_table.select()
            for key, value in kwargs.items():
                if key == "limit":
                    stmt = stmt.limit(value)
                elif isinstance(value, list):
                    stmt = stmt.filter(getattr(tasks_table.c, key).in_(value))
                elif isinstance(value, tuple):
                    cond, x = value
                    x = pd.to_datetime(x).to_pydatetime() if key in ["created_at", "updated_at"] else x

                    if cond == "==":
                        stmt = stmt.filter(getattr(tasks_table.c, key) == x)
                    elif cond == "!=":
                        stmt = stmt.filter(getattr(tasks_table.c, key) != x)
                    elif cond == "<":
                        stmt = stmt.filter(getattr(tasks_table.c, key) < x)
                    elif cond == "<=":
                        stmt = stmt.filter(getattr(tasks_table.c, key) <= x)
                    elif cond == ">":
                        stmt = stmt.filter(getattr(tasks_table.c, key) > x)
                    elif cond == ">=":
                        stmt = stmt.filter(getattr(tasks_table.c, key) >= x)
                    elif cond.lower() == "like":
                        stmt = stmt.filter(getattr(tasks_table.c, key).like(f"%{x}%"))
                    else:
                        raise ValueError(f"Unsupported condition operator: {cond}")
                else:
                    stmt = stmt.filter(getattr(tasks_table.c, key) == value)

            stmt = stmt.order_by(tasks_table.c.task_id.desc())
            records = [from_row(cls, row) for row in conn.execute(stmt)]
            return pd.DataFrame([r._asdict() for r in records]) if as_df else records

    def __repr__(self):
        task_type = self.definition["task-type"]

        def indent_subsequent_lines(x):
            lines = str(x).splitlines()
            if len(lines) == 0:
                return "| "
            return "\n".join(["| " + lines[0]] + ["        | " + e for e in lines[1:]])

        input = indent_subsequent_lines(str(self.input))
        output = indent_subsequent_lines(str(self.output))
        return (
            outdent(
                f"""
            Task(id={self.task_id}, type={task_type}, priority={self.priority}, status={self.status}, running_on={self.running_on})
              in  = xx__input__xx
              out = xx__output__xx
        """
            )
            .replace("xx__input__xx", input)
            .replace("xx__output__xx", output)
        )

    def get_logs(self, engine):
        with engine.connect() as conn:
            logs = pd.read_sql(text(f"SELECT * FROM task_log where task_id = {self.task_id}"), conn)
            return logs.sort_values("created_at")

    def cancel(self, engine):
        task = self.update_from_db(engine)

        if task.status == QUEUED:
            values = {"status": CANCELLED, "message": "Cancelled while queued"}
        elif task.status == RUNNING:
            values = {"status": CANCELLING, "message": "Cancelling a running task"}
        else:
            logging.info(f"Can't cancel task {self.task_id} as its status = {task.status}")
            return task

        return task.update_to_db(engine, updated_at=func.now(), **values)

    def delete(self, engine):
        """Delete this task from the database."""
        task = self.update_from_db(engine)
        if task.status == RUNNING:
            raise RuntimeError(f"Can't delete task {self.task_id} as its status = {task.status}")
        with engine.connect() as conn:
            stmt = tasks_table.delete().where(tasks_table.c.task_id == self.task_id)
            result = conn.execute(stmt)
            conn.commit()
            return result.rowcount > 0

    def mark_failed(self, engine, update_worker=True, status="failed"):
        """Useful if a worker has gone offline without informing the database"""
        updated_message = f"DEAD: {self.message}" if not self.message.startswith("DEAD") else self.message
        update_to_db(self, engine, status=status, message=updated_message)
        if self.running_on is not None and update_worker:
            from polaris.hpc.eqsql.worker import Worker

            worker = Worker.from_id(engine, self.running_on)
            if worker.task_id == self.task_id:
                worker.mark_dead(engine, update_task=False)

    def queue(self, engine, worker_id=None, message=None, force=False):
        if self.status not in ["waiting", "failed"] and not force:
            raise RuntimeError(f"Can't queue task {self.task_id}, it has status = {self.status}")
        values = {"status": "queued", "output": None, "running_on": None}
        values["message"] = "Requeued" if message is None else message
        if worker_id is not None:
            values["worker_id"] = worker_id
        self.update_to_db(engine, **values)

    def check_worker(self, engine, timeout=None):
        """Check that the worker this task is purportedly running on lists this task as it's current task."""
        from polaris.hpc.eqsql.worker import Worker

        if self.status != "running":
            return True
        worker = Worker.from_id(engine, self.running_on)
        return worker is not None and worker.task_id == self.task_id

    def check_updated_ago(self, timeout):
        """Check that the last update on this task is within the given timeout limit."""

        timeout = pd.Timedelta(timeout).to_pytimedelta() if isinstance(timeout, str) else timeout
        return self.updated_ago < timeout

    @property
    def updated_ago(self):
        return datetime.now(timezone.utc) - self.updated_at

    @property
    def primary_key(self):
        return self.task_id

    def update_from_db(self, engine):
        return update_from_db(self, engine)

    def update_to_db(self, engine, **kwargs):
        return update_to_db(self, engine, **kwargs)

    @classmethod
    def table(cls):
        return tasks_table

    @classmethod
    def key_col(cls):
        return tasks_table.c.task_id
