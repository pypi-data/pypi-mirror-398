
class MissingArgumentException(Exception):
    def __init__(self,
                 argument_name: str,
                 intent: str = None
                 ):
        self.argument_name = argument_name
        self.intent = intent
        super().__init__()

    def __str__(self):
        return f"The named argument {self.argument_name} was missing from the provided **kwargs set. {self.intent if self.intent else ''}"