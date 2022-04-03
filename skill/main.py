import logging
import os
import sys

import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration

from skill.alice import Request
from skill.constants.intents import GET_SCHEDULE
from skill.constants.state import PREVIOUS_MOVES
from skill.scenes import DEFAULT_SCENE, SCENES, WELCOME_SCENE

logging.basicConfig()

logging.getLogger().setLevel(logging.DEBUG)
logging.getLogger("requests.packages.urllib3").setLevel(logging.DEBUG)
# handler = logging.StreamHandler(sys.stdout)
# handler.setLevel(logging.DEBUG)
# root.addHandler(handler)

root_handler = logging.getLogger().handlers[0]
root_handler.setFormatter(logging.Formatter("[%(levelname)s]\t%(name)s\t%(request_id)s\t%(message)s\n"))


def handler(event, context):

    # если контекст пустой - это отладка или тесты
    if context is not None:
        sentry_logging = LoggingIntegration(
            level=logging.INFO, event_level=logging.ERROR
        )
        sentry_sdk.init(
            dsn=(
                "https://9e08c21c38da43de9c475699b61ab6d4@o241410"
                ".ingest.sentry.io/5974885"
            ),
            integrations=[sentry_logging],
            environment="development"
            if os.environ["DEBUG"] == "True"
            else "production",
        )

    request = Request(event)

    current_scene_id = get_id_scene(request)
    logging.info(f"Current scene: {current_scene_id}")
    logging.debug(f"Current event: {event}")

    try:

        # Проверка, что пользователь авторизован
        if request.access_token is None:
            # Токена нет. Скорее всего первый запуск или был выход из навыка
            return WELCOME_SCENE().reply(request)

        if current_scene_id is None:
            return DEFAULT_SCENE().reply(request)

        current_scene = SCENES.get(current_scene_id, DEFAULT_SCENE)()
        next_scene = current_scene.move(request)

        if next_scene is not None:
            logging.info(f"Moving from scene {current_scene.id()} to {next_scene.id()}")
            return next_scene.reply(request)
        else:
            logging.warning(
                f"Failed to parse user request at scene {current_scene.id()}"
            )
            return current_scene.fallback(request)

    except Exception as e:
        moves = request.session.get(PREVIOUS_MOVES, [])
        logging.exception(e, extra={"moves": moves})
        message = SCENES.get("HaveMistake")()
        return message.reply(request)


def get_id_scene(request: Request):
    res = request.session.get("scene")
    if res is None and GET_SCHEDULE in request.intents:
        res = "get_schedule"

    return res
