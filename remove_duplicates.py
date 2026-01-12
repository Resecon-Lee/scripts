"""
Remove duplicate universities based on IPEDS ID (UnitID)

Keeps the first occurrence of each IPEDS ID and removes subsequent duplicates.
"""

import pandas as pd
from datetime import datetime

print("="*70)
print("REMOVE DUPLICATES FROM MASTER DATABASE")
print("="*70)

# Read master file
input_file = "data/universities_master_with_contacts.xlsx"
output_file = "data/universities_master_with_contacts_deduped.xlsx"
backup_file = "data/universities_master_with_contacts_BACKUP.xlsx"

print(f"\n[READING] {input_file}")
df = pd.read_excel(input_file)
original_count = len(df)
print(f"  Total records: {original_count:,}")

# Check for duplicates
print(f"\n[CHECKING] Looking for duplicates based on UnitID (IPEDS)...")
duplicates = df[df.duplicated(subset=['UnitID'], keep=False)]
duplicate_count = len(duplicates)
num_unique_dups = len(duplicates['UnitID'].unique())

if duplicate_count > 0:
    print(f"\n[FOUND] {duplicate_count} duplicate records")
    print(f"  Affecting {num_unique_dups} unique IPEDS IDs")

    # Show sample duplicates
    print(f"\n[SAMPLE] First 5 duplicate groups:")
    for i, ipeds_id in enumerate(duplicates['UnitID'].unique()[:5]):
        dup_rows = df[df['UnitID'] == ipeds_id]
        print(f"\n  {i+1}. IPEDS ID: {ipeds_id}")
        for idx, row in dup_rows.iterrows():
            print(f"     - {row['Institution Name']} ({row['City location of institution (HD2024)']})")

    # Create backup
    print(f"\n[BACKUP] Creating backup of original file...")
    df.to_excel(backup_file, index=False)
    print(f"  Saved to: {backup_file}")

    # Remove duplicates - keep first occurrence
    print(f"\n[REMOVING] Removing duplicate records (keeping first occurrence)...")
    df_deduped = df.drop_duplicates(subset=['UnitID'], keep='first')
    records_removed = original_count - len(df_deduped)

    print(f"  Removed {records_removed} duplicate records")
    print(f"  Remaining records: {len(df_deduped):,}")

    # Save deduplicated file
    print(f"\n[SAVING] Writing deduplicated database...")
    df_deduped.to_excel(output_file, index=False)

    # Also overwrite original file
    print(f"[UPDATING] Overwriting original file...")
    df_deduped.to_excel(input_file, index=False)

    # Statistics
    print(f"\n" + "="*70)
    print("DEDUPLICATION SUMMARY")
    print("="*70)
    print(f"Original records: {original_count:,}")
    print(f"Duplicate records found: {duplicate_count}")
    print(f"Unique IPEDS IDs affected: {num_unique_dups}")
    print(f"Records removed: {records_removed}")
    print(f"Final unique records: {len(df_deduped):,}")
    print()
    print(f"Universities with IR contacts: {df_deduped['has_ir_contact'].sum():,}")
    print(f"Universities needing contacts: {(~df_deduped['has_ir_contact']).sum():,}")
    print()
    print(f"[SAVED] Deduplicated file: {output_file}")
    print(f"[UPDATED] Original file: {input_file}")
    print(f"[BACKUP] Backup saved: {backup_file}")
    print("="*70)

    # Show which duplicates were removed
    print(f"\n[INFO] Records removed (duplicates that were kept):")
    removed = df[df.duplicated(subset=['UnitID'], keep='first')]
    print(removed[['UnitID', 'Institution Name', 'City location of institution (HD2024)', 'ir_office_email']].to_string(index=False))

else:
    print(f"\n[SUCCESS] No duplicates found!")
    print(f"Database is clean: {original_count:,} unique records")

print()
