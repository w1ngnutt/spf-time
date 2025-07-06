"""
Shared report generation functionality for time tracking data.
Used by both email reports and command-line reporting tool.
"""

import datetime
import csv
import io
from typing import List, Dict, Tuple

from .database import DatabaseManager, TimeRecord
from .config import Config


class ReportGenerator:
    def __init__(self, config: Config, db_manager: DatabaseManager):
        self.config = config
        self.db_manager = db_manager
    
    def get_previous_complete_weeks_range(self, num_weeks: int) -> Tuple[datetime.date, datetime.date]:
        """Calculate date range for the specified number of complete work weeks"""
        today = datetime.date.today()
        work_week_start_day = self.config.payroll.start_day
        
        # Find the start of the current work week
        days_since_start = (today.weekday() - work_week_start_day) % 7
        current_week_start = today - datetime.timedelta(days=days_since_start)
        
        # Go back to the start of the previous week (1 week ago)
        previous_week_start = current_week_start - datetime.timedelta(weeks=1)
        
        # Calculate start date based on number of weeks requested
        start_date = previous_week_start - datetime.timedelta(weeks=num_weeks-1)
        
        # End date is the last day of the previous week
        end_date = current_week_start - datetime.timedelta(days=1)
        
        return start_date, end_date
    
    def get_report_data(self, num_weeks: int) -> Tuple[List[TimeRecord], Dict[int, str], datetime.date, datetime.date]:
        """Generate report data for the specified number of complete weeks"""
        start_date, end_date = self.get_previous_complete_weeks_range(num_weeks)
        
        # Get time records
        records = self.db_manager.get_time_records(
            start_date=start_date,
            end_date=end_date
        )
        
        # Get employee names
        employees = {emp.id: emp.name for emp in self.db_manager.get_employees(active_only=False)}
        
        return records, employees, start_date, end_date
    
    def generate_csv_report(self, records: List[TimeRecord], employees: Dict[int, str]) -> str:
        """Generate CSV report"""
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['Employee', 'Date', 'Clock In', 'Clock Out', 'Duration (Hours)'])
        
        for record in records:
            employee_name = employees.get(record.employee_id, 'Unknown')
            date = record.clock_in.strftime('%Y-%m-%d')
            clock_in = record.clock_in.strftime('%H:%M:%S')
            clock_out = record.clock_out.strftime('%H:%M:%S') if record.clock_out else 'Still Clocked In'
            
            if record.clock_out:
                duration = record.clock_out - record.clock_in
                duration_hours = round(duration.total_seconds() / 3600, 2)
            else:
                duration_hours = 'Ongoing'
            
            writer.writerow([employee_name, date, clock_in, clock_out, duration_hours])
        
        return output.getvalue()
    
    def generate_ascii_table(self, records: List[TimeRecord], employees: Dict[int, str]) -> str:
        """Generate ASCII table report for console output"""
        if not records:
            return "No time records found for the specified period."
        
        # Prepare data rows
        rows = []
        for record in records:
            employee_name = employees.get(record.employee_id, 'Unknown')
            date = record.clock_in.strftime('%Y-%m-%d')
            clock_in = record.clock_in.strftime('%H:%M:%S')
            clock_out = record.clock_out.strftime('%H:%M:%S') if record.clock_out else 'Still Clocked In'
            
            if record.clock_out:
                duration = record.clock_out - record.clock_in
                duration_hours = f"{round(duration.total_seconds() / 3600, 2):.2f}"
            else:
                duration_hours = 'Ongoing'
            
            rows.append([employee_name, date, clock_in, clock_out, duration_hours])
        
        # Calculate column widths
        headers = ['Employee', 'Date', 'Clock In', 'Clock Out', 'Duration (Hours)']
        col_widths = [len(header) for header in headers]
        
        for row in rows:
            for i, cell in enumerate(row):
                col_widths[i] = max(col_widths[i], len(str(cell)))
        
        # Add padding
        col_widths = [w + 2 for w in col_widths]
        
        # Generate table
        separator = '+' + '+'.join(['-' * w for w in col_widths]) + '+'
        
        result = []
        result.append(separator)
        
        # Header row
        header_row = '|' + '|'.join([f" {headers[i]:<{col_widths[i]-1}}" for i in range(len(headers))]) + '|'
        result.append(header_row)
        result.append(separator)
        
        # Data rows
        for row in rows:
            data_row = '|' + '|'.join([f" {str(row[i]):<{col_widths[i]-1}}" for i in range(len(row))]) + '|'
            result.append(data_row)
        
        result.append(separator)
        
        # Calculate totals by employee
        employee_totals = self.calculate_employee_totals(records, employees)
        
        # Add summary
        result.append("")
        result.append("Summary:")
        result.append("-" * 50)
        for employee, total_hours in employee_totals.items():
            result.append(f"{employee}: {total_hours:.2f} hours")
        
        total_all_hours = sum(employee_totals.values())
        result.append(f"Total: {total_all_hours:.2f} hours")
        
        return '\n'.join(result)
    
    def calculate_employee_totals(self, records: List[TimeRecord], employees: Dict[int, str]) -> Dict[str, float]:
        """Calculate total hours worked by each employee"""
        employee_totals = {}
        for record in records:
            employee_name = employees.get(record.employee_id, 'Unknown')
            if record.clock_out:
                duration = record.clock_out - record.clock_in
                hours = duration.total_seconds() / 3600
                employee_totals[employee_name] = employee_totals.get(employee_name, 0) + hours
        return employee_totals
    
    def generate_email_tables(self, records: List[TimeRecord], employees: Dict[int, str]) -> str:
        """Generate HTML tables for email reports (grouped by employee and week)"""
        if not records:
            return "<p>No time records found for the specified period.</p>"
        
        # Group records by employee and week
        employee_weeks = {}
        for record in records:
            employee_name = employees.get(record.employee_id, 'Unknown')
            # Calculate week start based on work week start day
            record_date = record.clock_in.date()
            days_since_start = (record_date.weekday() - self.config.payroll.start_day) % 7
            week_start = record_date - datetime.timedelta(days=days_since_start)
            
            if employee_name not in employee_weeks:
                employee_weeks[employee_name] = {}
            
            if week_start not in employee_weeks[employee_name]:
                employee_weeks[employee_name][week_start] = []
            
            employee_weeks[employee_name][week_start].append(record)
        
        # Generate HTML tables
        html_parts = []
        
        for employee_name in sorted(employee_weeks.keys()):
            html_parts.append(f"<h3>{employee_name}</h3>")
            
            for week_start in sorted(employee_weeks[employee_name].keys()):
                week_end = week_start + datetime.timedelta(days=6)
                week_records = employee_weeks[employee_name][week_start]
                
                html_parts.append(f"<h4>Week: {week_start.strftime('%Y-%m-%d')} to {week_end.strftime('%Y-%m-%d')}</h4>")
                html_parts.append("<table border='1' cellpadding='5' cellspacing='0'>")
                html_parts.append("<tr><th>Date</th><th>Clock In</th><th>Clock Out</th><th>Duration (Hours)</th></tr>")
                
                week_total = 0
                for record in sorted(week_records, key=lambda r: r.clock_in):
                    date = record.clock_in.strftime('%Y-%m-%d')
                    clock_in = record.clock_in.strftime('%H:%M:%S')
                    clock_out = record.clock_out.strftime('%H:%M:%S') if record.clock_out else 'Still Clocked In'
                    
                    if record.clock_out:
                        duration = record.clock_out - record.clock_in
                        duration_hours = round(duration.total_seconds() / 3600, 2)
                        week_total += duration_hours
                    else:
                        duration_hours = 'Ongoing'
                    
                    html_parts.append(f"<tr><td>{date}</td><td>{clock_in}</td><td>{clock_out}</td><td>{duration_hours}</td></tr>")
                
                html_parts.append(f"<tr><td colspan='3'><strong>Week Total</strong></td><td><strong>{week_total:.2f}</strong></td></tr>")
                html_parts.append("</table><br>")
        
        return '\n'.join(html_parts)