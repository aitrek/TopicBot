"""Self-defined Error"""


class ConfigDataError(Exception):

    def __init__(self):
        err = "Configs data has not been loaded!"
        super().__init__(err)


class MsgError(Exception):

    def __init__(self):
        err = "The input message key field error!"
        super().__init__(err)
