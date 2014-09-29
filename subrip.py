import re
from timeinterval import TimeInterval


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
        subtitle += self._ms_to_str(self.interval.begin) + " ---> " + self._ms_to_str(self.interval.end) + "\n"
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
        return SubRipElement._str_with_zeros(hours, 2) + \
               ":" + SubRipElement._str_with_zeros(minutes, 2) + \
               ":" + SubRipElement._str_with_zeros(total_seconds, 2) + \
               "," + SubRipElement._str_with_zeros(milliseconds, 3)

    @staticmethod
    def _str_with_zeros(number, length):
        number_str = str(number)
        number_str = "0" * (length - len(number_str)) + number_str
        return number_str


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
            if i != 0 and intervals[i - 1].begin > intervals[i].begin:
                raise ValueError("Intervals are unordered. Interval at " + str(i - 1) + " is later than next interval.")

            if numbers is None:
                self._elements[i] = SubRipElement(i + 1, intervals[i], texts[i])
            else:
                self._elements[i] = SubRipElement(numbers[i], intervals[i], texts[i])

    def __str__(self):
        subtitles = ""
        for subtitle in self._elements:
            subtitles += str(subtitle)
        return subtitles

    def find(self, time):
        index_min = 0
        index_max = len(self.elements) - 1
        while index_max >= index_min:
            index_mid = (index_min + index_max) // 2
            mid_interval = self.elements[index_mid].interval
            if mid_interval.contains(time):
                return self.elements[index_mid]
            elif mid_interval.is_earlier(time):
                index_min = index_mid + 1
            else:
                index_max = index_mid - 1
        return None

    @classmethod
    def parse(cls, text):
        pattern = r"(?P<number>\d+)\n(?P<from_h>\d+):(?P<from_m>\d+):(?P<from_s>\d+),(?P<from_ms>\d+)\s+-+>\s+(?P<to_h>\d+):(?P<to_m>\d+):(?P<to_s>\d+),(?P<to_ms>\d+)\n(?P<text>(.|\n)*?)(?=\n{2,}\d+\n\d+:\d+:\d+,\d+\s+-+>\s+\d+:\d+:\d+,\d+\n|\n*$)"
        r = re.compile(pattern)
        subs_decomposed = [m.groupdict() for m in r.finditer(text)]
        intervals = [None] * len(subs_decomposed)
        texts = [None] * len(subs_decomposed)
        numbers = [0] * len(subs_decomposed)
        for i, sub in enumerate(subs_decomposed):
            numbers[i] = int(sub["number"])
            from_ms = int(sub["from_ms"]) + 1000 * int(sub["from_s"]) + 60000 * int(sub["from_m"]) + 3600000 * int(
                sub["from_h"])
            to_ms = int(sub["to_ms"]) + 1000 * int(sub["to_s"]) + 60000 * int(sub["to_m"]) + 3600000 * int(
                sub["to_h"])
            intervals[i] = TimeInterval(from_ms, to_ms)
            texts[i] = sub["text"]
        return cls(intervals, texts, numbers)

    @staticmethod
    def _is_number(string):
        if string is None or len(string) == 0:
            return False
        check_string = string
        if string[-1] == "\n":
            check_string = string[:-1]
        for char in check_string:
            if not ("0" <= char <= "9"):
                return False
        return True

