class ValidationError(ValueError):

    @property
    def message(self):
        return str(self)
