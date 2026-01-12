"""
Merge existing IR contacts database with universities list

This script cross-references the universities.csv.xlsx file with the
US_Universities_IR_Contacts_Database.xlsx to pre-fill known contacts
before running web searches.

Usage:
    python merge_ir_contacts.py
"""

import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path


def normalize_name(name):
    """Normalize university name for matching"""
    if pd.isna(name):
        return ""
    # Convert to lowercase, remove common suffixes/variations
    name = str(name).lower().strip()
    # Remove common variations
    name = name.replace(" - ", "-")
    name = name.replace("university of", "univ of")
    name = name.replace("state university", "state univ")
    return name


def merge_contacts():
    """Merge the two files"""
    print("\n" + "="*70)
    print("IR CONTACTS MERGER")
    print("="*70)

    # File paths
    universities_file = "data/universities.csv.xlsx"
    contacts_file = "data/US_Universities_IR_Contacts_Database.xlsx"
    output_file = "data/universities_with_existing_contacts.xlsx"

    # Check files exist
    if not Path(universities_file).exists():
        print(f"\n[ERROR] File not found: {universities_file}")
        return

    if not Path(contacts_file).exists():
        print(f"\n[ERROR] File not found: {contacts_file}")
        return

    # Read files
    print(f"\n[READING] {universities_file}")
    df_universities = pd.read_excel(universities_file)
    print(f"  Found {len(df_universities):,} universities")

    print(f"\n[READING] {contacts_file}")
    df_contacts = pd.read_excel(contacts_file)
    print(f"  Found {len(df_contacts):,} universities with IR contacts")

    # Show columns
    print(f"\n[INFO] Universities file columns:")
    print(f"  - {df_universities.columns.tolist()[:5]}...")
    print(f"\n[INFO] Contacts file columns:")
    print(f"  - {df_contacts.columns.tolist()}")

    # Create matching columns
    print(f"\n[PROCESSING] Creating match keys...")
    df_universities['match_name'] = df_universities['Institution Name'].apply(normalize_name)
    df_contacts['match_name'] = df_contacts['University Name'].apply(normalize_name)

    # Also try matching on IPEDS ID (UnitID)
    if 'UnitID' in df_universities.columns and 'IPEDS ID' in df_contacts.columns:
        print(f"  Using IPEDS ID for matching (more accurate)")
        use_ipeds = True
    else:
        print(f"  Using name matching only")
        use_ipeds = False

    # Prepare contact columns to add
    contact_columns = {
        'IR Office Name': 'existing_ir_office_name',
        'IR Office Address': 'existing_ir_office_address',
        'IR Office Email': 'existing_ir_office_email',
        'IR Office Phone': 'existing_ir_office_phone',
        'IR Director Name': 'existing_ir_director_name',
        'IR Director Email': 'existing_ir_director_email',
        'Main Phone': 'existing_main_phone',
        'Website': 'existing_website',
        'State': 'existing_state',
        'City': 'existing_city'
    }

    # Initialize new columns
    for new_col in contact_columns.values():
        df_universities[new_col] = None

    df_universities['has_existing_contact'] = False
    df_universities['match_method'] = None

    # Perform matching
    print(f"\n[MATCHING] Cross-referencing universities...")
    matches_found = 0
    ipeds_matches = 0
    name_matches = 0

    for idx, uni_row in df_universities.iterrows():
        matched = False
        match_method = None

        # Try IPEDS ID match first (most accurate)
        if use_ipeds and not pd.isna(uni_row['UnitID']):
            ipeds_match = df_contacts[df_contacts['IPEDS ID'] == uni_row['UnitID']]
            if not ipeds_match.empty:
                contact_row = ipeds_match.iloc[0]
                matched = True
                match_method = 'IPEDS ID'
                ipeds_matches += 1

        # Try name match if IPEDS didn't work
        if not matched and uni_row['match_name']:
            name_match = df_contacts[df_contacts['match_name'] == uni_row['match_name']]
            if not name_match.empty:
                contact_row = name_match.iloc[0]
                matched = True
                match_method = 'Name'
                name_matches += 1

        # If matched, copy contact info
        if matched:
            for source_col, dest_col in contact_columns.items():
                if source_col in df_contacts.columns:
                    value = contact_row[source_col]
                    if not pd.isna(value):
                        df_universities.at[idx, dest_col] = value

            df_universities.at[idx, 'has_existing_contact'] = True
            df_universities.at[idx, 'match_method'] = match_method
            matches_found += 1

            if matches_found % 10 == 0:
                print(f"  Matched {matches_found} universities...", end='\r')

    print(f"  Matched {matches_found} universities...     ")

    # Add metadata columns
    df_universities['data_source'] = None
    df_universities.loc[df_universities['has_existing_contact'], 'data_source'] = 'Existing Database'
    df_universities['last_updated'] = None
    df_universities.loc[df_universities['has_existing_contact'], 'last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Drop temporary match columns
    df_universities = df_universities.drop(columns=['match_name'])

    # Save merged file
    print(f"\n[SAVING] Writing merged file...")
    df_universities.to_excel(output_file, index=False)

    # Statistics
    print(f"\n" + "="*70)
    print("MERGE SUMMARY")
    print("="*70)
    print(f"Total universities in list: {len(df_universities):,}")
    print(f"Universities with existing IR contacts: {matches_found:,} ({matches_found/len(df_universities)*100:.1f}%)")
    print(f"  - Matched by IPEDS ID: {ipeds_matches:,}")
    print(f"  - Matched by name: {name_matches:,}")
    print(f"Universities still needing contacts: {len(df_universities) - matches_found:,} ({(len(df_universities) - matches_found)/len(df_universities)*100:.1f}%)")
    print(f"\n[SAVED] Merged file: {output_file}")
    print("="*70)

    # Show sample matches
    print(f"\n[SAMPLE] Universities with existing contacts (first 5):")
    sample = df_universities[df_universities['has_existing_contact']][
        ['Institution Name', 'existing_ir_director_name', 'existing_ir_director_email', 'match_method']
    ].head(5)
    if not sample.empty:
        print(sample.to_string(index=False))

    # Show universities that still need searching
    print(f"\n[SAMPLE] Universities still needing contacts (first 5):")
    sample_missing = df_universities[~df_universities['has_existing_contact']][
        ['Institution Name', 'City location of institution (HD2024)', 'State abbreviation (HD2024)']
    ].head(5)
    print(sample_missing.to_string(index=False))

    print(f"\n[NEXT STEPS]")
    print(f"To search the web for remaining {len(df_universities) - matches_found:,} universities:")
    print(f"  python process_universities.py --input {output_file} --skip-existing --max 100")
    print()

    return df_universities, matches_found


if __name__ == "__main__":
    try:
        merge_contacts()
    except Exception as e:
        print(f"\n[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
