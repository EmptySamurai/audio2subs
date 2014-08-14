__author__ = 'emptysamurai'

import re
from tinterval import tinterval


class SubRipElement:
    @property
    def interval(self):
        return self._interval

    @interval.setter
    def interval(self, value):
        self._interval = value

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, value):
        self._text = value

    @property
    def number(self):
        return self._number

    @number.setter
    def number(self, value):
        self._number = value

    def __init__(self, number, interval, text):
        self._interval = interval
        self._text = text
        self._number = number

    def __str__(self):
        subtitle = str(self.number) + "\n"
        subtitle += self._ms_to_str(self.interval.start) + " ---> " + self._ms_to_str(self.interval.end) + "\n"
        subtitle += self.text
        if self.text[len(self.text) - 1] != "\n":
            subtitle += "\n"
        subtitle += "\n"
        return subtitle

    @staticmethod
    def _ms_to_str(ms):
        ms /= 1000
        total_seconds = int(ms)
        after_point = ms - total_seconds
        hours = total_seconds // 3600
        total_seconds -= hours * 60 * 60
        minutes = total_seconds // 60
        total_seconds -= minutes * 60
        milliseconds = int(round(after_point * 1000))
        return str(hours) + ":" + str(minutes) + ":" + str(total_seconds) + "," + str(milliseconds)


class SubRip:
    @property
    def elements(self):
        return self._elements

    def __init__(self, intervals, texts, numbers=None):
        if len(intervals) != len(texts):
            raise ValueError("Number of intervals must be equal to number of texts")
        if (numbers is not None) and (len(intervals) != len(numbers)):
            raise ValueError("Number of intervals must be equal to number of numbers")
        self._elements = [None] * len(intervals)
        for i in range(len(intervals)):
            if numbers is None:
                self._elements[i] = SubRipElement(i + 1, intervals[i], texts[i])
            else:
                self._elements[i] = SubRipElement(numbers[i], intervals[i], texts[i])

    def __str__(self):
        subtitles = ""
        for subtitle in self._elements:
            subtitles += str(subtitle)
        return subtitles

    @classmethod
    def parse(cls, text):
        pattern = r"(?P<number>\d+)\n(?P<from_h>\d+):(?P<from_m>\d+):(?P<from_s>\d+),(?P<from_ms>\d+)\s+-+>\s+(?P<to_h>\d+):(?P<to_m>\d+):(?P<to_s>\d+),(?P<to_ms>\d+)\n(?P<text>(.|\n)*?)(\n{2,}|\n*$)"
        r = re.compile(pattern)
        subs_decomposed = [m.groupdict() for m in r.finditer(text)]
        intervals = [None] * len(subs_decomposed)
        texts = [None] * len(subs_decomposed)
        numbers = [0] * len(subs_decomposed)
        for i, sub in enumerate(subs_decomposed):
            numbers[i] = int(sub["number"])
            from_ms = int(sub["from_ms"]) + 1000 * int(sub["from_s"]) + 6000 * int(sub["from_m"]) + 3600000 * int(
                sub["from_m"])
            to_ms = int(sub["to_ms"]) + 1000 * int(sub["to_s"]) + 6000 * int(sub["to_m"]) + 3600000 * int(
                sub["to_m"])
            intervals[i] = tinterval(from_ms, to_ms)
            texts[i] = sub["text"]
        return cls(intervals, texts, numbers)


with open("test.srt") as f:
    print(SubRip.parse(f.read()))