import json, os

TOKEN = None
DATABASE_URL = None

try:
    file = open("config.json", 'r')
    config = json.load(file)
    TOKEN = config['TOKEN']
    DATABASE_URL = config['DATABASE_URL']
except:
    print("file with token doesn't exist")

while TOKEN is None:

    try:
        TOKEN = os.environ['TOKEN']
        DATABASE_URL = os.environ['DATABASE_URL']
    except:
        print("TOKEN ищется")


# print("TOKEN: " + TOKEN)
# print("DATABASE_URL: " + DATABASE_URL)

print("TOKEN найден")
print("DATABASE_URL найден")
