import csv
import datetime
import calendar
import matplotlib.pyplot as plt
import matplotlib.patheffects as patheffects
from collections import defaultdict
import os
import numpy as np
from matplotlib.colors import LinearSegmentedColormap


INPUT_FILE = 'data/tmetric_processed.csv'

# Global threshold for holiday/worked weekend (in hours)
DAILY_THRESHOLD = 2.0  # hours



# We'll interpolate between threshold and a max reasonable workday (e.g., 14h)
MAX_HOURS = 14.0
# Maximum for weekly color scale (e.g. 62h)
WEEK_MAX = 62

# Colormap options
COLORMAPS = {
    'viridis': 'viridis',
    'plasma': 'plasma',
    'inferno': 'inferno',
    'turbo': 'turbo',
    'cividis': 'cividis',
    # Custom discrete palette (for reference, not used in continuous mode)
    'custom': LinearSegmentedColormap.from_list(
        'custom_workhours',
        [
            (0.0, 'white'),      # 0h
            (1/14, 'lightgreen'),# >0h up to 2h
            (4/14, 'yellow'),    # >2h up to 4h
            (6/14, 'orange'),    # >4h up to 6h
            (8/14, 'red'),       # >6h up to 8h
            (1.0, 'purple'),     # >8h up to 14h
        ]
    ),
}

# Choose which colormap to use (reversed viridis)
COLORMAPS_TO_TRY = ['viridis_r', 'custom']


def get_day_hours_by_year(input_file, year):
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
    all_days = [datetime.date(year, 1, 1) + datetime.timedelta(days=i) for i in range((datetime.date(year+1, 1, 1) - datetime.date(year, 1, 1)).days)]
    return {d: day_hours.get(d, 0.0) for d in all_days}


def plot_colormap_calendar(year, day_hours):
    import matplotlib.cm as cm
    for cmap_name in COLORMAPS_TO_TRY:
        if cmap_name == 'custom':
            cmap = COLORMAPS['custom']
        elif cmap_name.endswith('_r'):
            base_name = cmap_name[:-2]
            cmap = cm.get_cmap(base_name).reversed()
        else:
            cmap = cm.get_cmap(cmap_name)

        # Build a continuous list of weeks (Monday-Sunday), covering the whole year
        jan1 = datetime.date(year, 1, 1)
        # Find the first Monday on or before Jan 1
        first_monday = jan1 - datetime.timedelta(days=jan1.weekday())
        dec31 = datetime.date(year, 12, 31)
        # Find the last Sunday on or after Dec 31
        last_sunday = dec31 + datetime.timedelta(days=(6 - dec31.weekday()))
        all_days = [first_monday + datetime.timedelta(days=i) for i in range((last_sunday - first_monday).days + 1)]
        weeks = [all_days[i:i+7] for i in range(0, len(all_days), 7)]

        n_weeks = len(weeks)
        fig, ax = plt.subplots(figsize=(22, n_weeks * 0.8))

        # --- Draw weekday headers ---
        for day_idx, wd in enumerate(['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']):
            x = day_idx * 1.25
            y = -1.2
            ax.text(x, y, wd, ha='center', va='center', fontsize=15, fontweight='bold', color='midnightblue', zorder=100)
        # Add header for weekly total
        ax.text(7 * 1.25 + 0.1, -1.2, 'Total #h/week', ha='left', va='center', fontsize=15, fontweight='bold', color='midnightblue', zorder=100)

        # Draw each week as a row
        for week_idx, week in enumerate(weeks):
            week_total = 0.0
            for day_idx, date_obj in enumerate(week):
                x = day_idx * 1.25
                y = week_idx * 1.25
                hours = day_hours.get(date_obj, 0.0)
                week_total += hours
                # For both custom and viridis_r, use a continuous gradient colormap
                if hours == 0:
                    color = 'white'
                else:
                    norm_hours = min(hours / MAX_HOURS, 1.0)
                    color = cmap(norm_hours)
                # Draw a rounded rectangle for the cell background
                ax.add_patch(plt.Rectangle((x-0.5, y-0.6), 1.0, 1.1, linewidth=0.7, edgecolor='gray', facecolor=color, alpha=0.7, zorder=1, joinstyle='round', clip_on=False))
                # Draw the day number (larger font, bold, with outline for contrast)
                ax.text(x, y-0.08, str(date_obj.day), ha='center', va='center',
                        fontsize=15, fontweight='bold', color='black', zorder=10, path_effects=[patheffects.withStroke(linewidth=2, foreground='white')])
                # Draw the hours (with 1 decimal) below the day number, only if any hours
                if hours > 0:
                    ax.text(x, y+0.28, f"{hours:.1f}", ha='center', va='center', fontsize=11, color='navy', zorder=11, fontweight='bold', path_effects=[patheffects.withStroke(linewidth=1.5, foreground='white')])
                # Mark the start of a month with a prominent label
                if date_obj.day == 1:
                    ax.text(x, y-0.7, date_obj.strftime('%B'), ha='center', va='center', fontsize=16, fontweight='bold', color='darkred', zorder=50, bbox=dict(boxstyle='round,pad=0.25', facecolor='white', edgecolor='none', alpha=0.7))
            # Write the week total to the right of Sunday
            x_total = 7 * 1.25 + 0.1
            y_total = week_idx * 1.25
            week_norm = min(week_total / WEEK_MAX, 1.0)
            week_color = cmap(week_norm) if week_total > 0 else 'white'
            ax.add_patch(plt.Rectangle((x_total-0.1, y_total-0.5), 1.1, 1.0, linewidth=0.7, edgecolor='gray', facecolor=week_color, alpha=0.85, zorder=1, joinstyle='round', clip_on=False))
            ax.text(x_total+0.45, y_total, f"{week_total:.1f}", ha='center', va='center', fontsize=13, color='black', fontweight='bold', zorder=41, path_effects=[patheffects.withStroke(linewidth=2, foreground='white')])
        # Draw grid lines (optional, now cell backgrounds are used)
        # Set x-ticks for weekdays (hidden, since we have headers)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_ylim(n_weeks*1.25-0.5, -2.0)
        ax.set_xlim(-0.5, 7*1.25+2.0)
        # Add colorbar/legend on the right with every integer hour (day scale)
        cbar_ax = fig.add_axes([0.92, 0.15, 0.015, 0.7])
        from matplotlib.colorbar import ColorbarBase
        from matplotlib.colors import Normalize
        norm = Normalize(vmin=0, vmax=MAX_HOURS)
        ColorbarBase(cbar_ax, cmap=cmap, norm=norm, orientation='vertical')
        hour_ticks = list(range(int(MAX_HOURS)+1))
        cbar_ax.set_yticks(hour_ticks)
        cbar_ax.set_yticklabels([str(h) for h in hour_ticks])
        # Add a second y-axis to the colorbar for weekly totals
        cbar_ax2 = cbar_ax.twinx()
        week_ticks = list(range(0, WEEK_MAX+1, 7))
        week_tick_positions = [wt/WEEK_MAX for wt in week_ticks]
        cbar_ax2.set_yticks(week_tick_positions)
        cbar_ax2.set_yticklabels([str(wt) for wt in week_ticks])
        # Set labels on left and right
        # Remove previous y-labels
        cbar_ax.set_ylabel('')
        cbar_ax2.set_ylabel('')
        # Add text labels to the left and right of the colorbar
        cbar_ax.figure.text(0.90, 0.87, 'Hours worked (per day)', va='center', ha='right', rotation=90, fontsize=11)
        cbar_ax.figure.text(0.96, 0.87, 'Hours worked (per week)', va='center', ha='left', rotation=90, fontsize=11)
        plt.suptitle(f"Work Hours Calendar {year} — {cmap_name}", fontsize=18)
        plt.tight_layout(rect=[0, 0, 0.91, 0.96])
        os.makedirs('plots', exist_ok=True)
        plt.savefig(f'plots/work_hours_calendar_{year}_{cmap_name}.png')
        plt.close(fig)


def main():
    # Find all years present in the data
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
    years = sorted(years)

    for year in years:
        day_hours = get_day_hours_by_year(INPUT_FILE, year)
        plot_colormap_calendar(year, day_hours)

if __name__ == '__main__':
    main()
