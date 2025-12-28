class ToRowsRequiredError(Exception):
    def __init__(
        self,
        message: str = "A function to turn tables into rows must be provided when they aren't in row form already or from a supported provider",
    ) -> None:
        super().__init__(message)
