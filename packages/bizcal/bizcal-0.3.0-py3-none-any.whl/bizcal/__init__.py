########################################################################################
__all__ = ['Calendar']


import re
import datetime as pydt


class Calendar:
    def __init__(self, spec):
        if isinstance(spec, str):
            with open(spec) as f:
                spec = [s.strip() for s in f if s.strip()]
        cals = {}
        for line in spec:
            year, cal_spec = line.split(':')
            cals[int(year)] = set(
                x
                for holidays in cal_spec.split(',')
                for x in dates_from_range(int(year), holidays)
            )
        if not cals:
            raise ValueError('invalid calendar spec')
        years = sorted(cals.keys())
        self.ymin = years[0]
        self.ymax = years[-1]
        if self.ymax - self.ymin + 1 < len(years):
            raise ValueError('incomplete calendar spec')
        self.table = [cals[y] for y in years]
        assert len(self.table) == self.ymax - self.ymin + 1

    def __contains__(self, spec):
        d = parse_date(spec)
        return d.year >= self.ymin and d.year <= self.ymax

    def __call__(self, *args):
        if len(args) == 3:
            return Date(args[0], args[1], args[2], self, _internal=True)
        if len(args) == 1:
            d = parse_date(args[0])
            return Date(d.year, d.month, d.day, self, _internal=True)

    def __getitem__(self, spec):
        if isinstance(spec, tuple):
            if len(spec) != 2:
                raise ValueError('only cal[beg, end] allowed')
        elif isinstance(spec, str):
            if spec == '*':
                spec = f'{self.ymin}-{self.ymax}'
            spec = self.span(spec)
        else:
            raise ValueError(f'illegal range spec {spec}')
        return Range(self(spec[0]), self(spec[1]), _internal=True)

    @staticmethod
    def span(spec: str):
        if not isinstance(spec, str):
            raise TypeError('Calendar.span requires string input')
        beg, end = parse_range(spec)
        return (first_day(beg), last_day(end))

    @property
    def min(self):
        return self(first_day(str(self.ymin)))

    @property
    def max(self):
        return self(last_day(str(self.ymax)))


class Date(pydt.date):
    def __new__(cls, y, m, d, cal, idx=None, holiday=None, biz=None, *, _internal=None):
        if not _internal:
            raise TypeError('Date is an internal type, do NOT use it!')
        day = pydt.date.__new__(cls, y, m, d)
        day.cal = cal
        if idx is None:
            if day.year < cal.ymin or day.year > cal.ymax:
                raise ValueError(f'{day} outside [{cal.ymin}, {cal.ymax}]')
            day.idx = day.year - cal.ymin
        else:
            day.idx = idx
        if holiday is None:
            day.holiday = day.month * 100 + day.day in cal.table[day.idx]
        else:
            day.holiday = holiday
        day.open = not day.holiday and day.weekday() < 5 if biz is None else biz
        return day

    def clone(self):
        return Date(
            self.year,
            self.month,
            self.day,
            self.cal,
            self.idx,
            self.holiday,
            self.open,
            _internal=True,
        )

    def __eq__(self, d):
        if isinstance(d, Date):
            return self.num == d.num
        return self.year == d.year and self.month == d.month and self.day == d.day

    def __bool__(self):
        return self.open

    @property
    def num(self):
        return self.year * 10000 + self.month * 100 + self.day

    @property
    def str(self):
        return self.spec()

    def spec(self, sep=''):
        return self.strftime(f'%Y{sep}%m{sep}%d')

    @property
    def eom(self):
        if self.day == 31:
            return True
        # do NOT shift today, as it may fall outside this calendar
        d = pydt.date(self.year, self.month, 1) + pydt.timedelta(days=32)
        d = d.replace(day=1) - pydt.timedelta(days=1)
        return d.day == self.day

    ### calendar day shift
    def __add__(self, days):
        if not days:
            return self.clone()
        d = pydt.date.fromordinal(self.toordinal() + days)
        return Date(
            d.year,
            d.month,
            d.day,
            self.cal,
            self.idx if d.year == self.year else None,
            _internal=True,
        )

    def __sub__(self, days):
        return self + (-days)

    ### business day shift
    def __rshift__(self, days):
        return self.shift(days)

    def __lshift__(self, days):
        return self.shift(-days)

    def shift(self, days):
        if not days:
            return self.clone()
        delta = days > 0 and 1 or -1
        days = abs(days)
        day = self.clone()
        while days:
            day = day + delta
            days -= day.open and 1 or 0
        return day


class Range:
    def __init__(self, since, until, *, _internal=None):
        if not _internal:
            raise TypeError('Range is an internal type, do NOT use it!')
        self.since, self.until = (since, until)

    def __iter__(self):
        return self.bizdays

    @property
    def days(self):
        "Generate calendar days."
        day = self.since.clone()
        while True:
            yield day
            if day == self.until:
                return
            day = day + 1

    @property
    def bizdays(self):
        "Generate business days."
        for d in self.days:
            if d.open:
                yield d

    def __len__(self):
        "Count business days."
        return sum(1 for d in self.bizdays if d.open)

    @property
    def spec(self):
        "Range spec."
        if self.since.day == 1 and self.until.eom:
            if self.since.month == 1 and self.until.month == 12:
                return range_join(str(self.since.year), str(self.until.year))
            return range_join(self.since.strftime('%Y%m'), self.until.strftime('%Y%m'))
        return range_join(self.since.str, self.until.str)


def dates_from_range(year, spec):
    if '-' not in spec:
        yield int(spec)
        return
    beg, end = parse_range(spec, numeric=True)
    day = pydt.date(year, beg // 100, beg % 100)
    end = pydt.date(year, end // 100, end % 100)
    oneday = pydt.timedelta(1)
    while day <= end:
        yield day.month * 100 + day.day
        day = day + oneday


def parse_date(spec):
    if isinstance(spec, str):
        if spec == 'today':
            return pydt.datetime.now().date()
        return parse_date(int(re.sub(r'\D', '', spec)))
    if isinstance(spec, pydt.date):
        return spec
    if isinstance(spec, (list, tuple)):
        return parse_date(pydt.date(*spec))
    if spec < 19000000 or spec > 29999999:
        raise ValueError(f'invalid date number {spec}')
    year, mmdd = divmod(spec, 10000)
    return pydt.date(year, mmdd // 100, mmdd % 100)


def parse_range(spec, numeric=False):
    if numeric:
        s = parse_range(spec, numeric=False)
        return (int(s[0]), int(s[1]))
    s = [re.sub(r'\D', '', x) for x in spec.strip().split('-')]
    if len(s) > 2:
        raise ValueError(f'invalid range spec {spec}')
    if len(s) < 2:
        return (spec, spec)
    if len(s[0]) < len(s[1]):
        return (s[0], s[1])
    return (s[0], s[0][: -len(s[1])] + s[1])


def first_day(spec):
    if len(spec) == 8:
        year, mmdd = divmod(int(spec), 10000)
        return pydt.date(year, mmdd // 100, mmdd % 100)
    if len(spec) == 6:
        return first_day(spec + '01')
    if len(spec) == 4:
        return first_day(spec + '0101')
    raise ValueError(f'invalid date spec {spec}')


def last_day(spec):
    if len(spec) == 8:
        year, mmdd = divmod(int(spec), 10000)
        return pydt.date(year, mmdd // 100, mmdd % 100)
    if len(spec) == 6:
        day = last_day(spec + '01') + pydt.timedelta(days=32)
        return day.replace(day=1) - pydt.timedelta(days=1)
    if len(spec) == 4:
        return last_day(spec + '1231')
    raise ValueError(f'invalid date spec {spec}')


def range_join(x, y):
    if len(x) != len(y):
        return f'{x}-{y}'
    if not x:
        return ''
    sep = None
    for i in range(len(x)):
        if x[i] != y[i]:
            break
        sep = i
    if sep is None:
        return f'{x}-{y}'
    sep += 1
    return x if sep >= len(y) else f'{x}-{y[sep:]}'


### bizcal/__init__.py ends here
