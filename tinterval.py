__author__ = 'emptysamurai'


class tinterval:
    @property
    def start(self):
        return self._start

    @start.setter
    def start(self, value):
        if self.end < value:
            raise ValueError("End of the interval is earlier than start")
        self._start = value

    @property
    def end(self):
        return self._end

    @end.setter
    def end(self, value):
        if value < self.start:
            raise ValueError("End of the interval is earlier than start")
        self._end = value

    def __init__(self, start, end):
        if end < start:
            raise ValueError("End of the interval is earlier than start")
        self._start = start
        self._end = end

    def length(self):
        return self.end - self.start

    @classmethod
    def between(cls, start, end):
        return cls(start.end, end.start)