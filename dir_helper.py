# import requests
#
# url = "https://tts.p.rapidapi.com/v1/tts/voices"
#
# querystring = {"language":"One of the available languages (see %2Fv1%2Ftts%2Flanguages)"}
#
# headers = {
#     'x-rapidapi-host': "tts.p.rapidapi.com",
#     'x-rapidapi-key': "5e81cb3a3bmsha0b0866b7509c91p18bde2jsn76ad7bf48cff"
#     }
#
# response = requests.request("GET", url, headers=headers, params=querystring)
#
# print(response.text)

from os import listdir
from os.path import isfile, join


def file_list(path):

    temp = []
    onlyfiles = [f for f in listdir(path) if isfile(join(path, f))]
    for name in onlyfiles:
        temp.append(name[:-4])
    # res = str(res)
    return temp

# print(file_list())

# from pydub import AudioSegment
# from pydub.playback import play
#
# song = AudioSegment.from_wav("/home/mcs/Загрузки/nioce.mp3")
# play(song)