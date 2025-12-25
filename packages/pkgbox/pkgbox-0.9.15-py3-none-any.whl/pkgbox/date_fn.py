from datetime import datetime, date
from datetime import timedelta
import calendar
import numpy as np

dt_fmt = "%Y-%m-%d"
dtm_fmt = "%Y-%m-%d %H:%M:%S"
is_utc = True

class Cdt:

    def set_is_utc(self, is_utc=True):
        self.is_utc = is_utc

    def __init__(self, dt_fmt=dt_fmt, dtm_fmt=dtm_fmt):
        self.dt_fmt = dt_fmt
        self.dtm_fmt = dtm_fmt
        self.is_utc = True


    def to_dt(self, datestr):
        return datetime.strptime(datestr, dt_fmt).date()

    def now(self):
        if self.is_utc:
            today = (datetime.now() + timedelta(hours=5.5)).strftime(self.dtm_fmt)
        else:
            today = (datetime.now()).strftime(self.dtm_fmt)

        return today

    def yesterday(self):
        if self.is_utc:
            yesterday = (datetime.now() - timedelta(days=1) + timedelta(hours=5.5)).strftime(self.dt_fmt)
        else:
            yesterday = (datetime.now() - timedelta(days=1)).strftime(self.dt_fmt)

        return yesterday

    def today(self):
        if self.is_utc:
            today = (datetime.now() + timedelta(hours=5.5)).strftime(self.dt_fmt)
        else:
            today = (datetime.now()).strftime(self.dt_fmt)
        return today

    def today_x(self, x):
        if self.is_utc:
            today = (datetime.now() - timedelta(days=x) + timedelta(hours=5.5)).strftime(self.dt_fmt)
        else:
            today = (datetime.now() - timedelta(days=x)).strftime(self.dt_fmt)

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

    def now_datetime(self):
        if self.is_utc:
            today = (datetime.now() + timedelta(hours=5.5))
        else:
            today = (datetime.now())
        return today

    def yesterday_datetime(self):
        if self.is_utc:
            yesterday = (datetime.now() - timedelta(days=1) + timedelta(hours=5.5))
        else:
            yesterday = (datetime.now() - timedelta(days=1))
        return yesterday

    def today_datetime(self):
        if self.is_utc:
            today = (datetime.now() + timedelta(hours=5.5))
        else:
            today = (datetime.now())
        return today

    def today_x_datetime(self, x):
        if self.is_utc:
            today = (datetime.now() - timedelta(days=x) + timedelta(hours=5.5))
        else:
            today = (datetime.now() - timedelta(days=x))

        return today

    def today_7_datetime(self):
        today = self.today_x_datetime(7)
        return today

    def today_14__datetime(self):
        today = self.today_x_datetime(14)
        return today

    def today_21_datetime(self):
        today = self.today_x_datetime(21)
        return today

    def today_28_datetime(self):
        today = self.today_x_datetime(28)
        return today

    def week_datetime(self):
        return self.fn_week_tuple_datetime(self.today())

    def week_x_datetime(self, x):
        any_day_of_x_week = self.today_x(x*7)
        return self.fn_week_tuple_datetime(any_day_of_x_week)

    def current_week_datetime(self):
        return self.week_datetime()

    def last_week_datetime(self):
        return self.week_x_datetime(1)

    def previous_week_datetime(self):
        return self.week_x_datetime(1)

    def week_1_datetime(self):
        return self.week_x_datetime(1)

    def week_2_datetime(self):
        return self.week_x_datetime(2)

    def week_3_datetime(self):
        return self.week_x_datetime(3)

    def week_4_datetime(self):
        return self.week_x_datetime(4)

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

    def fn_week_tuple_datetime(self, datestr):
        '''
        Gives start date and end of monday to sunday week basis string input
        example. 2022-04-19 will give you output as ('2022-04-18', '2022-04-24')
        '''
        dt = datetime.strptime(datestr, self.dt_fmt)
        start = dt - timedelta(days=dt.weekday())
        end = start + timedelta(days=6)
        return (start, end)

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

    def date_split_extended(self, start_date, end_date, interval_type, dt_fmt="%Y-%m-%d"):
        """
        Splits the period from start_date to end_date into intervals by calendar period.
        Parameters:
            start_date (str): Start date in dt_fmt (default "%Y-%m-%d")
            end_date (str): End date in dt_fmt (default "%Y-%m-%d")
            interval_type (str): One of "day", "fortnight", "week", "month", "quarter", "year".
            dt_fmt (str): Date format string.
        Returns:
            List of tuples of strings [(interval_start, interval_end), ...].
        """
        # Convert input strings to date objects
        start = datetime.strptime(start_date, dt_fmt).date()
        end   = datetime.strptime(end_date, dt_fmt).date()
        intervals = []
        current = start

        while current <= end:
            it = interval_type.lower()
            if it == 'day':
                period_end = current
            elif it == 'fortnight':
                # 14-day windows
                period_end = current + timedelta(days=13)
            elif it == 'week':
                # Define a week as Monday to Sunday.
                days_to_sunday = 6 - current.weekday()
                period_end = current + timedelta(days=days_to_sunday)
            elif it == 'month':
                # Get last day of current month
                last_day = calendar.monthrange(current.year, current.month)[1]
                period_end = current.replace(day=last_day)
            elif it == 'quarter':
                # Quarters: Q1: Jan-Mar, Q2: Apr-Jun, Q3: Jul-Sep, Q4: Oct-Dec
                if current.month <= 3:
                    period_end = date(current.year, 3, 31)
                elif current.month <= 6:
                    period_end = date(current.year, 6, 30)
                elif current.month <= 9:
                    period_end = date(current.year, 9, 30)
                else:
                    period_end = date(current.year, 12, 31)
            elif it == 'year':
                period_end = date(current.year, 12, 31)
            else:
                raise ValueError(f"Unsupported interval type: {interval_type}")

            # Make sure not to go past the overall end date
            if period_end > end:
                period_end = end

            # Append the interval as formatted strings
            intervals.append((current.strftime(dt_fmt), period_end.strftime(dt_fmt)))

            # Next interval starts the day after period_end
            current = period_end + timedelta(days=1)

        return intervals

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
