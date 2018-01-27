import logging


class LineageModel(object):
    def __init__(self, operation):
        self._operation = operation
        self._table = None
        self._alias = None
        self._query_alias = None
        self._joins = None
        self._models = []
        self._indent = 1

    @property
    def table(self):
        return self._table

    @table.setter
    def table(self, value):
        self._table = value

    @property
    def alias(self):
        return self._alias

    @alias.setter
    def alias(self, value):
        self._alias = value

    @property
    def query_alias(self):
        return self._query_alias

    @alias.setter
    def query_alias(self, value):
        self._query_alias = value

    @property
    def joins(self):
        return self._joins

    @joins.setter
    def joins(self, value):
        self._joins = value

    @property
    def operation(self):
        return self._operation

    def set_indent(self, indent):
        self._indent = indent

    def connect_model(self, model):
        self._models.append(model)
        model.set_indent(self._indent+1)

    def count_models(self):
        count = 1
        for model in self._models:
            count += model.count_models()
        return count

    def __str__(self):
        ret = "{0};{1};{2};{3};{4}\n".format(self._operation, self._table, self._alias, self._query_alias, self._joins)
        for model in self._models:
            ret += (" " * (self._indent*4)) + str(model)
        return ret

    def recurse_tables(self, insert_tables, select_tables, aliases):
        if self._operation == 'INSERT':
            insert_tables.append(self._table)
        elif self._operation == 'WITH':
            if self._alias is not None and self._alias not in aliases:
                aliases.append(self._alias)
            if self._query_alias is not None and self._query_alias not in aliases:
                aliases.append(self._query_alias)
        elif self._operation == 'SELECT':
            if self._table not in aliases:
                select_tables.append(self._table)
            if self._alias is not None and self._alias not in aliases:
                aliases.append(self._alias)
            if self._query_alias is not None and self._query_alias not in aliases:
                aliases.append(self._query_alias)

            if self._joins is not None:
                joined_tables = self._joins.split(",")
                for elem in joined_tables:
                    table, alias = elem.split("|")
                    if table not in aliases and table not in select_tables:
                        select_tables.append(table)

        for model in self._models:
            model.recurse_tables(insert_tables, select_tables, aliases)

    def collect_tables(self):
        select_tables = []
        insert_tables = []
        aliases = []

        self.recurse_tables(insert_tables, select_tables, aliases)
        return insert_tables, select_tables
