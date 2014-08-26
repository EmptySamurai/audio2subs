__author__ = 'emptysamurai'


class TimeInterval:
    @property
    def begin(self):
        return self._begin

    @begin.setter
    def begin(self, value):
        if self.end < value:
            raise ValueError("End of the interval is earlier than start")
        self._begin = value

    @property
    def end(self):
        return self._end

    @end.setter
    def end(self, value):
        if value < self.begin:
            raise ValueError("End of the interval is earlier than start")
        self._end = value

    def __init__(self, begin, end):
        if end < begin:
            raise ValueError("End of the interval is earlier than start")
        self._begin = begin
        self._end = end

    def length(self):
        return self.end - self.begin

    def contains(self, time):
        return self.begin <= time <= self.end

    def is_earlier(self, time):
        return self.end < time

    def is_later(self, time):
        return self.begin > time

    @classmethod
    def between(cls, begin, end):
        return cls(begin.end, end.begin)