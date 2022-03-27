from datetime import date, datetime, time
from typing import List

import requests

from skill.constants.urls import BASE_URL
from skill.schemas import PlannedLesson, Student


class NotFoundError(Exception):
    pass


def get_schedule_on_date(token: str, id: str, day=None) -> List[PlannedLesson]:

    if day is None:
        day = date.today()

    start_time = datetime.combine(day, time.min)
    finish_time = datetime.combine(day, time.max)

    response = requests.get(
        BASE_URL + "/schedule/list-by-education",
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
    response = requests.get(
        f"{BASE_URL}/person/related-child-list", cookies={"X-JWT-Token": token}
    )

    if response.status_code == 401:
        raise Exception("Не удалось авторизоваться")

    result = []
    for student in response.json().get("data", {}).get("items", []):
        name = student.get("firstname", "")
        id = student.get("educations", [])[0].get("education_id", "")
        result.append(Student(name, id))

    return result
