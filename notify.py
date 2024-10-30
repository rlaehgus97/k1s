import os
import requests
from discordwebhook import Discord

LINE_URL = 'https://notify-api.line.me/api/notify'
LINE_TOKEN = os.getenv("LINE_NOTI_TOKEN")
DISCORD_URL = 'https://discordapp.com/api/webhooks/1301083910544822323/idrjNS5svHTmDdSwS1Bzy5MZUzT2byDFFCUxrrRB_olSBstdJ_TFJYnJsvux5eVkd7_8'

def line_notify(message = '안녕하세요. LINE Notify 테스트입니다.'):
    response = requests.post(
        LINE_URL,
        headers = {'Authorization': 'Bearer ' + LINE_TOKEN},
        data = {'message': message}
    )
    return response.text

def discord_notify(message = '안녕하세요. DISCORD Notify 테스트입니다.'):
    discord = Discord(url=DISCORD_URL)
    discord.post(content = message)
    # data = {"content":message}
    # response = requests.post(DISCORD_URL, json=data)
    # if response.status_code != 204:
    #     print(f"Discord 알림을 보내는데 실패하였습니다: {response.status_code}")

def notifies(message = '안녕하세요. 알림 Notify 테스트입니다.'):
    line_notify(message)
    discord_notify(message)

       
