class FieldError(Exception):
    def __init__(self, detail):
        super().__init__()
        self.detail= detail

    def __str__(self) -> str:
        return self.detail
