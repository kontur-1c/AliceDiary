import json
from urllib.request import Request, urlopen

from skill.constants.entities import images

secrets = json.load(open("skill/secrets.json"))

url_load = f"https://dialogs.yandex.net/api/v1/skills/{secrets['dialog_id']}/images"

req = Request(url_load, method="POST")
req.add_header("Authorization", f" OAuth {secrets['ya_token']}")
req.add_header("Content-Type", "application/json")

image_array = {}

for key, value in images.items():
    if not value:
        continue
    d = f'{{"url": "{value}"}}'.encode("utf-8")
    req.add_header("Content-Length", len(d))
    resp = urlopen(req, d)
    content = resp.read().decode("utf-8")
    datacon = json.loads(content)
    image_array[key] = datacon["image"]["id"]

json.dump(image_array, fp=open("skill/image.json", mode="w"), separators="\n")
