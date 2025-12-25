class Validator:
    """
    Abstract class
    """

    def __init__(self, *, exiting: bool):
        self._exiting = exiting

    def validate(self):
        """
        Abstract method
        Validates some condition.
        raises if invalid
        :return:
        """
