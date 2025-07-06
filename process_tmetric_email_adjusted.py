
import csv
import datetime
from dateutil.parser import parse
from collections import defaultdict

# For Excel export
import xlsxwriter

INPUT_FILE = 'data/tmetric.csv'
OUTPUT_FILE = 'data/tmetric_processed.csv'
PROJECT_NAME = 'Email (various)'

# Helper to get week start (Monday)
def week_start(day: datetime.date) -> datetime.date:
    return day - datetime.timedelta(days=day.weekday())

def parse_duration(duration_str):
    # Handles HH:MM or H:MM
    t = parse(duration_str)
    return datetime.timedelta(hours=t.hour, minutes=t.minute)

def main():
    # Read all rows and parse dates/durations
    rows = []
    with open(INPUT_FILE, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            row['parsed_day'] = parse(row['Day'], yearfirst=True, dayfirst=False).date()
            row['parsed_duration'] = parse_duration(row['Duration'])
            rows.append(row)

    # Group by week
    week_to_rows = defaultdict(list)
    for row in rows:
        ws = week_start(row['parsed_day'])
        week_to_rows[ws].append(row)

    # For each week, compute total duration and email duration
    for week, week_rows in week_to_rows.items():
        total_duration = sum((r['parsed_duration'] for r in week_rows), datetime.timedelta())
        email_duration = sum((r['parsed_duration'] for r in week_rows if r['Project'] == PROJECT_NAME), datetime.timedelta())
        # Compute email percentage
        total_seconds = total_duration.total_seconds()
        email_seconds = email_duration.total_seconds()
        email_pct = email_seconds / total_seconds if total_seconds > 0 else 0
        # Format email_duration as h:mm:ss
        email_hours = int(email_seconds // 3600)
        email_minutes = int((email_seconds % 3600) // 60)
        email_seconds_rem = int(email_seconds % 60)
        email_duration_str = f"{email_hours:02d}:{email_minutes:02d}:{email_seconds_rem:02d}"
        email_pct_str = f"{email_pct:.4f}" if total_seconds > 0 else "0.0000"
        # Format total_duration as h:mm:ss
        total_hours = int(total_seconds // 3600)
        total_minutes = int((total_seconds % 3600) // 60)
        total_seconds_rem = int(total_seconds % 60)
        total_duration_str = f"{total_hours:02d}:{total_minutes:02d}:{total_seconds_rem:02d}"
        # Get year, month, week number from week start
        year = week.year
        month = week.month
        week_number = week.isocalendar()[1]
        # Add adjusted duration and all stats to each row, including numeric columns for easier import
        adjusted_seconds_list = []
        orig_seconds_list = []
        # Calculate total non-email duration for proportional distribution
        non_email_rows = [r for r in week_rows if r['Project'] != PROJECT_NAME]
        total_non_email_seconds = sum(r['parsed_duration'].total_seconds() for r in non_email_rows)
        if total_non_email_seconds == 0:
            # Only email activities this week: do not adjust, keep original durations
            for r in week_rows:
                orig_seconds = r['parsed_duration'].total_seconds()
                adjusted_seconds = orig_seconds
                adjusted_seconds_list.append(adjusted_seconds)
                orig_seconds_list.append(orig_seconds)
                hours = int(adjusted_seconds // 3600)
                minutes = int((adjusted_seconds % 3600) // 60)
                seconds = int(adjusted_seconds % 60)
                r['Duration adjusted'] = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                r['Weekly Email Total'] = email_duration_str
                r['Weekly Email %'] = email_pct_str
                r['Year'] = year
                r['Month'] = month
                r['Week'] = week_number
                r['Weekly Total'] = total_duration_str
                # Numeric columns for Apple Numbers/Excel
                r['Duration adjusted (hours)'] = round(adjusted_seconds / 3600, 4)
                r['Weekly Email Total (hours)'] = round(email_duration.total_seconds() / 3600, 4)
                r['Weekly Total (hours)'] = round(total_seconds / 3600, 4)
        else:
            for r in week_rows:
                orig_seconds = r['parsed_duration'].total_seconds()
                orig_seconds_list.append(orig_seconds)
                if r['Project'] == PROJECT_NAME:
                    # Email time is not distributed to itself, set adjusted to 0
                    adjusted_seconds = 0
                else:
                    # Distribute email time proportionally to non-email activities
                    share = (orig_seconds / total_non_email_seconds)
                    adjusted_seconds = orig_seconds + share * email_seconds
                adjusted_seconds_list.append(adjusted_seconds)
                hours = int(adjusted_seconds // 3600)
                minutes = int((adjusted_seconds % 3600) // 60)
                seconds = int(adjusted_seconds % 60)
                r['Duration adjusted'] = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                r['Weekly Email Total'] = email_duration_str
                r['Weekly Email %'] = email_pct_str
                r['Year'] = year
                r['Month'] = month
                r['Week'] = week_number
                r['Weekly Total'] = total_duration_str
                # Numeric columns for Apple Numbers/Excel
                r['Duration adjusted (hours)'] = round(adjusted_seconds / 3600, 4)
                r['Weekly Email Total (hours)'] = round(email_duration.total_seconds() / 3600, 4)
                r['Weekly Total (hours)'] = round(total_seconds / 3600, 4)
            # Double check: weekly sum of original and adjusted durations should be the same (within rounding)
            orig_sum = sum(orig_seconds_list)
            adj_sum = sum(adjusted_seconds_list)
            if abs(orig_sum - adj_sum) > 1:  # allow 1 second tolerance
                print(f"WARNING: Week {year}-W{week_number:02d} sum mismatch: original={orig_sum:.2f}s, adjusted={adj_sum:.2f}s")

    # Write output
    fieldnames = list(rows[0].keys())
    for extra_col in [
        'Duration adjusted', 'Weekly Email Total', 'Weekly Email %', 'Year', 'Month', 'Week', 'Weekly Total',
        'Duration adjusted (hours)', 'Weekly Email Total (hours)', 'Weekly Total (hours)']:
        if extra_col not in fieldnames:
            fieldnames.append(extra_col)

    # Write CSV
    with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    # Write Excel
    excel_file = OUTPUT_FILE.replace('.csv', '.xlsx')
    workbook = xlsxwriter.Workbook(excel_file)
    worksheet = workbook.add_worksheet('Sheet1')
    # Write header
    for col, field in enumerate(fieldnames):
        worksheet.write(0, col, field)
    # Write data
    for row_idx, row in enumerate(rows, 1):
        for col, field in enumerate(fieldnames):
            worksheet.write(row_idx, col, row.get(field, ''))
    workbook.close()

if __name__ == '__main__':
    main()
