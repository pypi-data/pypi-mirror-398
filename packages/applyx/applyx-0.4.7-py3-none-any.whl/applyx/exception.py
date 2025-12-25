# coding=utf-8


class InternalException(Exception):
    def __init__(self, msg: str):
        self.msg = msg

    def __str__(self):
        return self.msg

    def __repr__(self):
        return f'{self.__class__.__name__}({self.msg})'
