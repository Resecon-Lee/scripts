"""
Merge Comprehensive IR Contacts Database with Main Universities List

This script:
1. Takes the main 6,050 universities list
2. Merges IR contacts from the comprehensive database (4,786 universities)
3. Adds any NEW universities from comprehensive database not in main list
4. Ensures no duplicates

Usage:
    python merge_comprehensive_contacts.py
"""

import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path


def normalize_name(name):
    """Normalize university name for matching"""
    if pd.isna(name):
        return ""
    name = str(name).lower().strip()
    # Remove common variations
    name = name.replace(" - ", "-")
    name = name.replace("university of", "univ of")
    name = name.replace("state university", "state univ")
    name = name.replace("  ", " ")
    return name


def merge_comprehensive_contacts():
    """Merge comprehensive contacts with main database"""
    print("\n" + "="*70)
    print("COMPREHENSIVE IR CONTACTS MERGER")
    print("="*70)

    # File paths
    main_file = "data/universities.csv.xlsx"
    comprehensive_file = "data/Comprehensive_US_Universities_IR_Contacts_Database.csv"
    output_file = "data/universities_master_with_contacts.xlsx"

    # Check files exist
    if not Path(main_file).exists():
        print(f"\n[ERROR] File not found: {main_file}")
        return

    if not Path(comprehensive_file).exists():
        print(f"\n[ERROR] File not found: {comprehensive_file}")
        return

    # Read files
    print(f"\n[READING] {main_file}")
    df_main = pd.read_excel(main_file)
    print(f"  Found {len(df_main):,} universities in main database")

    print(f"\n[READING] {comprehensive_file}")
    df_comprehensive = pd.read_csv(comprehensive_file)
    print(f"  Found {len(df_comprehensive):,} universities with IR contacts")

    print(f"\n[INFO] Main database columns: {df_main.columns.tolist()[:5]}...")
    print(f"[INFO] Comprehensive database columns: {df_comprehensive.columns.tolist()}")

    # Create matching keys
    print(f"\n[PROCESSING] Creating match keys...")
    df_main['match_name'] = df_main['Institution Name'].apply(normalize_name)
    df_comprehensive['match_name'] = df_comprehensive['University_Name'].apply(normalize_name)

    # Match on IPEDS ID (most accurate)
    use_ipeds = 'UnitID' in df_main.columns and 'IPEDS_ID' in df_comprehensive.columns
    if use_ipeds:
        print(f"  Using IPEDS ID + name matching")
    else:
        print(f"  Using name matching only")

    # Prepare columns to add from comprehensive database
    contact_mapping = {
        'IR_Office_Contact': 'ir_office_contact',
        'IR_Office_Email': 'ir_office_email',
        'IR_Office_Phone': 'ir_office_phone',
        'Academic_Affairs_Email': 'ir_academic_affairs_email',
        'IR_Director_Name': 'ir_director_name',
        'Phone': 'ir_main_phone',
        'Website': 'ir_website',
        'Address': 'ir_address',
        'Institution_Type': 'ir_institution_type',
        'Level': 'ir_level'
    }

    # Initialize new columns in main database
    for new_col in contact_mapping.values():
        df_main[new_col] = None

    df_main['has_ir_contact'] = False
    df_main['ir_match_method'] = None
    df_main['ir_data_source'] = None

    # Match and merge
    print(f"\n[MATCHING] Cross-referencing universities...")
    matches_found = 0
    ipeds_matches = 0
    name_matches = 0

    matched_comprehensive_ids = set()

    for idx, main_row in df_main.iterrows():
        matched = False
        match_method = None
        contact_row = None

        # Try IPEDS ID match first
        if use_ipeds and not pd.isna(main_row['UnitID']):
            ipeds_match = df_comprehensive[df_comprehensive['IPEDS_ID'] == main_row['UnitID']]
            if not ipeds_match.empty:
                contact_row = ipeds_match.iloc[0]
                matched = True
                match_method = 'IPEDS ID'
                ipeds_matches += 1
                matched_comprehensive_ids.add(ipeds_match.index[0])

        # Try name match if IPEDS didn't work
        if not matched and main_row['match_name']:
            name_match = df_comprehensive[df_comprehensive['match_name'] == main_row['match_name']]
            if not name_match.empty:
                contact_row = name_match.iloc[0]
                matched = True
                match_method = 'Name'
                name_matches += 1
                matched_comprehensive_ids.add(name_match.index[0])

        # Copy contact info if matched
        if matched:
            for source_col, dest_col in contact_mapping.items():
                if source_col in df_comprehensive.columns:
                    value = contact_row[source_col]
                    if not pd.isna(value) and str(value).strip():
                        df_main.at[idx, dest_col] = value

            df_main.at[idx, 'has_ir_contact'] = True
            df_main.at[idx, 'ir_match_method'] = match_method
            df_main.at[idx, 'ir_data_source'] = 'Comprehensive Database'
            matches_found += 1

            if matches_found % 100 == 0:
                print(f"  Matched {matches_found} universities...", end='\r')

    print(f"  Matched {matches_found} universities...     ")

    # Find universities in comprehensive database but NOT in main database
    print(f"\n[PROCESSING] Finding new universities from comprehensive database...")
    unmatched_comprehensive = df_comprehensive[~df_comprehensive.index.isin(matched_comprehensive_ids)]
    print(f"  Found {len(unmatched_comprehensive):,} new universities to add")

    # Prepare new universities to add
    if len(unmatched_comprehensive) > 0:
        print(f"[ADDING] Adding new universities to master database...")

        # Create DataFrame with new universities in same format as main
        new_universities = pd.DataFrame()

        # Map comprehensive columns to main columns
        new_universities['Institution Name'] = unmatched_comprehensive['University_Name']
        new_universities['State abbreviation (HD2024)'] = unmatched_comprehensive['State']
        new_universities['City location of institution (HD2024)'] = unmatched_comprehensive['City']
        new_universities['UnitID'] = unmatched_comprehensive['IPEDS_ID']

        # Add IR contact info
        for source_col, dest_col in contact_mapping.items():
            if source_col in unmatched_comprehensive.columns:
                new_universities[dest_col] = unmatched_comprehensive[source_col].values

        new_universities['has_ir_contact'] = True
        new_universities['ir_match_method'] = 'New from Comprehensive'
        new_universities['ir_data_source'] = 'Comprehensive Database'
        new_universities['match_name'] = unmatched_comprehensive['match_name'].values

        # Fill in missing columns from main database with None
        for col in df_main.columns:
            if col not in new_universities.columns:
                new_universities[col] = None

        # Ensure columns are in same order
        new_universities = new_universities[df_main.columns]

        # Append to main database
        df_main = pd.concat([df_main, new_universities], ignore_index=True)
        print(f"  Added {len(new_universities):,} new universities")

    # Add metadata
    df_main['last_updated'] = None
    df_main.loc[df_main['has_ir_contact'], 'last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Drop temporary match column
    df_main = df_main.drop(columns=['match_name'])

    # Save final merged file
    print(f"\n[SAVING] Writing master database...")
    df_main.to_excel(output_file, index=False)

    # Statistics
    total_universities = len(df_main)
    with_contacts = df_main['has_ir_contact'].sum()
    without_contacts = total_universities - with_contacts
    new_added = len(unmatched_comprehensive) if len(unmatched_comprehensive) > 0 else 0

    print(f"\n" + "="*70)
    print("MERGE SUMMARY")
    print("="*70)
    print(f"Original main database: 6,050 universities")
    print(f"Comprehensive database: 4,786 universities with contacts")
    print()
    print(f"MATCHING RESULTS:")
    print(f"  Universities matched with existing records: {matches_found:,}")
    print(f"    - Matched by IPEDS ID: {ipeds_matches:,}")
    print(f"    - Matched by name: {name_matches:,}")
    print(f"  New universities added from comprehensive: {new_added:,}")
    print()
    print(f"FINAL MASTER DATABASE:")
    print(f"  Total universities: {total_universities:,}")
    print(f"  With IR contacts: {with_contacts:,} ({with_contacts/total_universities*100:.1f}%)")
    print(f"  Still need contacts: {without_contacts:,} ({without_contacts/total_universities*100:.1f}%)")
    print()
    print(f"[SAVED] Master database: {output_file}")
    print("="*70)

    # Show samples
    print(f"\n[SAMPLE] Universities with IR contacts (first 5):")
    sample = df_main[df_main['has_ir_contact']][
        ['Institution Name', 'ir_director_name', 'ir_office_email', 'ir_match_method']
    ].head(5)
    if not sample.empty:
        print(sample.to_string(index=False))

    print(f"\n[SAMPLE] New universities added from comprehensive (first 5):")
    sample_new = df_main[df_main['ir_match_method'] == 'New from Comprehensive'][
        ['Institution Name', 'State abbreviation (HD2024)', 'ir_office_email']
    ].head(5)
    if not sample_new.empty:
        print(sample_new.to_string(index=False))

    print(f"\n[SAMPLE] Universities still needing contacts (first 5):")
    sample_missing = df_main[~df_main['has_ir_contact']][
        ['Institution Name', 'City location of institution (HD2024)', 'State abbreviation (HD2024)']
    ].head(5)
    if not sample_missing.empty:
        print(sample_missing.to_string(index=False))

    # Cost estimate
    universities_need_search = without_contacts
    estimated_cost = universities_need_search * 0.015

    print(f"\n[COST ESTIMATE]")
    print(f"Universities needing web search: {universities_need_search:,}")
    print(f"Estimated cost (Perplexity): ${estimated_cost:.2f}")
    print(f"Estimated time: {universities_need_search * 3 / 3600:.1f} hours")

    print(f"\n[NEXT STEPS]")
    print(f"To search the web for remaining {universities_need_search:,} universities:")
    print(f"  python process_universities.py --input {output_file} --skip-existing --max 100")
    print()

    return df_main, with_contacts, without_contacts


if __name__ == "__main__":
    try:
        merge_comprehensive_contacts()
    except Exception as e:
        print(f"\n[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
