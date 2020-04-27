import psycopg2
import discord_token
import discord
# import main
from psycopg2.extensions import AsIs
from psycopg2 import sql
import psycopg2.extras

DATABASE_URL = discord_token.DATABASE_URL

global connection
global cursor


def ident_or_literal(s):
    if type(s) == str:
        return sql.Identifier(s)
    else:
        return sql.Literal(s)


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


def select_request(columns='*', tables=('guild',), limit=(), where={}):
    if columns == "*":
        sql_command = "SELECT * FROM {tables}"
    else:
        sql_command = "SELECT {columns} FROM {tables}"
    if where:
        if where['sign'] in ["=", '>', '<', 'LIKE']:
            sql_command += " WHERE {where_field} " + where["sign"] + " {where_value}"
    if limit:
        sql_command += " LIMIT {limit}"
    sql_command += ';'
    sql_command = sql.SQL(sql_command).format(columns=sql.SQL(", ").join(sql.Identifier(column) for column in columns),
                                              tables=sql.SQL(", ").join([sql.Identifier(table) for table in tables]),
                                              where_field=sql.Identifier(where["where_field"]),
                                              where_value=sql.Literal(where["where_value"]),
                                              limit=sql.Literal(limit))
    cursor.execute(sql_command)
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
            pre_value = sql.SQL("")
            for value in values:
                if pre_value != sql.SQL(""):
                    pre_value += sql.SQL(", ")
                pre_value += sql.SQL("(") + sql.SQL(", ").join(sql.Literal(value_part) for value_part in value) + sql.SQL(")")
            print(pre_value.as_string(connection))
            cursor.execute(sql.SQL(sql_command).format(table=sql.Identifier(table),
                                                       columns=sql.SQL(", ").join(
                                                           [sql.Identifier(column) for column in columns]),
                                                       values=pre_value))
        # вставка одного значения
        else:
            cursor.execute(sql.SQL(sql_command).format(table=sql.Identifier(table),
                                                       columns=sql.SQL(", ").join(
                                                           [sql.Identifier(column) for column in columns]),
                                                       values=sql.SQL("(") + sql.SQL(", ").join(
                                                           sql.Literal(value) for value in values) + sql.SQL(")")))
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


if __name__ == "__main__":
            open_connection()
            init_db()
            close_connection()
