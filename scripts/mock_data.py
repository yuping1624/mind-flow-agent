import pandas as pd
import datetime
import random
import os
import sys

# Get scripts directory (where this file is located)
scripts_dir = os.path.dirname(os.path.abspath(__file__))

# File paths - save demo files in scripts/ directory
JOURNAL_DB_PATH = os.path.join(scripts_dir, "mind_flow_db_demo.csv")
PLANS_DB_PATH = os.path.join(scripts_dir, "plans_database_demo.csv")

# Simulate data for the past 7 days
base_time = datetime.datetime.now() - datetime.timedelta(days=7)

# Mood options
moods = ["Anxious", "Tired", "Flowing", "Motivated", "Stuck", "Relieved", "Energetic"]

# Sample notes for journal entries
notes = [
    "Completed 10 pushups despite feeling tired.",
    "Wrote 300 words for thesis.",
    "Did a micro-meditation session.",
    "Cleaned the desk to prepare for tomorrow.",
    "Almost gave up but Starter helped me do 1 rep.",
    "Had a great deep work session.",
    "Set up the alarm for early morning run.",
    "Did 5 pushups before breakfast.",
    "Completed morning routine despite low energy.",
    "Felt accomplished after finishing the task."
]

print("Generating mock data...")

# 1. Generate Plan Update (set goal) - saved to plans_database.csv
plan_data = []
plan_data.append({
    "timestamp": base_time.strftime("%Y-%m-%d %H:%M:%S"),
    "vision": "Lose 6kg of fat in 12 weeks",
    "system": "Do 30 push-ups every day"
})

# 2. Generate daily journal logs - saved to mind_flow_db.csv
journal_data = []

for i in range(7):
    current_day = base_time + datetime.timedelta(days=i)
    
    # Generate 1-2 entries per day
    for _ in range(random.randint(1, 2)):
        # Random time (evening)
        log_time = current_day.replace(
            hour=random.randint(18, 23), 
            minute=random.randint(0, 59)
        )
        
        # Energy index (simulate trend from low to high)
        energy = min(10, random.randint(3, 6) + int(i * 0.5))
        mood = random.choice(moods)
        note = random.choice(notes)
        
        journal_data.append({
            "Timestamp": log_time.strftime("%Y-%m-%d %H:%M"),
            "Mood": mood,
            "Energy": energy,
            "Note": note
        })

# Save journal data to CSV
df_journal = pd.DataFrame(journal_data)
df_journal.to_csv(JOURNAL_DB_PATH, index=False, encoding="utf-8")
print(f"✅ Generated {len(df_journal)} journal entries to {JOURNAL_DB_PATH}")

# Save plan data to CSV
df_plan = pd.DataFrame(plan_data)
df_plan.to_csv(PLANS_DB_PATH, index=False, encoding="utf-8")
print(f"✅ Generated {len(df_plan)} plan update to {PLANS_DB_PATH}")

print(f"\n🎉 Successfully generated mock data for 7 days!")
print("Your dashboard will now have beautiful charts!")

