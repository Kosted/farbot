import json, os

TOKEN = None

try:
    file = open("config.json", 'r')
    TOKEN = json.load(file)['TOKEN']
except:
    print("file with token doesn't exist")

while TOKEN is None:

    try:
        TOKEN = os.environ['TOKEN']
    except:
        pass


print(TOKEN)
