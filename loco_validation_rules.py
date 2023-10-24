class Rule:
    def check(self, input_string):
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

    def check(self, input_string):
        return input_string.__contains__(self.sequence)

    def get_explanation(self, string_value):
        return f"found forbidden sequence [{self.sequence}]"
