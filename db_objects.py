import psycopg2
from psycopg2 import sql


class Where:
    sign = sql.SQL('=')

    def __init__(self, column, value, sign=None):
        if sign is not None:
            if sign in ('>', '<', 'LIKE'):
                self.sign = sql.SQL(sign)
        self.column = sql.Identifier(column)
        self.value = sql.Literal(value)

    def get_compose(self):
        return self.column + self.sign + self.value

    def __add__(self, other):
        return self.get_compose() + other

    def __radd__(self, other):
        return other + self.get_compose()

    def __call__(self, *args, **kwargs):
        return self.get_compose()


class ColumnsAndValue(Where):
    def __init__(self, column, value):
        super().__init__(column, value, None)


class Values(Where):
    def __init__(self, *args):
        self.values = [sql.Literal(arg) for arg in args]

    def get_compose(self):
        return sql.SQL("(") + sql.SQL(",").join(self.values) + sql.SQL(")")


# class Array(Values):
#     def get_compose(self):
#         return sql.SQL('ARRAY[') + sql.SQL(",").join(self.values) + sql.SQL(']')


def ident_or_literal(s):
    if type(s) == str:
        return sql.Identifier(s)
    else:
        return sql.Literal(s)


def unfold_list_and_use_class(arg, class_obj, need_call=True, sep=','):

    if type(arg[0]) in (list, tuple):
        pre_join_elements = [class_obj(*elem) for elem in arg]
        if need_call:
            return sql.SQL(sep).join([elem() for elem in pre_join_elements])
        else:
            return sql.SQL(sep).join(pre_join_elements)
    elif need_call:
        return class_obj(*arg)()
    else:
        return sql.SQL(sep).join([class_obj(elem) for elem in arg])
