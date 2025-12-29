import datetime


def get_string_date():
    """Returns the current date formatted as "Month Day, Year".

    For example: "January 14, 2025".
    """
    today = datetime.date.today()  # Get the current date
    return today.strftime("%B %d, %Y")
