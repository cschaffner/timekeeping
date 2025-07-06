
import csv
import datetime
import matplotlib.pyplot as plt
from collections import defaultdict
import os

INPUT_FILE = 'data/tmetric_processed.csv'


# Read processed data and sum hours per day type
weekday_hours = defaultdict(float)
saturday_hours = defaultdict(float)
sunday_hours = defaultdict(float)
with open(INPUT_FILE, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        # Parse date
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
        hours = float(row.get('Duration adjusted (hours)', 0))
        wd = date_obj.weekday()
        if wd < 5:
            weekday_hours[date_obj] += hours
        elif wd == 5:
            saturday_hours[date_obj] += hours
        elif wd == 6:
            sunday_hours[date_obj] += hours

# Prepare data for histograms
weekday_list = list(weekday_hours.values())
saturday_list = list(saturday_hours.values())
sunday_list = list(sunday_hours.values())

# Ensure plots directory exists
os.makedirs('plots', exist_ok=True)

# Plot all histograms, but only save the last (Sunday)
fig, axes = plt.subplots(3, 1, figsize=(8, 12))

axes[0].hist(weekday_list, bins=range(0, 20), edgecolor='black', align='left')
axes[0].set_xlabel('Hours worked per work-day (Mon-Fri)')
axes[0].set_ylabel('Number of days')
axes[0].set_title('Histogram of Hours Worked per Work-Day (Mon-Fri)')
axes[0].set_xticks(range(0, 20))
axes[0].grid(axis='y', linestyle='--', alpha=0.7)

axes[1].hist(saturday_list, bins=range(0, 20), edgecolor='black', align='left', color='orange')
axes[1].set_xlabel('Hours worked per Saturday')
axes[1].set_ylabel('Number of Saturdays')
axes[1].set_title('Histogram of Hours Worked per Saturday')
axes[1].set_xticks(range(0, 20))
axes[1].grid(axis='y', linestyle='--', alpha=0.7)

axes[2].hist(sunday_list, bins=range(0, 20), edgecolor='black', align='left', color='green')
axes[2].set_xlabel('Hours worked per Sunday')
axes[2].set_ylabel('Number of Sundays')
axes[2].set_title('Histogram of Hours Worked per Sunday')
axes[2].set_xticks(range(0, 20))
axes[2].grid(axis='y', linestyle='--', alpha=0.7)

fig.tight_layout()
fig.savefig('plots/histograms.png')
plt.show()
