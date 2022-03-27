STATE_RESPONSE_KEY = "session_state"
USER_STATE_RESPONSE_KEY = "user_state_update"

GEOLOCATION_ALLOWED = "Geolocation.Allowed"
GEOLOCATION_REJECTED = "Geolocation.Rejected"


class Request:
    def __init__(self, request_body):
        self.request_body = request_body

    def __getitem__(self, key):
        return self.request_body[key]

    @property
    def command(self):
        return self.request_body.get("request", {}).get("original_utterance", "")

    @property
    def tokens(self):
        return self.request_body.get("request", {}).get("nlu", {}).get("tokens", [])

    @property
    def intents(self):
        return self.request_body.get("request", {}).get("nlu", {}).get("intents", {})

    @property
    def entities_list(self):
        return [
            entity["type"]
            for entity in self.request_body.get("request", {})
            .get("nlu", {})
            .get("entities", [])
        ]

    @property
    def type(self):
        return self.request_body.get("request", {}).get("type")

    @property
    def session(self) -> dict:
        return self.request_body.get("state", {}).get("session", {})

    @property
    def user(self):
        return self.request_body.get("state", {}).get("user", {})

    @property
    def application(self):
        return self.request_body.get("state", {}).get("application", {})

    @property
    def access_token(self):
        return (
            self.request_body.get("session", {})
            .get("user", {})
            .get("access_token", None)
        )

    @property
    def authorization_complete(self):
        return self.request_body.get("account_linking_complete_event") is not None

    def slots(self, intent: str):
        return (
            self.request_body.get("request", {})
            .get("nlu", {})
            .get("intents", {})
            .get(intent, {})
            .get("slots", {})
            .keys()
        )

    def slot(self, intent: str, slot: str):
        return (
            self.request_body.get("request", {})
            .get("nlu", {})
            .get("intents", {})[intent]
            .get("slots", {})
            .get(slot, {})
            .get("value", None)
        )

    def entity(self, entity_type: str):
        return [
            entity["value"]
            for entity in self.request_body.get("request", {})
            .get("nlu", {})
            .get("entities", [])
            if entity["type"] == entity_type
        ]


def big_image(image_id: list, title=None, description=None):
    my_image = {"type": "BigImage", "image_id": image_id}
    if title:
        my_image["title"] = title
    if description:
        my_image["description"] = description

    return my_image


def image_list(
    image_ids: list,
    header="",
    footer="",
    button_text="",
    button_url="",
    button_payload="",
):
    card = {
        "type": "ItemsList",
        "items": image_ids,
    }
    if header:
        card["header"] = {"text": header}
    if footer or button_text or button_url or button_payload:
        card["footer"] = dict()
        if footer:
            card["footer"]["text"] = footer
        if button_text or button_url or button_payload:
            card["footer"]["button"] = dict()
            if button_text:
                card["footer"]["button"]["text"] = button_text
            if button_url:
                card["footer"]["button"]["url"] = button_url
            if button_payload:
                card["footer"]["button"]["payload"] = button_payload

    return card


def image_gallery(image_ids: list):
    if image_ids and image_ids[0] != "":

        items = [{"image_id": image_id} for image_id in image_ids]
        return {
            "type": "ImageGallery",
            "items": items,
        }
    else:
        return {}


def image_button(
    image_id="",
    title="",
    description="",
    button_text="",
    button_url="",
    button_payload="",
):
    image = {}
    if image_id:
        image["image_id"] = image_id
    if title:
        image["title"] = title
    if description:
        image["description"] = description
    if button_text or button_url or button_payload:
        my_button = {}
        if button_text:
            my_button["text"] = button_text
        if button_url:
            my_button["url"] = button_url
        if button_payload:
            my_button["payload"] = button_payload
        image["button"] = my_button

    return image


def button(title, payload=None, url=None, hide=False):
    my_button = {
        "title": title,
        "hide": hide,
    }
    if payload is not None:
        my_button["payload"] = payload
    if url is not None:
        my_button["url"] = url
    return my_button


def has_location(event):
    return event["session"].get("location") is not None
