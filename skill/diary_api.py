import os
from datetime import date, datetime, time
from typing import List

import requests

from skill.schemas import PlannedLesson, Student


class NotFoundError(Exception):
    pass


# region URLs


def base_url():
    if os.environ.get("DEBUG", "False").lower() in ("true", "1", "t"):
        url = "https://journal.bpo.edu.n3demo.ru/api/journal"
    else:
        url = "https://dnevnik2.petersburgedu.ru/api/journal"

    return url


def schedule_url():
    return f"{base_url()}/schedule/list-by-education"


def students_url():
    return f"{base_url()}/person/related-child-list"


# endregion


def get_schedule_on_date(token: str, id: str, day=None) -> List[PlannedLesson]:

    if day is None:
        day = date.today()

    start_time = datetime.combine(day, time.min)
    finish_time = datetime.combine(day, time.max)

    response = requests.get(
        schedule_url(),
        params={
            "p_educations[]": id,
            "p_datetime_from": datetime.strftime(start_time, "%d.%m.%Y %H:%M:%S"),
            "p_datetime_to": datetime.strftime(finish_time, "%d.%m.%Y %H:%M:%S"),
        },
        cookies={"X-JWT-Token": token},
    )

    if response.status_code == 500:
        return []

    result = []
    for lesson in response.json().get("data", {}).get("items", []):
        lesson_from = datetime.strptime(
            lesson["datetime_from"], "%d.%m.%Y %H:%M:%S"
        ).time()
        lesson_to = datetime.strptime(lesson["datetime_to"], "%d.%m.%Y %H:%M:%S").time()
        result.append(
            PlannedLesson(lesson["subject_name"], lesson_from, lesson_to),
        )
    return sorted(result)


def get_students(token: str) -> List[Student]:
    response = requests.get(students_url(), cookies={"X-JWT-Token": token})

    if response.status_code == 401:
        raise Exception("Не удалось авторизоваться")

    result = []
    for student in response.json().get("data", {}).get("items", []):
        name = student.get("firstname", "")
        id = student.get("educations", [])[0].get("education_id", "")
        result.append(Student(name, id))

    return result
