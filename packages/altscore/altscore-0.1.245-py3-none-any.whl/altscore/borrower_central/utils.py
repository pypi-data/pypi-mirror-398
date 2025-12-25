import stringcase


def clean_dict(d: dict) -> dict:
    return {k: v for k, v in d.items() if v is not None}


def convert_to_dash_case(s):
    snake_case = stringcase.snakecase(s)
    return stringcase.spinalcase(snake_case)
