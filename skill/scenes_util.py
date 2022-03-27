import json
import logging
from abc import ABC, abstractmethod
from typing import Optional

from skill.alice import Request
from skill.constants.state import (
    PERMANENT_VALUES,
    PREVIOUS_MOVES,
    STATE_RESPONSE_KEY,
    USERSTATE_RESPONSE_KEY,
)


class Scene(ABC):

    temp_context = dict()

    @classmethod
    def id(cls):
        return cls.__name__

    """Генерация ответа сцены"""

    @abstractmethod
    def reply(self, request):
        raise NotImplementedError()

    """Проверка перехода к новой сцене"""

    def move(self, request: Request):
        next_scene = self.handle_local_intents(request)
        if next_scene is None:
            next_scene = self.handle_global_intents(request)
        return next_scene

    @abstractmethod
    def handle_global_intents(self, request):
        raise NotImplementedError()

    @abstractmethod
    def handle_local_intents(self, request: Request) -> Optional[str]:
        raise NotImplementedError()

    @abstractmethod
    def fallback(self, request: Request):
        raise NotImplementedError()

    def make_response(
        self,
        request: Request,
        text,
        tts=None,
        card=None,
        state=None,
        user_state=None,
        buttons=None,
        directives=None,
        end_session=False,
    ):
        response = {
            "text": text[:1024],
            "tts": tts[:1024] if tts is not None else text[:1024],
        }
        if card:
            response["card"] = card
        if buttons:
            response["buttons"] = buttons
        if directives is not None:
            response["directives"] = directives
        if end_session:
            response["end_session"] = end_session

        webhook_response = {
            "response": response,
            "version": "1.0",
            STATE_RESPONSE_KEY: {
                "scene": self.id(),
            },
        }

        if state == {}:
            webhook_response[STATE_RESPONSE_KEY] = {}
        else:
            for key, value in request.session.items():
                if key in PERMANENT_VALUES:
                    webhook_response[STATE_RESPONSE_KEY][key] = value
            if state is not None:
                webhook_response[STATE_RESPONSE_KEY].update(
                    (k, v) for k, v in state.items() if v is not None
                )
        if user_state is not None:
            webhook_response[USERSTATE_RESPONSE_KEY] = user_state

        prev_moves = request.session.get(PREVIOUS_MOVES, [])
        prev_moves.append(request.command)
        webhook_response[STATE_RESPONSE_KEY][PREVIOUS_MOVES] = prev_moves[-10:]

        logging.debug(f"RESPONSE {json.dumps(webhook_response, ensure_ascii=False)}")

        return webhook_response
