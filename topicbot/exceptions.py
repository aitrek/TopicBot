"""Module to handle kinds of exceptions/errors"""


class ConfigDataError(Exception):

    def __init__(self):
        err = "Configs data has not been loaded!"
        super().__init__(err)


class MsgError(Exception):

    def __init__(self):
        err = "The user input message field error!"
        super().__init__(err)
