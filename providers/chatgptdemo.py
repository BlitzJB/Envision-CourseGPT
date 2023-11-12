import requests
import re

uid_cache = None

def get_user_id():
    global uid_cache
    if uid_cache:
        return uid_cache
    url = "https://chat.chatgptdemo.net"
    response = requests.get(url)
    if response.status_code == 200:
        pattern = r'<div id="USERID" style="display: none">(\w+)</div>'
        match = re.search(pattern, response.text)
        if match:
            uid_cache = match.group(1)
            return uid_cache
        raise Exception("Could not find user id")
    return None

def clear_uid_cache():
    global uid_cache
    uid_cache = None


chatid_cache = None

def get_chat_id():
    global chatid_cache
    if chatid_cache:
        return chatid_cache
    url = "https://chat.chatgptdemo.net/get_user_chat"
    response = requests.post(url, json={"user_id": get_user_id()})
    chatid_cache = response.json()["_id"]
    return chatid_cache