import csv
from dateutil.parser import parse
from collections import defaultdict
from typing import Dict, List
import matplotlib.pyplot as plt
from matplotlib import colors as mcolors
import numpy as np
import collections

from pprint import pprint

import datetime


def weekday(day: datetime.date) -> int:
    """
    returns the numerical weekday of day
    """
    return int(day.strftime("%u"))

def weeknr(day: datetime.date) -> int:
    """
    returns number of the week
    :param day:
    :return:
    """
    return int(day.strftime("%V"))

def week_start(day: datetime.date) -> datetime.date:
    """
    returns the date Monday of the same week as day
    :param day: datetime.date
    :return:
    """
    return day - datetime.timedelta(days=weekday(day) - 1)  # the date of Monday of that week

def hours_minutes(td: datetime.timedelta) -> str:
    """
    returns a nicely formatted "hours:min" from a timedelta (stolen and adapted from datetime.timedelta.__str__
    :param td: timedelta
    :return: string with "h:min"
    """
    mm, ss = divmod(td.seconds, 60)
    hh, mm = divmod(mm, 60)
    s = "%d:%02d" % (hh, mm)
    if td.days:
        def plural(n):
            return n, abs(n) != 1 and "s" or ""

        s = ("%d day%s, " % plural(td.days)) + s
    return s


class Activity(object):
    '''
    and activity has Day,Academic Year,Year,Week,Weekday,User,Project,Project Code,Client,Time Entry,Tags,Start Time,End Time,Duration,Issue Id,Link
    '''
    def __init__(self, row: dict) -> None:
        """
        reads in a row of tmetric CSV file and saves it
        check https://docs.python.org/3/library/datetime.html#strftime-strptime-behavior
        :param row: CSV row of tmetric data
        """
        dt = parse(row['Day'], dayfirst=True)
        self.day = dt.date()

        # self.week_nr = int(row['Week'])
        # assert int(row['Week']) == int(dt.strftime("%V"))
        # self.weekday = int(row['Weekday'])  # Monday: 1, Tue: 2, ..., Sun: 7
        # assert int(row['Weekday']) == weekday(self.day)
        # self.week_start = week_start(self.day)   # the date of Monday of that week
        dt = parse(row['Start Time'])
        dt = dt.replace(year=self.day.year)
        dt = dt.replace(month=self.day.month)
        dt = dt.replace(day=self.day.day)
        self.start_time = dt
        dt = parse(row['End Time'])
        dt = dt.replace(year=self.day.year)
        dt = dt.replace(month=self.day.month)
        dt = dt.replace(day=self.day.day)
        self.end_time = dt
        td = parse(row['Duration'])
        self.duration = datetime.timedelta(hours=td.hour, minutes=td.minute)
        if not(self.end_time - self.start_time == self.duration):
            print(self.end_time, self.start_time, self.duration)
            self.end_time = self.start_time + self.duration
        assert self.end_time - self.start_time == self.duration, 'calculation trouble'

        # Add this to store tags and optionally the row
        self.tags = row.get('Work Type', '')
        self.row = row  # optional, for future flexibility


class Work(object):
    '''
    maintains a list of activities and allows to access functions of those
    '''
    def __init__(self, filename: str) -> None:
        '''
        reads in activities and stores them in a list
        :param filename: name of csv file with tmetric data
        '''
        self.activities = []
        with open(filename, newline='', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                act = Activity(row)
                self.activities.append(act)

    def hours_per_day(self) -> Dict[datetime.date, datetime.timedelta]:
        '''
        computes work hours per day and returns a dictionary with day: hours
        :return: dict with keys: dates, values: timedelta
        '''
        day_sum = defaultdict(datetime.timedelta)
        for act in self.activities:
            day_sum[act.day] += act.duration
        return day_sum

    def hours_per_week(self) -> Dict[datetime.date, datetime.timedelta]:
        '''
        computes work hours per week and returns a dictionary with day: hours
        :param day: datetime
        :return: dict with keys: start dates of a week, values: timedelta
        '''
        week_sum = defaultdict(datetime.timedelta)
        # special_date = datetime.date(day=29, month=7, year=2019)
        for act in self.activities:
            # if week_start(act.day) == special_date:
            #     print('act date: {}. sum: {}'.format(act.day, hours_minutes(week_sum[special_date])))
            week_sum[week_start(act.day)] += act.duration
        return week_sum


    def holidays(self, start_date: datetime.date, end_date: datetime.date, exclude_weekend: bool = True,
                 hour_threshold = datetime.timedelta(hours=4), verbose: bool = False) -> List[datetime.date]:
        """
        lists all holidays between start_date and end_date inclusive
        :param start_date: datetime.date
        :param end_date: datetime.date
        :param exclude_weekend: boolean
        :param hour_threshold:
        :return: list of dates between start_date and end_date with less than hour_threshold work, possible with
        weekends excluded
        """
        holidays = []
        day_sum = self.hours_per_day()
        day = start_date
        while day <= end_date:  # loop over all days from start_date to end_date
            if (not day in day_sum.keys()) or (day in day_sum.keys() and day_sum[day] <= hour_threshold):
                if not (exclude_weekend and (weekday(day) == 6 or weekday(day) == 7)):
                    holidays.append(day)
            day = day + datetime.timedelta(days=1)

        if verbose:
            print('days with less than {} between {} and {}, '.format(hour_threshold, start_date, end_date))
            if exclude_weekend:
                print('excluding weekends')
            else:
                print('including weekends')
            for day in holidays:
                print('{:%A, %d %b %Y} ({})'.format(day, hours_minutes(day_sum[day])))

        return holidays

    def weekends(self, start_date: datetime.date, end_date: datetime.date,
                 hour_threshold = datetime.timedelta(hours=4), verbose: bool = False) -> List[datetime.date]:
        """
        lists all weekend days between start_date and end_date inclusive with more than hour_threshold work
        :param start_date: datetime.date
        :param end_date: datetime.date
        :param hour_threshold:
        :return: list of dates between start_date and end_date with more than hour_threshold work
        """
        weekends = []
        day_sum = self.hours_per_day()
        day = start_date
        while day <= end_date:  # loop over all days from start_date to end_date
            if weekday(day) == 6 or weekday(day) == 7: # weekend
                if day_sum[day] > hour_threshold:
                    weekends.append(day)

            day = day + datetime.timedelta(days=1)

        if verbose:
            print('weekend days with more than {} between {} and {}, '.format(hour_threshold, start_date, end_date))
            for day in weekends:
                print('{:%A, %d %b %Y} ({})'.format(day, hours_minutes(day_sum[day])))

        return weekends

    def plot_week_hours(self, start_date, end_date):
        """
        plots hours per week
        :param start_date:
        :param end_date:
        :return:
        """
        week_sum = self.hours_per_week()
        fig, ax = plt.subplots(figsize=(8.42, 5.95))

        week_list = []
        hour_list = []
        current_week = week_start(start_date)
        while current_week <= end_date:
            week_list.append(weeknr(current_week))
            hour_list.append(week_sum[current_week].days*24 + week_sum[current_week].seconds/3600)
            current_week += datetime.timedelta(days=7)

        # Example data
        # people = ('Tom', 'Dick', 'Harry', 'Slim', 'Jim')
        y_pos = np.arange(len(week_list))
        # performance = 3 + 10 * np.random.rand(len(people))

        ax.barh(y_pos, hour_list, align='center',
                color='green', ecolor='black')
        ax.set_yticks(y_pos)
        ax.set_yticklabels(week_list)
        ax.invert_yaxis()  # labels read top-to-bottom
        ax.set_xlabel('hours')
        for y in range(len(week_list)):
            hour = hour_list[y]
            ax.text(hour+1.5, y, '{:.1f}'.format(hour), ha='center', va='center', color='black')

        ax.set_title('Hours per week')

        print('total number of hours: {:.1f}'.format(sum(hour_list)))

        plt.show()
        return True


    def plot_day_hours(self, start_date, end_date):
        """
        plots hours per week, but split into days
        adapted from https://matplotlib.org/gallery/lines_bars_and_markers/horizontal_barchart_distribution.html#sphx-glr-gallery-lines-bars-and-markers-horizontal-barchart-distribution-py

        :param start_date:
        :param end_date:
        :return:
        """
        day_sum = self.hours_per_day()
        fig, ax = plt.subplots(figsize=(8.42, 5.95))

        week_labels = [] # contains week numbers (for y-axis labels)
        hour_list = []
        # we want to create a 2-dimensional nparray with 7 columns and a row corresponding to one week
        # containing the number of hours worked per day in every column

        current_week = week_start(start_date)
        while current_week <= end_date:
            week_labels.append(weeknr(current_week))
            day_hours = []
            for day_offset in range(7):
                hours = day_sum[current_week + datetime.timedelta(days=day_offset)]
                day_hours.append(hours.days*24 + hours.seconds/3600)

            hour_list.append(day_hours)
            current_week += datetime.timedelta(days=7)

        data = np.array(hour_list)
        data_cum = data.cumsum(axis=1)

        category_colors = plt.get_cmap('RdYlGn')(
            np.linspace(0.15, 0.85, data.shape[1]))
        category_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday',
                          'Sunday']

        y_pos = np.arange(len(week_labels))

        for i, (colname, color) in enumerate(zip(category_names, category_colors)):
            widths = data[:, i]
            starts = data_cum[:, i] - widths
            ax.barh(y_pos, widths, left=starts, height=0.5,
                    label=colname, color=color)
            xcenters = starts + widths / 2

            r, g, b, _ = color
            text_color = 'white' if r * g * b < 0.5 else 'darkgrey'
            for y, (x, c) in enumerate(zip(xcenters, widths)):
                if c >= 2:
                    ax.text(x, y, '{:.1f}'.format(c), ha='center', va='center',
                            color=text_color)

        ax.legend(ncol=len(category_names), bbox_to_anchor=(0, 1),
                  loc='lower left', fontsize='small')

        ax.set_yticks(y_pos)
        ax.set_yticklabels(week_labels)
        ax.invert_yaxis()  # labels read top-to-bottom
        ax.set_xlabel('hours')

        plt.show()
        return True


    def plot_hours_per_day(self, start_date, end_date):
        """
        plots hours per week, but split into days
        adapted from https://matplotlib.org/gallery/lines_bars_and_markers/horizontal_barchart_distribution.html#sphx-glr-gallery-lines-bars-and-markers-horizontal-barchart-distribution-py

        :param start_date:
        :param end_date:
        :return:
        """
        day_sum = self.hours_per_day()
        fig, ax = plt.subplots(figsize=(8.42, 5.95))

        week_labels = [] # contains week numbers (for y-axis labels)
        hour_list = []
        # we want to create a 2-dimensional nparray with 7 columns and a row corresponding to one week
        # containing the number of hours worked per day in every column

        current_week = week_start(start_date)
        while current_week <= end_date:
            week_labels.append(weeknr(current_week))
            day_hours = []
            for day_offset in range(7):
                hours = day_sum[current_week + datetime.timedelta(days=day_offset)]
                day_hours.append(hours.days*24 + hours.seconds/3600)

            hour_list.append(day_hours)
            current_week += datetime.timedelta(days=7)

        data = np.array(hour_list)
        data_cum = data.cumsum(axis=1)

        category_colors = plt.get_cmap('RdYlGn')(
            np.linspace(0.15, 0.85, data.shape[1]))
        category_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday',
                          'Sunday']

        y_pos = np.arange(len(week_labels))
        day_starts = [0, 10, 20, 30, 40, 50, 55]

        for i, (colname, color) in enumerate(zip(category_names, category_colors)):
            widths = data[:, i]
            starts = day_starts[i]
            ax.barh(y_pos, widths, left=starts, height=0.5,
                    label=colname, color=color)
            xcenters = starts + widths / 2

            r, g, b, _ = color
            text_color = 'white' if r * g * b < 0.5 else 'darkgrey'
            for y, (x, c) in enumerate(zip(xcenters, widths)):
                if c >= 2:
                    ax.text(x, y, '{:.1f}'.format(c), ha='center', va='center',
                            color=text_color)

        ax.legend(ncol=len(category_names), bbox_to_anchor=(0, 1),
                  loc='lower left', fontsize='small')

        ax.set_yticks(y_pos)
        ax.set_yticklabels(week_labels)
        ax.invert_yaxis()  # labels read top-to-bottom
        ax.set_xlabel('hours')

        plt.show()
        return True


    def plot_tags_pie(self, year: int):
        """
        Plots a pie chart of total time spent per tag for the given year.
        """
        tag_sums = collections.defaultdict(datetime.timedelta)
        for act in self.activities:
            if act.day.year == year:
                tags = act.__dict__.get('tags') or act.__dict__.get('Tags') or act.__dict__.get('Tag')
                # If tags are not already parsed, try to get from row
                if not tags and hasattr(act, 'row'):
                    tags = act.row.get('Project Code', '')
                if not tags:
                    continue
                # Assume tags are comma-separated
                for tag in [t.strip() for t in tags.split(',') if t.strip()]:
                    tag_sums[tag] += act.duration

        if not tag_sums:
            print(f"No tag data found for year {year}.")
            return

        labels = list(tag_sums.keys())
        times = [td.days * 24 + td.seconds / 3600 for td in tag_sums.values()]

        fig, ax = plt.subplots(figsize=(8, 8))
        ax.pie(times, labels=labels, autopct='%1.1f%%', startangle=140)
        ax.set_title(f"Total Time Spent per Tag in {year}")
        plt.show()
        return True


def compute_week_sums():
    week_sum = defaultdict(datetime.timedelta)
    for row in tmetric:
        td = parse(row['Duration'])
        duration = datetime.timedelta(hours=td.hour, minutes=td.minute)
        print(row['Duration'], duration)
        week_sum[row['Week']] += duration

    for week, dura in week_sum.items():
        hours = int(dura.total_seconds()/3600)
        minutes = int(dura.total_seconds()/60) - 60*hours
        print('week: {}, hours: {}:{}'.format(week, hours, minutes))
    return week_sum


def compute_day_sums():
    day_sum = defaultdict(datetime.timedelta)
    for row in tmetric:
        td = parse(row['Duration'])
        duration = datetime.timedelta(hours=td.hour, minutes=td.minute)
        day = parse(row['Day'], dayfirst=True)
        day_sum[day] += duration

    for day, dura in day_sum.items():
        hours = int(dura.total_seconds()/3600)
        minutes = int(dura.total_seconds()/60) - 60*hours
        print('day: {}, hours: {}:{}'.format(day.date(), hours, minutes))
    return day_sum


def plot_test():

    colors = dict(mcolors.BASE_COLORS, **mcolors.CSS4_COLORS)

    # Sort colors by hue, saturation, value and name.
    by_hsv = sorted((tuple(mcolors.rgb_to_hsv(mcolors.to_rgba(color)[:3])), name)
                    for name, color in colors.items())
    sorted_names = [name for hsv, name in by_hsv]

    n = len(sorted_names)
    ncols = 8
    nrows = 52

    fig, ax = plt.subplots(figsize=(8.42, 5.95))

    # Get height and width
    X, Y = fig.get_dpi() * fig.get_size_inches()
    h = Y / (nrows + 1)
    w = X / ncols

    for i, name in enumerate(sorted_names):
        col = i % ncols
        row = i // ncols
        y = Y - (row * h) - h

        xi_line = w * (col + 0.05)
        xf_line = w * (col + 0.25)
        xi_text = w * (col + 0.3)

        ax.text(xi_text, y, name, fontsize=(h * 0.8),
                horizontalalignment='left',
                verticalalignment='center')

        ax.hlines(y + h * 0.1, xi_line, xf_line,
                  color=colors[name], linewidth=(h * 0.6))

    ax.set_xlim(0, X)
    ax.set_ylim(0, Y)
    # ax.set_axis_off()

    fig.subplots_adjust(left=0, right=1,
                        top=1, bottom=0,
                        hspace=0, wspace=0)
    plt.show()


def main():
    filename = 'data/tmetric.csv'
    worktime = Work(filename)
    start_date = datetime.date(day=27, month=8, year=2018)
    end_date = datetime.date(day=1, month=9, year=2019)
    weekends = worktime.weekends(start_date, end_date, verbose=True)
    holidays = worktime.holidays(start_date, end_date, verbose=True)
    # worktime.plot_week_hours(start_date, end_date)
    # worktime.plot_day_hours(start_date, end_date)
    # worktime.plot_hours_per_day(start_date, end_date)
    worktime.plot_tags_pie(2024)  # <-- Add this line

if __name__ == "__main__":
    main()