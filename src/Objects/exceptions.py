class InvalidNodeIDError(Exception):
    def __init__(self, s):
        self.s = s
        super().__init__(self.s)
