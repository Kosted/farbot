import psycopg2
import discord_token
import discord
import main


DATABASE_URL = discord_token.DATABASE_URL

global connection
global cursor





def open_connection():
    global connection
    global cursor
    connection = psycopg2.connect(discord_token.DATABASE_URL, sslmode='require')
    cursor = connection.cursor()
    # Print PostgreSQL Connection properties
    print(connection.get_dsn_parameters(), "\n")


def close_connection():
    cursor.close()
    connection.close()
    print("PostgreSQL connection is closed")


def init_db():

    try:
        cursor.execute("SELECT * FROM guild LIMIT 1")
        print("База данных существует")
    except (Exception, psycopg2.Error) as error:
        connection.commit()
        print("База данных еще не создана. Приступаю", error)
        with open("requestFiles/db_structure", "r") as db_struct:
            # create_db_commands = db_struct.read()
            line: str = None
            command = ''
            while line != '':
                line = db_struct.readline()
                if not line.startswith(('--', '\n')):
                    if line.startswith('\t'):
                        line = line[1:]
                    if line.endswith('\n'):
                        line = line[:-1] + ' '
                    command += line
            cursor.execute(command)
            connection.commit()



# while True:
#     try:
#         connection = psycopg2.connect(discord_token.DATABASE_URL, sslmode='require')
#
#         cursor = connection.cursor()
#         # Print PostgreSQL Connection properties
#         print(connection.get_dsn_parameters(), "\n")
#
#         # request = input("request: \n")
#         # while request.lower() not in ["stop", "e", "exit"]:
#         # if request =="s":
#         #
#         #     with open("db_structure.txt", "r") as file:
#         #         request = file.read()
#         #     cursor.execute(request)
#         #
#         #     record = cursor.fetchall()
#         #     print("record =" + record + ";")
#         # else:
#         with open("requestFiles/text2.txt", "r") as file:
#             request = file.read()
#             print(request)
#             cursor.execute(request)
#
#             print("record =")
#             responce = cursor.fetchall()
#             for record in responce:
#                 print(str(record))
#
#         # connection.commit()
#
#     except (Exception, psycopg2.Error) as error:
#         print("Error while connecting to PostgreSQL", error)
#     finally:
#         # closing database connection.539879904506806282
#         if connection:
#             cursor.close()
#             connection.close()
#             print("PostgreSQL connection is closed")


if __name__ == "__main__":
    open_connection()
    init_db()
    close_connection()
