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
            print("$%@$%@$% spam!")
            return True
    for i in range(len(text)-4):
        # print(text[i:i+5])
        if text[i:i+5] == text[i]*5:
            print("фффффффффффф spam!")
            return True

    if len(text) > 25 and text.count(" ") < len(text)/18:
        print("asdfll;j;asdjf spam!")
        return True

    for i in range(int(len(text) / 2)):
        for j in range(int(len(text) / 2) - 5):
            temp = str(text[i:i + j + 5])
            if text.count(temp) > 4:
                # print(text[i:i + j + 5])
                print("хух хух хух хух spam!")
                return True
    return False


def remove_non_alphanumeric(text):
    return re.sub(r'[_,-,\W]+', '', text)

# print('*'+ remove_non_alphanumeric("Wamy (артем)")+ '*')
# if spam("aadfadf     aaaaab"):
#     print("true")
# else:
#     print("false")
