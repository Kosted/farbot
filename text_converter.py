import re


def spam(text):
    default_len = len(text)
    not_a_latter_counter = 0
    if default_len > 20:
        for symbol in text:
            if symbol not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ" \
                             "абвгдеёжзийклмнопрстуяхцчшщъыьэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУЯХЦЧШЩЪЫЬЭЮЯ":
                not_a_latter_counter += 1
        if not_a_latter_counter*3 > default_len:
            print("spam!")
            return True
    for i in range(len(text)-4):
        # print(text[i:i+5])
        if text[i:i+5] == text[i]*5:
            print("spam!")
            return True
    return False


def remove_non_alphanumeric(text):
    return re.sub(r'\W+', '', text)

# print('*'+ remove_non_alphanumeric("Wamy (артем)")+ '*')
# if spam("aadfadf     aaaaab"):
#     print("true")
# else:
#     print("false")