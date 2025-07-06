#!/usr/bin/env python3
"""
Command-line time tracking report generator.

Usage:
    python generate_report.py <weeks> [-o=csv]
    
Arguments:
    weeks: Number of weeks to include in the report
    -o=csv: Optional flag to output CSV format instead of ASCII table
"""

import argparse
import sys
import os

# Add the spf_time module to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'spf_time'))

from spf_time.database import DatabaseManager
from spf_time.config import Config
from spf_time.report_generator import ReportGenerator


def main():
    parser = argparse.ArgumentParser(
        description='Generate time tracking reports',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python generate_report.py 2           # Generate ASCII table for last 2 weeks
  python generate_report.py 4 -o=csv    # Generate CSV report for last 4 weeks
        """
    )
    
    parser.add_argument('weeks', type=int, help='Number of weeks to include in the report')
    parser.add_argument('-o', '--output', choices=['csv'], 
                       help='Output format (csv for CSV, omit for ASCII table)')
    
    args = parser.parse_args()
    
    # Validate weeks argument
    if args.weeks < 1:
        print("Error: Number of weeks must be at least 1", file=sys.stderr)
        sys.exit(1)
    
    if args.weeks > 52:
        print("Error: Number of weeks cannot exceed 52", file=sys.stderr)
        sys.exit(1)
    
    try:
        # Load configuration
        config = Config()
        
        # Create database manager
        db_manager = DatabaseManager(config.database.db_path)
        
        # Create report generator
        generator = ReportGenerator(config, db_manager)
        
        # Generate report data
        records, employees, start_date, end_date = generator.get_report_data(args.weeks)
        
        # Generate and display report
        if args.output == 'csv':
            report = generator.generate_csv_report(records, employees)
            print(report, end='')
        else:
            # ASCII table output
            print(f"Time Tracking Report - {args.weeks} Week{'s' if args.weeks > 1 else ''}")
            print(f"Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
            print()
            
            report = generator.generate_ascii_table(records, employees)
            print(report)
    
    except FileNotFoundError as e:
        print(f"Error: Configuration or database file not found: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error generating report: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()