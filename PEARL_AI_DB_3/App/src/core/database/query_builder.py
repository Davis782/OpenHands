from typing import List, Dict, Tuple

class QueryBuilder:
    """
    A Python-based SQL Query Builder for constructing dynamic SQL queries.
    Supports SELECT, FROM, JOIN, WHERE, GROUP BY, ORDER BY, LIMIT, and OFFSET clauses.
    """

    def __init__(self):
        self._select_columns: List[str] = []
        self._from_table: str = ""
        self._joins: List[str] = []
        self._where_conditions: List[str] = []
        self._group_by_columns: List[str] = []
        self._order_by_columns: List[str] = []
        self._limit: int | None = None
        self._offset: int | None = None
        self._params: Dict[str, any] = {}

    def select(self, columns: List[str]) -> 'QueryBuilder':
        """
        Specifies the columns to be selected.
        """
        self._select_columns = columns
        return self

    def from_table(self, table_name: str) -> 'QueryBuilder':
        """
        Specifies the primary table for the query.
        """
        self._from_table = table_name
        return self

    def join(self, table: str, on_condition: str, join_type: str = 'INNER') -> 'QueryBuilder':
        """
        Adds a JOIN clause to the query.
        """
        self._joins.append(f"{join_type.upper()} JOIN {table} ON {on_condition}")
        return self

    def where(self, condition: str, params: Dict[str, any] = None) -> 'QueryBuilder':
        """
        Adds a WHERE clause condition and its associated parameters.
        Conditions should use named parameters (e.g., 'column = :param_name').
        """
        self._where_conditions.append(condition)
        if params:
            self._params.update(params)
        return self

    def group_by(self, columns: List[str]) -> 'QueryBuilder':
        """
        Adds a GROUP BY clause.
        """
        self._group_by_columns = columns
        return self

    def order_by(self, columns: List[str]) -> 'QueryBuilder':
        """
        Adds an ORDER BY clause.
        """
        self._order_by_columns = columns
        return self

    def limit(self, count: int) -> 'QueryBuilder':
        """
        Adds a LIMIT clause.
        """
        self._limit = count
        return self

    def offset(self, count: int) -> 'QueryBuilder':
        """
        Adds an OFFSET clause.
        """
        self._offset = count
        return self

    def build(self) -> Tuple[str, Dict[str, any]]:
        """
        Compiles all the stored components into a complete SQL string and a dictionary of parameters.
        """
        if not self._from_table:
            raise ValueError("FROM table must be specified.")

        sql_parts = []

        # SELECT
        select_clause = ", ".join(self._select_columns) if self._select_columns else "*"
        sql_parts.append(f"SELECT {select_clause}")

        # FROM
        sql_parts.append(f"FROM {self._from_table}")

        # JOIN
        if self._joins:
            sql_parts.append(" ".join(self._joins))

        # WHERE
        if self._where_conditions:
            sql_parts.append(f"WHERE {" AND ".join(self._where_conditions)}")

        # GROUP BY
        if self._group_by_columns:
            sql_parts.append(f"GROUP BY {", ".join(self._group_by_columns)}")

        # ORDER BY
        if self._order_by_columns:
            sql_parts.append(f"ORDER BY {", ".join(self._order_by_columns)}")

        # LIMIT
        if self._limit is not None:
            sql_parts.append(f"LIMIT {self._limit}")

        # OFFSET
        if self._offset is not None:
            sql_parts.append(f"OFFSET {self._offset}")

        return " ".join(sql_parts), self._params

    def insert(self, **kwargs) -> 'QueryBuilder':
        """
        Specifies data for an INSERT query.
        """
        self._insert_data = kwargs
        self._params.update(kwargs)
        return self

    def build_insert(self) -> Tuple[str, Dict[str, any]]:
        """
        Compiles the INSERT query.
        """
        if not self._from_table:
            raise ValueError("FROM table must be specified for INSERT.")
        if not self._insert_data:
            raise ValueError("No data provided for INSERT.")

        columns = ", ".join(self._insert_data.keys())
        placeholders = ", ".join([f":{col}" for col in self._insert_data.keys()])
        sql = f"INSERT INTO {self._from_table} ({columns}) VALUES ({placeholders})"
        return sql, self._params

    def update(self, **kwargs) -> 'QueryBuilder':
        """
        Specifies data for an UPDATE query.
        """
        self._update_data = kwargs
        self._params.update(kwargs)
        return self

    def build_update(self) -> Tuple[str, Dict[str, any]]:
        """
        Compiles the UPDATE query.
        """
        if not self._from_table:
            raise ValueError("FROM table must be specified for UPDATE.")
        if not self._update_data:
            raise ValueError("No data provided for UPDATE.")
        if not self._where_conditions:
            raise ValueError("WHERE clause must be specified for UPDATE.")

        set_clauses = ", ".join([f"{col} = :{col}" for col in self._update_data.keys()])
        sql = f"UPDATE {self._from_table} SET {set_clauses} WHERE {" AND ".join(self._where_conditions)}"
        return sql, self._params

    def delete(self) -> 'QueryBuilder':
        """
        Marks the query as a DELETE operation.
        """
        self._is_delete = True
        return self

    def build_delete(self) -> Tuple[str, Dict[str, any]]:
        """
        Compiles the DELETE query.
        """
        if not self._from_table:
            raise ValueError("FROM table must be specified for DELETE.")
        if not self._where_conditions:
            raise ValueError("WHERE clause must be specified for DELETE.")

        sql = f"DELETE FROM {self._from_table} WHERE {" AND ".join(self._where_conditions)}"
        return sql, self._params
