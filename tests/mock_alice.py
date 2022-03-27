from functools import wraps

from fluentcheck import Check


def chained(fn):
    @wraps(fn)
    def new(*args, **kwargs):
        fn(*args, **kwargs)
        return args[0]

    return new


#########################################################
# ПОДГОТОВКА ЗАПРОСОВ
#########################################################


class AliceIntentSlot:
    def __init__(self, name: str):
        self.name = name
        self.type = ""
        self.tokens = {"start": 0, "end": 0}
        self.value = ""

    @chained
    def type(self, type: str):
        self.type = type

    @chained
    def tokens(self, start=0, end=0):
        self.tokens["start"] = start
        self.tokens["end"] = end

    @chained
    def value(self, value):
        self.value = value

    def val(self):
        result = {}
        if self.name:
            result.update(
                {
                    self.name: {
                        "type": self.type,
                        "tokens": {
                            "start": self.tokens["start"],
                            "end": self.tokens["end"],
                        },
                        "value": self.value,
                    }
                }
            )

        return result


class AliceIntent:
    def __init__(self, name=""):
        self.name = name
        self.slots = {}

    @chained
    def add_slot(self, slot: AliceIntentSlot):
        self.slots.update(slot.val())

    def val(self):
        return {self.name: self.slots}

    @chained
    def confirm(self):
        self.name = "YANDEX.CONFIRM"
        self.slots.clear()

    @chained
    def reject(self):
        self.name = "YANDEX.REJECT"
        self.slots.clear()

    @chained
    def discard(self):
        self.name = "YANDEX.REJECT"
        self.slots.clear()

    @chained
    def help(self):
        self.name = "YANDEX.HELP"
        self.slots.clear()

    @chained
    def what_can_you_do(self):
        self.name = "YANDEX.WHAT_CAN_YOU_DO"
        self.slots.clear()

    @chained
    def repeat(self):
        self.name = "YANDEX.REPEAT"
        self.slots.clear()


class AliceEntity:
    def __init__(self, type=""):
        self.type = type
        self.tokens = {"start": 0, "end": 0}
        self.value = ""

    @chained
    def tokens(self, start=0, end=0):
        self.tokens["start"] = start
        self.tokens["end"] = end

    @chained
    def value(self, value):
        self.value = value

    @chained
    def fio(self, first_name="", patronymic_name="", last_name=""):
        assert first_name or patronymic_name or last_name

        self.type = "YANDEX.FIO"
        self.value = {
            "first_name": first_name,
            "patronymic_name": patronymic_name,
            "last_name": last_name,
        }

    @chained
    def number(self, num: int):
        self.type = "YANDEX.NUMBER"
        self.value = num

    @chained
    def datetime(
        self,
        year=None,
        year_is_relative=None,
        month=None,
        month_is_relative=None,
        day=None,
        day_is_relative=None,
        hour=None,
        hour_is_relative=None,
        minute=None,
        minute_is_relative=None,
    ):
        self.type = "YANDEX.DATETIME"
        value = {
            "year": year,
            "year_is_relative": year_is_relative,
            "month": month,
            "month_is_relative": month_is_relative,
            "day": day,
            "day_is_relative": day_is_relative,
            "hour": hour,
            "hour_is_relative": hour_is_relative,
            "minute": minute,
            "minute_is_relative": minute_is_relative,
        }
        value = {k: v for k, v in value.items() if v is not None}
        self.value = value

    def val(self):
        return {"type": self.type, "value": self.value}


class AliceRequest:
    def __init__(
        self,
        has_screen=False,
        has_payments=False,
        has_account_linking=False,
        has_audio_player=False,
    ):
        self.new_session = False
        self.command = ""
        self.original_utterance = ""
        self.nlu_tokens = []
        self.intents = {}
        self.entities = []
        self.state_sessions = {}
        self.state_user = {}
        self.state_application = {}
        self.interfaces = {}
        if has_screen:
            self.interfaces["screen"] = {}
        if has_payments:
            self.interfaces["payments"] = {}
        if has_account_linking:
            self.interfaces["account_linking"] = {}
        if has_audio_player:
            self.interfaces["audio_player"] = {}

    @chained
    def new_session(self):
        self.new_session = True

    @chained
    def set_command(self, command=""):
        self.command = command
        self.set_original_utterance(command)

    @chained
    def set_original_utterance(self, original_utterance=""):
        self.original_utterance = original_utterance
        self.set_nlu_token(original_utterance.lower().split(" "))

    @chained
    def set_nlu_token(self, tokens: list):
        self.nlu_tokens = tokens

    @chained
    def add_intent(self, intent: AliceIntent):
        self.intents.update(intent.val())

    @chained
    def add_entity(self, entity: AliceEntity):
        self.entities.append(entity.val())

    @chained
    def add_to_state_session(self, name: str, value):
        self.state_sessions[name] = value

    @chained
    def add_to_state_user(self, name: str, value):
        self.state_user[name] = value

    @chained
    def add_to_state_application(self, name: str, value):
        self.state_application[name] = value

    @chained
    def from_scene(self, scene: str):
        self.add_to_state_session("scene", scene)

    def build(self):
        def meta():
            return {
                "locale": "ru-RU",
                "timezone": "UTC",
                "client_id": "AliceMock",
                "interfaces": self.interfaces,
            }

        def session(new=False):
            return {
                "message_id": 3,
                "session_id": "d825cbef-e7d6-4af9-9810-3ff3f358ac16",
                "skill_id": "3308dc06-b901-4f7e-8882-beb1b84c0753",
                "user": {"user_id": "000"},
                "application": {"application_id": "000"},
                "user_id": "000",
                "new": new,
            }

        req = {
            "meta": meta(),
            "session": session(self.new_session),
            "request": {
                "command": self.command,
                "original_utterance": self.original_utterance,
                "nlu": {
                    "tokens": self.nlu_tokens,
                    "entities": self.entities,
                    "intents": self.intents,
                },
                "markup": {"dangerous_context": False},
                "type": "SimpleUtterance",
            },
            "version": "1.0",
            "state": {
                "session": self.state_sessions,
                "user": self.state_user,
                "applications": self.state_application,
            },
        }
        return req


#########################################################
# ВАЛИДАЦИЯ ОТВЕТОВ
#########################################################


class AliceAnswer:
    def __init__(self, answer: str):

        # Базовая проверка: без этого не будет работать вообще
        Check(answer).is_not_none().is_dict().has_keys("response")
        Check(answer.get("response", {})).is_not_none().is_dict().has_keys(
            "text", "tts"
        )

        self.answer = answer

    @property
    def response(self):
        return self.answer.get("response", {})

    @property
    def text(self):
        return self.response.get("text", {})

    @property
    def tts(self):
        return self.response.get("tts", {})

    @property
    def session_state(self):
        return self.answer.get("session_state", {})

    @property
    def user_state(self):
        return self.answer.get("user_state_update", {})

    @property
    def next_scene(self):
        return self.session_state.get("scene")

    def get_state_session(self, state: str):
        return self.session_state.get(state, None)

    def get_state_user(self, state: str):
        return self.user_state.get(state, None)
