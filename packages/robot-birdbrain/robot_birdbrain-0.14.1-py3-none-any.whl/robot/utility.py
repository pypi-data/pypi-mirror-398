import inspect


class Utility:
    @staticmethod
    def caller(index=2):
        return inspect.getouterframes(inspect.currentframe(), 2)[index].function

    @staticmethod
    def is_none_or_empty(s):
        if s is None or s == "":
            return True

        return False

    @staticmethod
    def bounds(utility_input, input_min, input_max):
        if int(utility_input) < int(input_min):
            return int(input_min)
        if int(utility_input) > int(input_max):
            return int(input_max)

        return int(utility_input)

    @staticmethod
    def decimal_bounds(utility_input, input_min, input_max):
        if float(utility_input) < float(input_min):
            return float(input_min)
        if float(utility_input) > float(input_max):
            return float(input_max)

        return float(utility_input)

    @staticmethod
    def flatten_string(original_list, divider="/"):
        if isinstance(original_list[0], list):
            original_list = original_list[0]

        original_list = list(original_list)

        s = ""
        for element in list(original_list):
            if isinstance(element, str):
                s += str(element) + divider
            elif isinstance(element, int):
                s += str(element) + divider
            else:
                for sub_element in element:
                    s += str(sub_element) + divider

        return s[:-1]
