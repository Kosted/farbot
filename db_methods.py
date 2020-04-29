import psycopg2
import discord_token
import discord
# import main
from psycopg2.extensions import AsIs
from psycopg2 import sql
import psycopg2.extras

from db_objects import Where, unfold_list_and_use_class, Values, ColumnsAndValue

DATABASE_URL = discord_token.DATABASE_URL

global connection
global cursor


def open_connection():
    global connection
    global cursor
    connection = psycopg2.connect(discord_token.DATABASE_URL, sslmode='require')
    cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
    # Print PostgreSQL Connection properties
    print(connection.get_dsn_parameters(), "\n")


def close_connection():
    cursor.close()
    connection.close()
    print("PostgreSQL connection is closed")


def init_db():
    """
    :return: True, if db exist
    :return: True, if db was create now
    """
    try:
        cursor.execute("SELECT * FROM guild LIMIT 1")
        print("База данных существует")
        return True
    except (Exception, psycopg2.Error) as error:
        connection.commit()
        print("База данных еще не создана. Приступаю\n", error)
        with open("requestFiles/db_structure", "r") as db_struct:
            # create_db_commands = db_struct.read()
            # line: str = None
            # command = ''
            # while line != '':
            #     line = db_struct.readline()
            #     if not line.startswith(('--', '\n')):
            #         if line.startswith('\t'):
            #             line = line[1:]
            #         if line.endswith('\n'):
            #             line = line[:-1] + ' '
            #         command += line
            # cursor.execute(command)
            cursor.execute(db_struct.read())
            connection.commit()
            return False


def update_request(table, columns_and_values,  where=()):
    sql_command = sql.SQL("UPDATE {table} SET {values} WHERE {where}").format(table=sql.Identifier(table),
                                                                              values=(unfold_list_and_use_class(
                                                                                  columns_and_values, ColumnsAndValue)),
                                                                              where=(unfold_list_and_use_class(where, Where)))
    print(sql_command.as_string(connection))
    cursor.execute(sql_command)
    connection.commit()
    # sql_command = sql_command + sql.SQL(",").join(ColumnsAndValue(*elem) for elem in columns_and_values)

    # if type(where) is list:
    #     pass
    # else:
    #
    #     sql_command = sql_command + sql.SQL(",").join(sql.Identifier(where[]))


def select_request(columns='*', tables=('guild',), limit=(), where=()):
    if columns == "*":
        sql_command = "SELECT * FROM {tables}"
    else:
        sql_command = "SELECT {columns} FROM {tables}"
    if where:
        sql_command += " WHERE {where} "
    if limit:
        sql_command += " LIMIT {limit}"
    sql_command += ';'
    sql_command = sql.SQL(sql_command).format(
        columns=unfold_list_and_use_class(columns, sql.Identifier, need_call=False),
        tables=unfold_list_and_use_class(tables, sql.Identifier, need_call=False),
        where=unfold_list_and_use_class(where, Where),
        limit=sql.Literal(limit))
    cursor.execute(sql_command)
    print(sql_command.as_string(connection))
    #    {'columns': AsIs(columns),
    # 'tables': AsIs(tables),
    # 'where': AsIs(where),
    # 'limit': limit})
    result = cursor.fetchall()
    connection.commit()
    return result


def insert_request(values, columns=(), table='guild'):
    # cursor.execute("INSERT INTO %(table)s VALUES( %(values1)s,%(values2)s, %(values3)s);", AsIs(tables))

    # c обьявлением колонок
    if columns is not None:
        sql_command = "INSERT INTO {table} ({columns}) VALUES {values};"

        # если вставляется не одно значение в таблицу
        if type(values[0]) in (list, tuple):
            # pre_value = sql.SQL("")
            # for value in values:
            #     if pre_value != sql.SQL(""):
            #         pre_value += sql.SQL(", ")
            #     pre_value += sql.SQL("(") + sql.SQL(", ").join(sql.Literal(value_part) for value_part in value) + sql.SQL(")")
            # print(pre_value.as_string(connection))
            sql_command = sql.SQL(sql_command).format(table=sql.Identifier(table),
                                                      columns=unfold_list_and_use_class(columns, sql.Identifier,
                                                                                        need_call=False),
                                                      values=unfold_list_and_use_class(values, Values))
            cursor.execute(sql_command)
        # вставка одного значения
        else:
            # sql_command = sql.SQL(sql_command).format(table=sql.Identifier(table),
            #                                           columns=unfold_list_and_use_class(columns, sql.Identifier,
            #                                                                             need_call=False),
            #                                           values=unfold_list_and_use_class(values, sql.Literal,
            #                                                                            need_call=False))
            sql_command = sql.SQL(sql_command).format(table=sql.Identifier(table),
                                                      columns=unfold_list_and_use_class(columns, sql.Identifier,
                                                                                        need_call=False),
                                                      values=unfold_list_and_use_class(values, Values))
            cursor.execute(sql_command)
            # без обьявления колонок
        # else:
        #     sql_command = "INSERT INTO %(table)s VALUES ( %(values)s );"
        #
        #     values = (", ".join(value) for value in values)
        #     cursor.execute(sql_command, {'values': AsIs(values),
        #                                  "table": AsIs(table)})
        #     # else:
        #     #     insert_method(sql_command, {'values': AsIs(", ".join(values)),
        #     #                                 "table": AsIs(table)})
        connection.commit()
        print(sql_command.as_string(connection))


if __name__ == "__main__":
    open_connection()
    init_db()
    close_connection()
