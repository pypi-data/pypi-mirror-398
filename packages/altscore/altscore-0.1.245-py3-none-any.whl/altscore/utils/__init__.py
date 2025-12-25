import stringcase


def divide_in_chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def convert_to_dash_case(s):
    snake_case = stringcase.snakecase(s)
    return stringcase.spinalcase(snake_case)