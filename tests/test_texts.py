from fluentcheck import Check

import skill.texts as texts

dictionary = []

class test_CheckRightTexts:
    def test_hello(self):
        text, tts = texts.hello()
        Check(text).is_not_none().is_string().contains_char(
            "Привет! Это цифровой дневник для Санкт-Петербурга."
        ).contains_char("Готовы продолжить?")


class test_CheckGrammar:
    def test_hello(self):
        text = texts.hello()
