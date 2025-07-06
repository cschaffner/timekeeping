import csv
import datetime
import calendar
import matplotlib.pyplot as plt
from collections import defaultdict
import os

INPUT_FILE = 'data/tmetric_processed.csv'


# Global threshold for holiday/worked weekend (in hours)
DAILY_THRESHOLD = 2.0  # hours

def get_holidays_by_year(input_file, year, threshold=DAILY_THRESHOLD):
    # Map date -> total hours
    day_hours = defaultdict(float)
    with open(input_file, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            day = row.get('parsed_day') or row.get('Day')
            if not day:
                continue
            try:
                date_obj = datetime.datetime.strptime(day, '%Y-%m-%d').date()
            except Exception:
                try:
                    date_obj = datetime.datetime.strptime(day, '%d/%m/%Y').date()
                except Exception:
                    continue
            if date_obj.year != year:
                continue
            hours = float(row.get('Duration adjusted (hours)', 0))
            day_hours[date_obj] += hours
    # Build set of all days in the year
    today = datetime.date.today()
    all_days = [datetime.date(year, 1, 1) + datetime.timedelta(days=i) for i in range((datetime.date(year+1, 1, 1) - datetime.date(year, 1, 1)).days)]
    workday_holidays = set()
    weekend_worked = set()
    for date_obj in all_days:
        # For the current year, skip future days
        if year == today.year and date_obj > today:
            continue
        hours = day_hours.get(date_obj, 0.0)
        wd = date_obj.weekday()
        if wd < 5:
            # Weekday: less than threshold hours or missing is a holiday
            if hours < threshold:
                workday_holidays.add(date_obj)
        else:
            # Weekend: more than threshold hours is a 'worked weekend'
            if hours >= threshold:
                weekend_worked.add(date_obj)
    return workday_holidays, weekend_worked

def plot_holiday_calendar(year, workday_holidays, weekend_worked):
    # Create a calendar for the year, mark holidays and worked weekends
    months = range(1, 13)
    fig, axes = plt.subplots(3, 4, figsize=(18, 12))
    for i, month in enumerate(months):
        ax = axes[i // 4, i % 4]
        cal = calendar.monthcalendar(year, month)
        ax.axis('off')
        # Plot days (week starts on Monday)
        for week_idx, week in enumerate(cal):
            for day_idx, day in enumerate(week):
                # Add extra spacing between days and weeks
                x = day_idx * 1.25
                y = week_idx * 1.25
                if day == 0:
                    # Show empty cell for alignment
                    ax.text(x, y, '', ha='center', va='center',
                            bbox=dict(boxstyle='round', facecolor='lightgray', edgecolor='gray', alpha=0.2))
                    continue
                date_obj = datetime.date(year, month, day)
                # Mark workday holidays in green, worked weekends in red, others white
                if date_obj in workday_holidays:
                    color = 'lightgreen'
                elif date_obj in weekend_worked:
                    color = 'red'
                else:
                    color = 'white'
                ax.text(x, y, str(day), ha='center', va='center',
                        bbox=dict(boxstyle='round', facecolor=color, edgecolor='gray', alpha=0.7))
        # Draw a rounded box around the whole month, including the month name
        n_weeks = len(cal)
        # Draw the month name inside the box, above the days
        ax.text(3.5*1.25, -1.0, calendar.month_name[month], ha='center', va='center', fontsize=14, fontweight='bold',
                bbox=dict(boxstyle='round', facecolor='white', edgecolor='none', alpha=1.0), zorder=20)
        # Rectangle includes the month name row
        rect = plt.Rectangle(
            (-0.5, -1.5), 7*1.25, n_weeks*1.25+1.0,
            linewidth=2, edgecolor='black', facecolor='none',
            linestyle='-', zorder=10, joinstyle='round',
        )
        ax.add_patch(rect)
        # Set x-ticks for weekdays
        ax.set_xticks([i*1.25 for i in range(7)])
        ax.set_xticklabels(['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'])
        # Set y-limits to fit all weeks and the month name
        ax.set_ylim(n_weeks*1.25-0.5, -1.5)
        ax.set_xlim(-0.5, 7*1.25-0.5)
    plt.suptitle(f"Holiday Calendar {year}", fontsize=18)
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    os.makedirs('plots', exist_ok=True)
    plt.savefig(f'plots/holiday_calendar_{year}.png')
    plt.show()

def main():
    # Compute and plot statistics for all years in the data
    # First, find all years present in the data
    years = set()
    with open(INPUT_FILE, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            day = row.get('parsed_day') or row.get('Day')
            if not day:
                continue
            try:
                date_obj = datetime.datetime.strptime(day, '%Y-%m-%d').date()
            except Exception:
                try:
                    date_obj = datetime.datetime.strptime(day, '%d/%m/%Y').date()
                except Exception:
                    continue
            years.add(date_obj.year)
    years = sorted([y for y in years if y >= 2019])

    green_counts = []
    red_counts = []
    green_per_year = []
    red_per_year = []
    for year in years:
        workday_holidays, weekend_worked = get_holidays_by_year(INPUT_FILE, year, DAILY_THRESHOLD)
        print(f"Year {year}: Green (workday holidays) = {len(workday_holidays)}, Red (worked weekends) = {len(weekend_worked)}")
        green_counts.append(len(workday_holidays))
        red_counts.append(len(weekend_worked))
        green_per_year.append(workday_holidays)
        red_per_year.append(weekend_worked)
        if year == 2024:
            plot_holiday_calendar(year, workday_holidays, weekend_worked)

    # Plot bar chart of green and red days per year, with value labels on bars
    import numpy as np
    x = np.arange(len(years))
    width = 0.35
    fig, ax = plt.subplots(figsize=(8, 5))
    bars1 = ax.bar(x - width/2, green_counts, width, label=f'Workday holidays (<{DAILY_THRESHOLD}h)', color='lightgreen', edgecolor='black')
    bars2 = ax.bar(x + width/2, red_counts, width, label=f'Worked weekends (>={DAILY_THRESHOLD}h)', color='red', edgecolor='black')
    # Add value labels on top of each bar
    for bar in bars1:
        height = bar.get_height()
        if height > 0:
            ax.annotate(f'{int(height)}',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3),  # 3 points vertical offset
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=11, fontweight='bold', color='black')
    for bar in bars2:
        height = bar.get_height()
        if height > 0:
            ax.annotate(f'{int(height)}',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=11, fontweight='bold', color='black')
    ax.set_xticks(x)
    ax.set_xticklabels([str(y) for y in years])
    ax.set_ylabel('Number of days')
    ax.set_xlabel('Year')
    ax.set_title('Number of green and red days per year')
    ax.legend()
    plt.tight_layout()
    os.makedirs('plots', exist_ok=True)
    plt.savefig('plots/holiday_stats_per_year.png')
    plt.show()

if __name__ == '__main__':
    main()
