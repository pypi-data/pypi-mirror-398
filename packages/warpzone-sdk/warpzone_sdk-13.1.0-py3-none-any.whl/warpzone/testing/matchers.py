class AnyObjectOfType:
    """Type equality matcher for use in assertions."""

    def __init__(self, expected_type):
        self.expected_type = expected_type

    def __eq__(self, other):
        return isinstance(other, self.expected_type)
