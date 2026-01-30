"""
Process the universities.csv.xlsx file to find Institutional Research contacts

This script is specifically configured for the data/universities.csv.xlsx file
with 6,050+ universities from IPEDS data.

Usage:
    # Test with first 10 universities
    python process_universities.py --test

    # Process first 100 universities
    python process_universities.py --max 100

    # Process all universities (6,050+) - this will take hours!
    python process_universities.py --all

    # Resume from row 100
    python process_universities.py --start 100 --max 200

    # Use different provider
    python process_universities.py --provider openai --max 50
"""

import os
import sys
from pathlib import Path
import argparse
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from university_contact_finder import UniversityContactFinder


def estimate_cost(num_universities: int, provider: str) -> dict:
    """Estimate cost and time for processing"""
    estimates = {
        'perplexity': {
            'cost_per_uni': 0.015,
            'time_per_uni': 3.0,
            'name': 'Perplexity'
        },
        'openai': {
            'cost_per_uni': 0.025,
            'time_per_uni': 4.0,
            'name': 'OpenAI (GPT-4o-mini)'
        },
        'anthropic': {
            'cost_per_uni': 0.055,
            'time_per_uni': 5.0,
            'name': 'Anthropic Claude'
        },
        'ollama': {
            'cost_per_uni': 0.005,  # Just search API
            'time_per_uni': 8.0,
            'name': 'Ollama (local)'
        }
    }

    config = estimates.get(provider, estimates['perplexity'])

    total_cost = num_universities * config['cost_per_uni']
    total_time_sec = num_universities * config['time_per_uni']
    total_time_min = total_time_sec / 60
    total_time_hours = total_time_min / 60

    return {
        'provider': config['name'],
        'universities': num_universities,
        'estimated_cost': total_cost,
        'estimated_time_seconds': total_time_sec,
        'estimated_time_minutes': total_time_min,
        'estimated_time_hours': total_time_hours,
        'cost_per_university': config['cost_per_uni']
    }


def print_estimate(estimate: dict):
    """Print cost and time estimate"""
    print("\n" + "="*60)
    print("PROCESSING ESTIMATE")
    print("="*60)
    print(f"Provider: {estimate['provider']}")
    print(f"Universities to process: {estimate['universities']:,}")
    print(f"\nEstimated cost: ${estimate['estimated_cost']:.2f}")
    print(f"  (${estimate['cost_per_university']:.4f} per university)")

    if estimate['estimated_time_hours'] >= 1:
        print(f"\nEstimated time: {estimate['estimated_time_hours']:.1f} hours")
        print(f"  ({estimate['estimated_time_minutes']:.0f} minutes)")
    else:
        print(f"\nEstimated time: {estimate['estimated_time_minutes']:.1f} minutes")
        print(f"  ({estimate['estimated_time_seconds']:.0f} seconds)")

    print("="*60)


def main():
    parser = argparse.ArgumentParser(
        description="Process universities.csv.xlsx to find IR contacts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test with 10 universities
  python process_universities.py --test

  # Process first 100
  python process_universities.py --max 100

  # Process all (6,050+ universities - will take many hours!)
  python process_universities.py --all

  # Resume from row 100, process 50 more
  python process_universities.py --start 100 --max 50

  # Use Claude for higher quality
  python process_universities.py --provider anthropic --max 50

  # Exclude already-processed universities from one file
  python process_universities.py --exclude-from b_schools_contacts_full.xlsx --max 100

  # Exclude from multiple files
  python process_universities.py --exclude-from file1.xlsx file2.xlsx --max 100

  # Adjust fuzzy matching sensitivity (0.9 = stricter, 0.75 = looser)
  python process_universities.py --exclude-from existing.xlsx --fuzzy-threshold 0.9
        """
    )

    parser.add_argument("--test", action="store_true",
                       help="Test mode: process only first 10 universities")
    parser.add_argument("--all", action="store_true",
                       help="Process ALL universities (6,050+). WARNING: This will take many hours!")
    parser.add_argument("--max", type=int,
                       help="Maximum number of universities to process")
    parser.add_argument("--start", type=int, default=0,
                       help="Row number to start from (for resuming)")
    parser.add_argument("--provider", choices=["openai", "anthropic", "perplexity", "ollama"],
                       default="perplexity",
                       help="LLM provider to use (default: perplexity)")
    parser.add_argument("--search-api", choices=["perplexity", "tavily", "brave", "serp"],
                       default="perplexity",
                       help="Search API to use (default: perplexity)")
    parser.add_argument("--delay", type=float, default=1.0,
                       help="Delay between requests in seconds (default: 1.0)")
    parser.add_argument("--input", help="Input file path (default: data/universities.csv.xlsx)")
    parser.add_argument("--output", help="Output file path (default: data/universities_with_contacts.xlsx)")
    parser.add_argument("--skip-existing", action="store_true",
                       help="Skip universities that already have contacts (for merged files)")
    parser.add_argument("--exclude-from", nargs='+', metavar="FILE",
                       help="Skip universities found in these file(s). Supports multiple files.")
    parser.add_argument("--fuzzy-threshold", type=float, default=0.85,
                       help="Fuzzy matching threshold (0-1) for exclusions (default: 0.85)")
    parser.add_argument("--no-confirm", action="store_true",
                       help="Skip confirmation prompt")

    args = parser.parse_args()

    # Configuration
    input_file = args.input or "data/universities.csv.xlsx"
    output_file = args.output or input_file.replace('.xlsx', '_with_contacts.xlsx')

    # Check if input file exists
    if not Path(input_file).exists():
        print(f"❌ Error: Input file not found: {input_file}")
        print("\nMake sure you have the universities.csv.xlsx file in the data/ directory.")
        return 1

    # Determine number of universities to process
    if args.test:
        max_universities = 10
        print("\n[TEST] TEST MODE: Processing first 10 universities")
    elif args.all:
        max_universities = None
        print("\n[WARNING] ALL MODE: Processing ALL universities (6,050+)")
    elif args.max:
        max_universities = args.max
    else:
        # Default to 10 if nothing specified
        max_universities = 10
        print("\n[INFO] No limit specified, processing first 10 universities")
        print("   Use --max N to process more, or --all for everything")

    # Calculate estimate
    if max_universities:
        estimate = estimate_cost(max_universities, args.provider)
    else:
        # Estimate for all 6050
        estimate = estimate_cost(6050, args.provider)

    print_estimate(estimate)

    # Confirmation prompt (unless --no-confirm)
    if not args.no_confirm:
        print("\n[WARNING] IMPORTANT NOTES:")
        print("* Not all universities will have IR office contacts available")
        print("* Some universities may be small/specialized institutions")
        print("* Progress is saved after each university (can resume if interrupted)")
        print("* Results will include 'contacts_found' count (may be 0 for some)")
        print()

        if estimate['estimated_time_hours'] >= 2:
            print("[TIME WARNING] This will take several hours. Consider:")
            print("   * Starting with --max 100 to test")
            print("   * Running overnight for large batches")
            print("   * Using --start to resume if interrupted")
            print()

        response = input("Continue? (y/N): ")
        if response.lower() != 'y':
            print("\n[CANCELLED] Operation cancelled")
            return 0

    # Create finder
    print(f"\n[INIT] Initializing {args.provider}...")
    try:
        finder = UniversityContactFinder(
            provider=args.provider,
            search_api=args.search_api,
            rate_limit_delay=args.delay
        )
    except Exception as e:
        print(f"\n[ERROR] Error initializing: {str(e)}")
        print("\nMake sure you have:")
        print("1. Created .env file with your API keys")
        print("2. Installed all dependencies: pip install -r requirements_university_finder.txt")
        return 1

    # Process the file
    print(f"\n[CONFIG] Input file: {input_file}")
    print(f"[CONFIG] Output file: {output_file}")
    print(f"[CONFIG] Column: 'Institution Name'")
    if args.start > 0:
        print(f"[CONFIG] Starting from row: {args.start}")
    if max_universities:
        print(f"[CONFIG] Max universities: {max_universities}")
    if args.exclude_from:
        print(f"[CONFIG] Excluding universities from: {', '.join(args.exclude_from)}")
        print(f"[CONFIG] Fuzzy match threshold: {args.fuzzy_threshold:.0%}")
    print()

    start_time = datetime.now()

    try:
        result_df = finder.process_excel(
            input_file=input_file,
            output_file=output_file,
            university_column="Institution Name",  # The actual column name in your file
            start_row=args.start,
            max_universities=max_universities,
            skip_existing=args.skip_existing,
            exclude_files=args.exclude_from,
            fuzzy_threshold=args.fuzzy_threshold
        )

        end_time = datetime.now()
        duration = end_time - start_time

        # Print summary statistics
        print("\n" + "="*60)
        print("PROCESSING SUMMARY")
        print("="*60)

        total_processed = len(result_df)
        successful = len(result_df[result_df['search_status'] == 'completed'])
        with_contacts = len(result_df[result_df['contacts_found'] > 0])
        total_contacts = result_df['contacts_found'].sum()

        print(f"Total universities processed: {total_processed:,}")
        print(f"Successful searches: {successful:,}")
        print(f"Universities with contacts found: {with_contacts:,} ({with_contacts/total_processed*100:.1f}%)")
        print(f"Total contacts extracted: {int(total_contacts):,}")
        print(f"\nTime taken: {duration}")
        print(f"Average time per university: {duration.total_seconds()/total_processed:.1f} seconds")
        print(f"\n[SAVED] Results saved to: {output_file}")
        print("="*60)

        # Show sample of results
        if with_contacts > 0:
            print("\n[SAMPLE] Sample Results (universities with contacts):")
            sample = result_df[result_df['contacts_found'] > 0][
                ['Institution Name', 'contacts_found', 'contact_1_name', 'contact_1_email']
            ].head(5)
            print(sample.to_string(index=False))

        return 0

    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] Process interrupted by user")
        print(f"[SAVED] Progress saved to: {output_file}")
        print(f"\nTo resume, run:")
        print(f"python process_universities.py --start {args.start + (max_universities or 0)}")
        return 1

    except Exception as e:
        print(f"\n[ERROR] Error during processing: {str(e)}")
        print(f"\nPartial results may be saved in: {output_file}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
