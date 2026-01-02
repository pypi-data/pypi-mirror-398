from collections.abc import Callable


class AnsiWrapperGenerator:
    '''
    Return a function to wrap around a string which will style the text
    according to the passed ANSI escape codes
    '''
    def __init__(self, no_ansi: bool):
        self.no_ansi = no_ansi
        

    def genwrapper(self, start_code: str, end_code: str) -> Callable[[str], str]:
        if self.no_ansi:
            return lambda string: string
        return lambda string: start_code + string + end_code
