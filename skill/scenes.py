import datetime
import inspect
import sys
from typing import List

from skill import diary_api, texts
from skill.alice import Request, button, image_button, image_list
from skill.constants import entities, intents, state
from skill.scenes_util import Scene
from skill.schemas import PlannedLesson, Student
from skill.tools import ya_date_transform

# region Общие сцены

# класс общая сцена


class GlobalScene(Scene):
    def reply(self, request: Request):
        pass  # Здесь не нужно пока ничего делать

    def handle_global_intents(self, request):

        # Должны быть обработаны в первую очередь
        if intents.HELP in request.intents:
            return HelpMenu()
        if intents.WHAT_CAN_YOU_DO in request.intents:
            return WhatCanDo()
        if intents.CLEAN in request.intents:
            return ClearSettings()

        # Глобальные команды
        if intents.GET_SCHEDULE in request.intents:
            return get_scene_for_schedule(request)
        if intents.MAIN_MENU in request.intents:
            return Todo()

    def handle_local_intents(self, request: Request):
        pass  # Здесь не нужно пока ничего делать

    def fallback(self, request: Request):
        if request.session.get(state.NEED_FALLBACK, False):
            text, tts = texts.sorry_and_goodbye()
            return self.make_response(request, text, tts, end_session=True)
        else:
            save_state = {}
            # Сохраним важные состояние
            for save in state.MUST_BE_SAVE:
                if save in request.session:
                    save_state.update({save: request.session[save]})
            save_state[state.NEED_FALLBACK] = True
            text, tts = texts.help_menu_fallback()
            return self.make_response(
                request,
                text,
                tts,
                buttons=HELP,
                state=save_state,
            )


class Welcome(GlobalScene):
    def reply(self, request: Request):
        text, tts = texts.hello()
        buttons = [
            button("Что ты умеешь?"),
        ]

        return self.make_response(
            request,
            text,
            tts,
            buttons=buttons,
            directives={"start_account_linking": {}},
            user_state=None
        )

    def handle_local_intents(self, request: Request):
        if intents.REJECT in request.intents:
            return MaybeHelp()

        if request.authorization_complete:
            return Todo()


class Todo(GlobalScene):
    def reply(self, request: Request):

        students = get_all_students_from_request(request)
        user_state_students = []
        if not students:
            students = diary_api.get_students(request.access_token)
            user_state_students = [x.dump() for x in students]

        todo = _prepare_todo_list(request.access_token, students)
        cards = _prepare_cards_todo(todo)
        text, tts = texts.todo_list(todo)
        return self.make_response(
            request,
            text,
            tts,
            card=image_list(cards, header=text),
            buttons=[button("Расписание уроков"), button("Расписание на завтра")],
            user_state={state.STUDENTS: user_state_students}
        )

    def handle_local_intents(self, request: Request):
        if intents.CONFIRM in request.intents:
            return get_scene_for_schedule(request)


class Goodbye(GlobalScene):
    def reply(self, request: Request):
        text, tts = texts.goodbye()
        return self.make_response(request, text, tts, end_session=True)


class SorryAndGoodbye(GlobalScene):
    def reply(self, request: Request):
        text, tts = texts.sorry_and_goodbye()
        return self.make_response(request, text, tts, end_session=True)


class HaveMistake(GlobalScene):
    def reply(self, request: Request):
        text, tts = texts.mistake()
        return self.make_response(request, text, tts, end_session=True)


class MaybeHelp(GlobalScene):
    def reply(self, request: Request):
        text, tts = texts.maybe_you_need_help()
        return self.make_response(request, text, tts, buttons=YES_NO)

    def handle_local_intents(self, request: Request):
        if intents.CONFIRM in request.intents:
            return HelpMenu()
        elif intents.REJECT in request.intents:
            return Goodbye()


class WhatCanDo(GlobalScene):
    def reply(self, request: Request):
        text, tts = texts.what_can_i_do()
        return self.make_response(
            request,
            text,
            tts,
            buttons=YES_NO,
            state={},
        )

    def handle_local_intents(self, request: Request):
        if intents.CONFIRM in request.intents:
            return HelpMenu()
        if intents.REJECT in request.intents:
            return Welcome()


class HelpMenu(GlobalScene):
    def reply(self, request: Request):
        students = get_all_students_from_request(request)

        text, tts = texts.help_menu_start(students)
        return self.make_response(
            request,
            text,
            tts,
            buttons=YES_NO
        )

    def handle_local_intents(self, request: Request):
        if intents.CONFIRM in request.intents:
            return HelpMenu_Schedule()
        elif intents.REJECT in request.intents:
            return HelpMenu_SuggestSpec()


class HelpMenu_Schedule(GlobalScene):
    def reply(self, request: Request):
        text, tts = texts.help_menu_schedule()
        return self.make_response(request, text, tts, buttons=YES_NO)

    def handle_local_intents(self, request: Request):
        if intents.CONFIRM in request.intents:
            return HelpMenu_Spec()
        if intents.REJECT in request.intents:
            return Welcome()


class HelpMenu_SuggestSpec(GlobalScene):
    def reply(self, request: Request):
        text, tts = texts.help_menu_suggest_spec()
        return self.make_response(request, text, tts, buttons=YES_NO)

    def handle_local_intents(self, request: Request):
        if intents.CONFIRM in request.intents:
            return HelpMenu_Spec()
        if intents.REJECT in request.intents:
            return Welcome()


class HelpMenu_Spec(GlobalScene):
    def reply(self, request: Request):
        text, tts = texts.help_menu_spec()
        return self.make_response(request, text, tts, buttons=DEFAULT_BUTTONS)


# endregion


# region base scenario


class GetSchedule(GlobalScene):
    def __init__(self, student=None):
        self.student = student

    def reply(self, request: Request):
        context = request.session.get(state.TEMP_CONTEXT, {})
        req_date = get_date_from_request(request)
        if (
            req_date is None
            and context is not None
            and context.get("request_date") is not None
        ):
            req_date = datetime.datetime.strptime(
                context.get("request_date"), "%Y-%m-%d"
            )

        lessons_list = diary_api.get_schedule_on_date(
            request.access_token,
            self.student.id,
            req_date,
        )
        text_title, tts_title = texts.title(self.student, req_date)
        if not lessons_list:
            text, tts = texts.no_schedule()
            return self.make_response(
                request,
                text_title + ". " + text,
                tts_title + " " + tts,
                buttons=DEFAULT_BUTTONS,
            )
        else:
            text, tts = texts.tell_about_schedule(lessons_list)
            return self.make_response(
                request,
                text_title + ". " + text,
                tts_title + " " + tts,
                buttons=DEFAULT_BUTTONS,
            )

    def handle_local_intents(self, request: Request):

        if intents.CONFIRM in request.intents:
            context = request.session.get(state.TEMP_CONTEXT, {})
            student = Student(**context.get("student"))
            return GetSchedule(student)
        if intents.REJECT in request.intents or intents.MAIN_MENU in request.intents:
            return Welcome()


class ChooseStudentSchedule(GlobalScene):
    def __init__(self):
        self.wrong_choice = False

    def reply(self, request: Request):

        req_date = get_date_from_request(request)
        students = get_all_students_from_request(request)
        cards = _prepare_cards_student(students)
        text, tts = texts.choose_schedule(students)
        return self.make_response(
            request,
            text,
            tts,
            card=image_list(cards, header=text),
            state={
                state.TEMP_CONTEXT: {
                    "request_date": req_date
                    if req_date is None
                    else datetime.datetime.strftime(req_date, "%Y-%m-%d")
                }
            },
        )

    def handle_local_intents(self, request: Request):
        if entities.FIO in request.entities_list:
            student = exist_student_in_saved(request)
            if student is not None:
                return GetSchedule(student)
            else:
                self.wrong_choice = True

    def fallback(self, request):
        return choose_student_fallback(self, request)


# endregion

# region debug


class ClearSettings(GlobalScene):
    def reply(self, request: Request):

        return self.make_response(
            request, "Сброс", "Сброс", state={}, user_state={state.STUDENTS: None}, end_session=True
        )


# endregion


def global_fallback(self, request: Request, texts_response):
    if request.session.get(state.NEED_FALLBACK, False):
        text, tts = texts.sorry_and_goodbye()
        return self.make_response(request, text, tts, end_session=True)
    else:
        text, tts = texts_response
        return self.make_response(
            request,
            text,
            tts,
            buttons=HELP,
            state={state.NEED_FALLBACK: True},
        )


def choose_student_fallback(self, request: Request):
    if request.session.get(state.NEED_FALLBACK, False):
        text, tts = texts.sorry_and_goodbye()
        return self.make_response(request, text, tts, end_session=True)
    else:
        students = get_all_students_from_request(request)
        cards = _prepare_cards_student(students)
        if self.wrong_choice:
            text, tts = texts.wrong_student_fallback(students)
        else:
            text, tts = texts.choose_student_fallback(students)
        return self.make_response(
            request,
            text,
            tts,
            card=image_list(cards, header=text),
            state={
                state.NEED_FALLBACK: True,
                state.TEMP_CONTEXT: request.session.get(state.TEMP_CONTEXT),
            },
        )


# region Helpers


def get_date_from_request(request: Request):
    if entities.DATETIME in request.entities_list:
        ya_date = request.entity(entities.DATETIME)[0]
        ya_date = ya_date_transform(ya_date)
    elif intents.DAY in request.intents:
        day = request.slot(intents.DAY, "Day")
        delta = DAYS.index(day) - datetime.date.today().weekday()
        if delta < 0:
            delta += 7
        ya_date = datetime.datetime.today() + datetime.timedelta(days=delta)
    else:
        ya_date = None

    return ya_date


def get_scene_for_schedule(request: Request):

    students = get_all_students_from_request(request)

    if len(students) > 1:
        context = request.session.get(state.TEMP_CONTEXT)
        if entities.FIO in request.entities_list:
            name = request.entity(entities.FIO)[0]["first_name"].capitalize()
            search = [x for x in students if x == name]
            if not search:
                return ChooseStudentSchedule()
            else:
                student = search[0]
        elif context is not None and "student" in context:
            student = Student(**context.get("student"))
        else:
            return ChooseStudentSchedule()
    else:
        student = students[0]

    return GetSchedule(student)


def get_all_students_from_request(request: Request) -> List[Student]:
    saved_list = request.user.get(state.STUDENTS, [])
    students = [Student(**s) for s in saved_list]

    return students


def exist_student_in_saved(request: Request):
    students = get_all_students_from_request(request)
    name = request.entity(entities.FIO)[0]["first_name"].capitalize()
    search = [x for x in students if x == name]
    if not search:
        student = None
    else:
        student = search[0]

    return student


def get_lessons_from_request(request: Request, name_of_intent: str):
    # Выделим предметы. Их может не быть
    lessons = []
    slots = request.intents.get(name_of_intent, {}).get("slots", {})
    for i in range(1, 10):
        subject = "subject" + str(i)
        if subject in slots:
            lesson = slots.get(subject).get("value")
            lessons = lessons + entities.subjects.get(lesson)

    return lessons


# endregion


def _prepare_cards_lessons(lessons: List[PlannedLesson]):
    return [
        image_button(title=str(x), description=x.duration, image_id=x.link_url)
        for x in lessons
    ]


def _prepare_cards_student(students: List[Student]):
    return [
        image_button(title=x.name.capitalize(), button_text=x.name.capitalize())
        for x in students
    ]


def _prepare_cards_todo(todo):
    return [
        image_button(
            title=name.capitalize(),
            description=f"Уроков: {tasks}",
        )
        for name, tasks in todo.items()
    ]


def _prepare_todo_list(token: str, students: List[Student]):
    result = {}
    for student in students:
        result[student.name] = len(diary_api.get_schedule_on_date(token, student.id))
    return result


def _list_scenes():
    current_module = sys.modules[__name__]
    scenes = []
    for name, obj in inspect.getmembers(current_module):
        if inspect.isclass(obj) and issubclass(obj, Scene):
            scenes.append(obj)
    return scenes


SCENES = {scene.id(): scene for scene in _list_scenes()}

DEFAULT_SCENE = Todo
WELCOME_SCENE = Welcome
YES_NO = [button("Да"), button("Нет")]
HELP = [button("Помощь")]
DEFAULT_BUTTONS = [
    button("Расписание на завтра"),
    button("Главное меню"),
]
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
