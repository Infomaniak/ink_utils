import re


class Rule:
    def matches(self, input_string):
        raise NotImplementedError

    def warn(self, language, string_id, string_value):
        print(get_string_id_header(language, string_id) + self.get_explanation(string_value))

    def get_explanation(self, string_value):
        raise NotImplementedError("Rule did not specify an explanation message")


def get_string_id_header(language, string_id):
    return f"[{language}] {string_id}: "


class ExistenceRule(Rule):
    def __init__(self, sequence):
        self.sequence = sequence

    def matches(self, input_string):
        return input_string.__contains__(self.sequence)

    def get_explanation(self, string_value):
        return f"found forbidden sequence [{self.sequence}]"


class FrenchEmailRule(Rule):
    def __init__(self):
        self.pattern = re.compile(r"(?P<adresse>adresses?)?\s(?P<email>(e-|e)?mails?)")
        self.reason = None

    def matches(self, input_string):
        results = re.search(self.pattern, input_string.lower())
        if results is None:
            return False

        email_wording = results.group("email")
        if results.group("adresse") is None:
            self.reason = "e-mail"
            return email_wording.startswith("mail")
        else:
            self.reason = "adresse mail"
            return email_wording.startswith("e")

    def get_explanation(self, string_value):
        return f"in french only '{self.reason}' is authorized\nFound in '{string_value}'\n"
