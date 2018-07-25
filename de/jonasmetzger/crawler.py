from json import JSONDecodeError

import time
import calendar
import datetime
import requests
import re
import json
import base64
from time import sleep
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5

username = "---"
password = "---"

header = {
    'Content-type': 'application/x-www-form-urlencoded',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3324.0 Safari/537.36',
}

discovered_keys = set()

def get_steam_login(username, password):
    response = requests.post("https://steamcommunity.com/login/getrsakey/", headers=header, data={'username': username})
    data = response.json()
    modCalc = int(str(response.json()['publickey_mod']), 16)
    modExp = int(str(response.json()['publickey_exp']), 16)
    rsa = RSA.construct((modCalc, modExp))
    cipher = PKCS1_v1_5.new(rsa)
    payload = {
        'username': username,
        'password': base64.b64encode(cipher.encrypt(password.encode())),
        "emailauth": "",
        "loginfriendlyname": "",
        "captchagid": "-1",
        "captcha_text": "",
        "emailsteamid": "",
        "rsatimestamp": data["timestamp"],
        "remember_login": False,
        "donotcache": str(int(time.time() * 1000)),
    }
    response = requests.post('https://steamcommunity.com/login/dologin/', headers=header, data=payload)
    if response.json()['success'] == True:
        return response.cookies.get_dict()['steamLoginSecure']
    else:
        print("failed to login!")


def activate_steam_code(steam_code, steamLoginSecure):
    cookie = {
        'sessionid': '94d492aa53ba1c9c071112b0',
        'steamLoginSecure': steamLoginSecure,
    }
    payload = {
        'product_key': steam_code,
        'sessionid': '94d492aa53ba1c9c071112b0'
    }
    read = requests.post('https://store.steampowered.com/account/ajaxregisterkey/' + str(steam_code),
                         cookies=cookie,
                         headers=header,
                         data=payload)
    json_response = json.loads(read.text)
    if json_response['success'] == 2:
        print("Key ist valide aber schon aktivert wurden.")
    elif json_response['success'] == 1:
        print("Key ist valide und wurde aktivert!")
    else:
        print("Key unvalide. Code: " + str(json_response['success']))


def collect_promoted_posts():
    read = requests.get('https://pr0gramm.com/api/items/get?flags=1&promoted=1')
    while not read.status_code == 200:
        sleep(0.1)
        read = requests.get('https://pr0gramm.com/api/items/get?flags=1&promoted=1')
    json_object = json.loads(read.text)
    full_posts = list()
    for posts in json_object['items']:
        full_posts.append(posts['id'])
    return full_posts


def collect_new_posts():
    read = requests.get('https://pr0gramm.com/api/items/get?flags=2')
    while not read.status_code == 200:
        sleep(0.1)
        read = requests.get('https://pr0gramm.com/api/items/get?flags=2')
    json_object = json.loads(read.text)
    full_posts = list()
    for posts in json_object['items']:
        full_posts.append(posts['id'])


    return full_posts


def get_comments_from_post(id):
    read = requests.get('https://pr0gramm.com/api/items/info?itemId=' + str(id))
    while not read.status_code == 200:
        sleep(0.1)
        read = requests.get('https://pr0gramm.com/api/items/info?itemId=' + str(id))
    if (read.status_code == 200):
        json_object = json.loads(read.content.decode("utf-8"))
        comments = list()
        for comment in json_object['comments']:
            comment_pair = dict()
            comment_pair['content'] = comment['content']
            comment_pair['created'] = comment['created']
            comments.append(comment_pair)
    return comments

counter = 0
while True:
    print("Durchlauf: " + str(counter))
    counter += 1
    for posts in collect_new_posts():
        for comment_pair in get_comments_from_post(posts):
            comment = comment_pair['content']
            regExpression = re.compile(r"[A-Z0-9]{5}-[A-Z0-9]{5}-[A-Z0-9]{5}")
            found = regExpression.search(comment)
            if found:
                key = found.group(0)
                if key not in discovered_keys:
                    print("found potencial steam key: " + key)
                    activate_steam_code(key, get_steam_login(username, password))
                    discovered_keys.add(key)