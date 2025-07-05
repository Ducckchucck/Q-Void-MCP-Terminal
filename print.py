import time

total_progress = 100
total_minutes = 210  # 3.5 hours
interval_minutes = total_minutes / total_progress
interval_seconds = interval_minutes * 60

for i in range(1, total_progress + 1):
    progress = i
    hours_left = round(((total_progress - i) * interval_minutes) / 60, 2)
    print(f"Progress: {progress}% done | Hours left: {hours_left}")
    if i != total_progress:
        time.sleep(interval_seconds)
