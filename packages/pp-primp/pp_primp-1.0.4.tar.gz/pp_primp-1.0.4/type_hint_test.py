import pp_primp
import requests
import json


headers = {
    "accept": "application/json; charset=utf-8",
    "accept-language": "en,zh-CN;q=0.9,zh;q=0.8,zh-HK;q=0.7",
    "cache-control": "no-cache",
    "content-type": "text/plain; charset=utf-8",
    "origin": "https://booking.philippineairlines.com",
    "pragma": "no-cache",
    "priority": "u=1, i",
    "referer": "https://booking.philippineairlines.com/booking/manage-booking/retrieve",
    "sec-ch-ua": "\"Google Chrome\";v=\"143\", \"Chromium\";v=\"143\", \"Not A(Brand\";v=\"24\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36"
}

url = "https://booking.philippineairlines.com/Reland-to-him-Macb-Tilly-Hye-is-my-liues-vpon-th/3nOsRQ8irc_ZtcVNrFJG8gbVR_3mK-NK2L-00vw-NqY"
params = {
    "d": "booking.philippineairlines.com"
}
data = {
    "f": "gpc"
}
data = json.dumps(data, separators=(',', ':'))
response = pp_primp.post(url, headers=headers, params=params, data=data,proxy='http://127.0.0.1:7890')
response2 = requests.post(url, headers=headers, params=params, data=data,proxies={'all':'http://127.0.0.1:7890'})

print(response.text)
print(response)

print(response2.text)
print(response2)