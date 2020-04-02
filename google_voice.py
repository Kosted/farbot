# import requests
# import json
#
# url = 'https://domain.com'
# headers = {'Content-type': 'application/json',  # Определение типа данных
#            'Accept': 'text/plain',
#            'Content-Encoding': 'utf-8'}
# data = {"user_info" : [{"username" : "<user login>",
#                        "key" : "<api_key>"},
#                       {}]}  # Если по одному ключу находится несколько словарей, формируем список словарей
# answer = requests.post(url, data=json.dumps(data), headers=headers)
# print(answer)
# response = answer.json()
# print(response)


# import pyttsx3
#
# tts = pyttsx3.init()
#
# voices = tts.getProperty('voices')
#
# # Задать голос по умолчанию
#
# tts.setProperty('voice', 'ru')
#
# # Попробовать установить предпочтительный голос
#
# for voice in voices:
#
#     if voice.name == 'Aleksandr':
#
#         tts.setProperty('voice', voice.id)
#
# tts.say('мне мама сказала что у них продлят карантин!')
#
# tts.runAndWait()

from gtts import gTTS


def convert_text_to_voice(text):
    tts = gTTS(text, lang='ru')
    temp = text[:40]
    path = "/home/mcs/PycharmProjects/first_bot/Farbot/voice files/" + temp + ".mp3"
    tts.save(path)
    print("create mp3: " + temp)
    return path
