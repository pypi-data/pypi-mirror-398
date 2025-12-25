class InvalidInput(Exception):
    """
    Custom exception for invalid input errors from Rubika API.
    """

    def __init__(self, error: dict):
        self.error = error

    def __str__(self):
        return f'InvalidInputError(status={self.error.get("status")}, dev_message={self.error.get("dev_message")})'