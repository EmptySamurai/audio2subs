__author__ = 'emptysamurai'


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

    def __init__(self, interval, text, number):
        self._interval = interval
        self._text = text
        self._number = number

    def __str__(self):
        subtitle = str(self.number) + "\n"
        subtitle += self._ms_to_str(self.interval.start) + " --> " + self._ms_to_str(self.interval.end) + "\n"
        subtitle += self.text
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

    def __init__(self, intervals, texts):
        if len(intervals) != len(texts):
            raise ValueError("Number of intervals must be equal to number of texts")
        self._elements = [None] * len(intervals)
        for i in range(len(intervals)):
            self._elements[i] = SubRipElement(intervals[i], texts[i], i)

    def __str__(self):
        subtitles = ""
        for subtitle in self._elements:
            subtitles += str(subtitle)
        return subtitles