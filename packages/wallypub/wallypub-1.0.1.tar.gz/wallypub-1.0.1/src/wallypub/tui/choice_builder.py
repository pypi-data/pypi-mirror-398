from InquirerPy.base import Choice


def choice_builder(*options) -> list[Choice]:
    """
    choice_builder is a variadic function that takes n options and
    returns a list of InquirerPy choices.

    Calling out that there is some automagic in the Choice dataclass that faithfully works as the key in
    the settings and secrets updates.
    """
    choice_list = []
    for opt in options:
        choice_list.append(Choice(opt))
    return choice_list
