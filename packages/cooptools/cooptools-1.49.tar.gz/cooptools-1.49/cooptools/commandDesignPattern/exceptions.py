
class ResolveStateException(Exception):
    def __init__(self, command, inner: Exception):
        print(f"Unable to execute command: {command}"
              f"\n{inner}")
        super().__init__()


class ResolveBatchException(Exception):
    def __init__(self, batch, inner: Exception):
        print(f"Unable to execute batch: {batch}"
              f"\n{inner}")
        super().__init__()
