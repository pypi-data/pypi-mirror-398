class Sample:
    """Description of the sample. Needed for writing valid nx file"""

    def __init__(self, name: str = "undefined sample", description: dict = None):
        self.name = name
        self.description = description
