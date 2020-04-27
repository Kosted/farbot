import json, os

TOKEN = None
DATABASE_URL = None
DEBUG = False

try:
    file = open("config.json", 'r')
    config = json.load(file)

    TOKEN = config['TOKEN']
    print("TOKEN найден в config файле")

    DATABASE_URL = config['DATABASE_URL']
    print("DATABASE_URL найден в config файле")

    DEBUG = True
    print("Запущен DEBUG мод")

except:

    print("File with token doesn't exist.\nTry to search on env variable...")

    count = 0
    while TOKEN is None:

        try:

            TOKEN = os.environ['TOKEN']
            print("TOKEN обанружен в системных переменных")

            DATABASE_URL = os.environ['DATABASE_URL']
            print("DATABASE_URL обанружен в системных переменных")

        except:

            count += 1
            print(count, ". Поиск токена и ссылки на бд в системных переменных...")

# print("TOKEN: " + TOKEN)
# print("DATABASE_URL: " + DATABASE_URL)
