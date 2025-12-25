from datetime import datetime
from datetime import timedelta
import numpy as np

dt_fmt = "%Y-%m-%d"
dtm_fmt = "%Y-%m-%d %H:%M:%S"

class Cdt:
    def __init__(self, dt_fmt=dt_fmt, dtm_fmt=dtm_fmt):
        self.dt_fmt = dt_fmt
        self.dtm_fmt = dtm_fmt

    def now(self):
        today = (datetime.now() + timedelta(hours=5.5)).strftime(self.dtm_fmt)
        return today

    def yesterday(self):
        yesterday = (datetime.now() - timedelta(days=1) + timedelta(hours=5.5)).strftime(self.dt_fmt)
        return yesterday

    def today(self):
        today = (datetime.now() + timedelta(hours=5.5)).strftime(self.dt_fmt)
        return today

    def today_x(self, x):
        today = (datetime.now() - timedelta(days=x) + timedelta(hours=5.5)).strftime(self.dt_fmt)
        return today

    def today_7(self):
        today = self.today_x(7)
        return today

    def today_14(self):
        today = self.today_x(14)
        return today

    def today_21(self):
        today = self.today_x(21)
        return today

    def today_28(self):
        today = self.today_x(28)
        return today

    def week(self):
        return self.fn_week_tuple(self.today())

    def week_x(self, x):
        any_day_of_x_week = self.today_x(x*7)
        return self.fn_week_tuple(any_day_of_x_week)

    def current_week(self):
        return self.week()

    def last_week(self):
        return self.week_x(1)

    def previous_week(self):
        return self.week_x(1)

    def week_1(self):
        return self.week_x(1)

    def week_2(self):
        return self.week_x(2)

    def week_3(self):
        return self.week_x(3)

    def week_4(self):
        return self.week_x(4)

    def month(self):
        return (self.fn_first_day_of_month(self.today()), self.fn_last_day_of_month(self.today()))

    def month_x(self, x):
        first_day_of_month = self.fn_first_day_of_month(self.today())
        for i in np.arange(1, x+1):
            last_day_of_prev_month = (datetime.strptime(first_day_of_month, self.dt_fmt) - timedelta(days=1)).strftime(self.dt_fmt)
            first_day_of_month = self.fn_first_day_of_month(last_day_of_prev_month)
        last_day_of_month = self.fn_last_day_of_month(first_day_of_month)
        return (first_day_of_month, last_day_of_month)

    def current_month(self):
        return self.month()

    def last_month(self):
        return self.month_x(1)

    def previous_month(self):
        return self.month_x(1)

    def month_1(self):
        return self.month_x(1)

    def month_2(self):
        return self.month_x(2)

    def month_3(self):
        return self.month_x(3)

    def month_4(self):
        return self.month_x(4)

    def fn_week_tuple(self, datestr):
        '''
        Gives start date and end of monday to sunday week basis string input
        example. 2022-04-19 will give you output as ('2022-04-18', '2022-04-24')
        '''
        dt = datetime.strptime(datestr, self.dt_fmt)
        start = dt - timedelta(days=dt.weekday())
        end = start + timedelta(days=6)
        return (start.strftime(self.dt_fmt), end.strftime(self.dt_fmt))

    def fn_last_day_of_month(self, datestr):
        # this will never fail
        # get close to the end of the month for any day, and add 4 days 'over'
        any_day = datetime.strptime(datestr, self.dt_fmt)
        next_month = any_day.replace(day=28) + timedelta(days=4)
        # subtract the number of remaining 'overage' days to get last day of current month, or said programattically said, the previous day of the first of next month
        return (next_month - timedelta(days=next_month.day)).strftime(self.dt_fmt)

    def fn_first_day_of_month(self, datestr):
        any_day = datetime.strptime(datestr, self.dt_fmt)
        return any_day.replace(day=1).strftime(self.dt_fmt)

    def date_split(self, start, end, intv):
        def date_range_generator(start, end, intv):
            start = datetime.strptime(start, self.dt_fmt)
            end = datetime.strptime(end, self.dt_fmt)
            diff = (end - start) / intv
            for i in range(intv):
                if(i != 0):
                    x = ((start + diff * i) - timedelta(days=1)).strftime(self.dt_fmt)
                    yield x
                x = (start + diff * i).strftime(self.dt_fmt)
                yield x
            yield end.strftime(self.dt_fmt)
        dt_lst = list(date_range_generator(start, end, intv))
        return list(zip(dt_lst[::2], dt_lst[1::2]))

    def datetime_split(self, start, end, intv):
        def date_range_generator(start, end, intv):
            start = datetime.strptime(start, self.dtm_fmt)
            end = datetime.strptime(end, self.dtm_fmt)
            diff = (end - start) / intv
            for i in range(intv):
                if(i != 0):
                    x = ((start + diff * i) - timedelta(seconds=1)).strftime(self.dtm_fmt)
                    yield x
                x = (start + diff * i).strftime(self.dtm_fmt)
                yield x
            yield end.strftime(self.dtm_fmt)
        dt_lst = list(date_range_generator(start, end, intv))
        return list(zip(dt_lst[::2], dt_lst[1::2]))
