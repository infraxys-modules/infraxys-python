class BaseException(Exception):

    def __init__(self, label):
        self.label = label

    def __str__(self):
        return "BaseException: {}".format(self.label)


class UnauthorizedException(BaseException):

    def __str__(self):
        return "UnauthorizedException: {}".format(self.label)


class BadRequestException(BaseException):

    def __str__(self):
        return "BadRequestException: {}".format(self.label)


class NotFoundException(BaseException):

    def __str__(self):
        return "NotFoundException: {}".format(self.label)
