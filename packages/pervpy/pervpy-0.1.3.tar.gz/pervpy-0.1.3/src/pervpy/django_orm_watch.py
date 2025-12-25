# Python
import time
from typing import Literal, Optional

# Django
from django.db import connections as db_connections, reset_queries
from django.db.backends.base.base import BaseDatabaseWrapper
    

class DjangoORMQuery:

    def __init__(self, raw_dict: dict[str, str]):
        # Saving the dict received the `queries` properties of the connection
        self.query_data: dict[str, str] = raw_dict
        
        # The time calculated 
        self.time: str = raw_dict.get("time", "0")
        
        # Saving the different verbosity levels of the query
        qs: str = raw_dict.get("sql", "None")
        self.query_type: Literal["select", "update", "insert", "delete", "other"] = "other"
        self.model_name = "unknown"
        self.query: dict[int, str] = {
            1: qs,
            2: qs,
            3: qs,
        }
        
        # Processing `SELECT` queries
        if qs.startswith("SELECT"):
            self.model_name = qs.split('FROM "')[1].split('"')[0]
            self.query_type = "select"

            before_from = qs.split("FROM")[0]
            after_from = qs.split("FROM")[1]

            # Django doesn't use SELECT * FROM ...
            # Instead, it uses SELECT "user"."id", "user"."name", ... FROM ...
            # So, to shorten it, we count the items and add it between the SELECT and FROM
            field_count = len(before_from.split(","))
            if field_count > 1:
                self.query[1] = f"SELECT ({field_count} fields) FROM {self.model_name}"
                self.query[2] = f"SELECT ({field_count} fields) FROM{after_from}"
            else:
                self.query[1] = f"{before_from} FROM {self.model_name}"
        
        # Processing `INSERT` queries
        elif qs.startswith("INSERT"):
            self.model_name = qs.split('INTO "')[1].split('"')[0]
            self.query_type = "insert"

            before_values = qs.split("VALUES")[0]
            after_values = ")".join(qs.split(")")[2:])

            field_count = len(before_values.split(","))
            if field_count > 1:
                self.query[1] = f"INSERT INTO {self.model_name} ({field_count} fields)"
                self.query[2] = f"INSERT INTO {self.model_name} ({field_count} fields){after_values}"
            else:
                self.query[1] = f"INSERT INTO {self.model_name}"

        # Processing `UPDATE` queries
        elif qs.startswith("UPDATE"):
            self.model_name = qs.split('UPDATE "')[1].split('"')[0]
            self.query_type = "update"

            set_statement = qs.split('" SET')[1].split(' WHERE "')[0]
            after_set = qs.split(' WHERE "')[1]

            field_count = len(set_statement.split(', "'))
            if field_count > 1:
                self.query[1] = f"UPDATE {self.model_name} ({field_count} fields)"
                self.query[2] = f'UPDATE {self.model_name} ({field_count} fields) WHERE "{after_set}'
            else:
                self.query[1] = f"UPDATE {self.model_name}"

        # Processing `DELETE` queries
        elif qs.startswith("DELETE"):
            self.model_name = qs.split('FROM "')[1].split('"')[0]
            self.query_type = "delete"
            self.query[1] = f"DELETE FROM {self.model_name}"


class DjangoORMWatch:

    def __init__(self, only_for_result=False):
        """Creates a new instance of `DjangoORMWatch`. If you can create an instance before
        the code you wish to watch and have access to the instance, keep the `only_for_result`
        as False.
        
        If, however, you cannot keep access to the instance, use the static `reset_queries` to
        reset the saved queries and then use the static `eval` function to get the queries
        """
        if not only_for_result:
            # Clearing the connection history
            reset_queries()
            # Starting the total timer
            self.start = time.perf_counter_ns()
            # Then end time, will be set after calling the `stop` function
            self.end: int = self.start
        else:
            self.start = None
            self.end = None
        
        # Setting the empty connection list
        self.connections: list[BaseDatabaseWrapper] = []

    @classmethod
    def start(cls) -> 'DjangoORMWatch':
        """A convenience function to create an instance of `DjangoORMWatch` which
        in turn, starts watching for ORM queries

        Returns:
            DjangoORMWatch: A new instance of the class
        """
        return cls()


    def stop(self) -> 'DjangoORMWatch':
        """Stops the watch and stores the queries for further processing
        """
        # Stopping the end timer
        if self.start is not None:
            self.end = time.perf_counter_ns()

        # Storing the final queries
        self.connections: list[BaseDatabaseWrapper] = db_connections.all()
        self.queries: list[DjangoORMQuery] = []
        
        for c in self.connections:
            for q in c.queries:
                self.queries.append(DjangoORMQuery(q))
        
        return self
    
    @staticmethod
    def _print_queries(*, queries: list[DjangoORMQuery], connections: list[BaseDatabaseWrapper], verbosity: Literal[0, 1, 2, 3] = 2, start: Optional[int] = None, end: Optional[int] = None):
        v = verbosity
        if verbosity not in [0, 1, 2, 3]:
            v = 2
        duration: Optional[int] = None
        if start is not None and end is not None and start > 0 and end > 0:
            duration = (end - start) / 1_000_000 # nanosecond to millsecond
        
        if verbosity > 0:
            print("******************************")
            print(f"Start of queries - Verbosity level {v}" + (" (original)" if v == 3 else ""))
            print("******************************")
            
            index = 1
            for q in queries:
                print("-=-=-=-==-=")
                print(f"No. {index}")
                print(f"Model: {q.model_name}")
                print(f"Time: {q.time}")
                print("-")
                print(q.query[v])
                print("-=-=-=-==-=")
                index += 1

            print("******************************")
            print("End of queries")

        print("******************************")
        print("Overview of the queries:")
        if len(connections) > 0:
            print(f"\tConnections: {len(connections)}")
        print(f"\tQueries: {len(queries)}")
        if duration is not None and duration > 0:
            print(f"\tTime: {duration: .2f} ms")
        print("******************************")
             
    
    def print(self, verbosity: Literal[0, 1, 2, 3] = 2):
        """Prints the query data and their overview

        By passing the verbosity level, you can choose how detailed the queries should be printed

        Args:
            verbosity (Literal[0, 1, 2, 3], optional): The verbosity level of the queries. Defaults to 2.
        """
        self._print_queries(
            queries=self.queries,
            connections=self.connections,
            start=self.start,
            end=self.end,
            verbosity=verbosity,
        )

    @staticmethod
    def reset_queries():
        reset_queries()
    
    @staticmethod
    def eval() -> 'DjangoORMWatch':
        return DjangoORMWatch(only_for_result=True).stop()
