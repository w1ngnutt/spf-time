import sendgrid
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition
import base64
from typing import List, Dict
import datetime
from .config import Config
from .database import TimeRecord

class EmailService:
    def __init__(self, config: Config):
        self.config = config
        
    def get_week_start(self, date: datetime.date) -> datetime.date:
        """Get the start of the work week containing the given date based on payroll config"""
        # Get the configured work week start day (0=Monday, 1=Tuesday, ..., 6=Sunday)
        work_week_start_day = self.config.payroll.start_day
        
        # Calculate days since the work week start day
        days_since_start = (date.weekday() - work_week_start_day) % 7
        return date - datetime.timedelta(days=days_since_start)
    
    def generate_weekly_table(self, records: List[TimeRecord], employees: Dict[int, str], week_start: datetime.date) -> str:
        """Generate HTML table for a single week"""
        week_end = week_start + datetime.timedelta(days=6)
        
        # Create date range for the work week (starts on configured payroll start day)
        date_list = []
        for i in range(7):
            date_list.append(week_start + datetime.timedelta(days=i))
        
        # Aggregate hours by employee and day for this week
        employee_hours = {}
        for record in records:
            if record.clock_out is None:
                continue  # Skip incomplete records
            
            record_date = record.clock_in.date()
            
            # Only include records from this week
            if not (week_start <= record_date <= week_end):
                continue
            
            employee_id = record.employee_id
            
            if employee_id not in employee_hours:
                employee_hours[employee_id] = {}
            
            if record_date not in employee_hours[employee_id]:
                employee_hours[employee_id][record_date] = 0.0
            
            duration = record.clock_out - record.clock_in
            hours = duration.total_seconds() / 3600
            employee_hours[employee_id][record_date] += hours
        
        # Generate HTML table
        html = f'<h4>Week of {week_start.strftime("%B %d, %Y")} - {week_end.strftime("%B %d, %Y")}</h4>\n'
        html += '<table border="1" cellpadding="5" cellspacing="0" style="border-collapse: collapse; font-family: Arial, sans-serif; margin-bottom: 20px;">\n'
        
        # Header row
        html += '  <tr style="background-color: #f0f0f0; font-weight: bold;">\n'
        html += '    <td>Employee</td>\n'
        
        # Day headers
        for date in date_list:
            day_name = date.strftime('%a')  # Mon, Tue, etc.
            date_str = date.strftime('%m/%d')
            html += f'    <td style="text-align: center;">{day_name}<br>{date_str}</td>\n'
        
        html += '    <td style="text-align: center; background-color: #e6f3ff;">Weekly Total</td>\n'
        html += '  </tr>\n'
        
        # Employee rows
        week_grand_total = 0.0
        for employee_id in sorted(employee_hours.keys(), key=lambda x: employees.get(x, 'Unknown')):
            employee_name = employees.get(employee_id, 'Unknown')
            html += f'  <tr>\n'
            html += f'    <td style="font-weight: bold;">{employee_name}</td>\n'
            
            employee_week_total = 0.0
            for date in date_list:
                hours = employee_hours.get(employee_id, {}).get(date, 0.0)
                if hours > 0:
                    html += f'    <td style="text-align: center;">{hours:.1f}</td>\n'
                else:
                    html += f'    <td style="text-align: center; color: #ccc;">-</td>\n'
                employee_week_total += hours
            
            html += f'    <td style="text-align: center; font-weight: bold; background-color: #e6f3ff;">{employee_week_total:.1f}</td>\n'
            html += '  </tr>\n'
            week_grand_total += employee_week_total
        
        # Daily totals row
        html += '  <tr style="background-color: #f0f0f0; font-weight: bold;">\n'
        html += '    <td>Daily Totals</td>\n'
        
        for date in date_list:
            daily_total = sum(employee_hours.get(emp_id, {}).get(date, 0.0) for emp_id in employee_hours.keys())
            html += f'    <td style="text-align: center;">{daily_total:.1f}</td>\n'
        
        html += f'    <td style="text-align: center; background-color: #d6e9ff;">{week_grand_total:.1f}</td>\n'
        html += '  </tr>\n'
        html += '</table>\n'
        
        return html
    
    def generate_hours_table(self, records: List[TimeRecord], employees: Dict[int, str], start_date: datetime.date, end_date: datetime.date) -> str:
        """Generate HTML tables showing hours worked by each employee per day, organized by week"""
        # Find all weeks in the date range
        weeks = []
        current_week_start = self.get_week_start(start_date)
        
        while current_week_start <= end_date:
            weeks.append(current_week_start)
            current_week_start += datetime.timedelta(weeks=1)
        
        # Generate a table for each week
        html_tables = []
        for week_start in weeks:
            weekly_table = self.generate_weekly_table(records, employees, week_start)
            html_tables.append(weekly_table)
        
        return '\n'.join(html_tables)
    
    def send_report_email(self, csv_data: str, date_range: str, records: List[TimeRecord] = None, employees: Dict[int, str] = None, start_date: datetime.date = None, end_date: datetime.date = None, html_tables: str = None) -> bool:
        try:
            sg = sendgrid.SendGridAPIClient(api_key=self.config.email.sendgrid_api_key)
            
            current_date = datetime.datetime.now().strftime('%m/%d/%Y')
            subject = self.config.email.subject_template.format(date_range=date_range) + f" - Generated {current_date}"
            
            # Use provided HTML tables or generate hours table
            hours_table = html_tables if html_tables else ""
            if not hours_table and records and employees and start_date and end_date:
                hours_table = self.generate_hours_table(records, employees, start_date, end_date)
            
            html_content = f"""
            <html>
            <body>
                <h2>Time Tracking Report</h2>
                <p><strong>Report Period:</strong> {date_range}</p>
                
                {f'<h3>Hours Summary:</h3>{hours_table}<br>' if hours_table else ''}
                
                <p>Please find the attached CSV file containing detailed time tracking records for all employees.</p>
                
                <h3>Report Summary:</h3>
                <ul>
                    <li>Generated on: {date_range}</li>
                    <li>Format: CSV (Comma Separated Values)</li>
                    <li>Contains: Employee names, dates, clock in/out times, and duration</li>
                </ul>
                
                <p>If you have any questions about this report, please contact the system administrator.</p>
                
                <hr>
                <p><em>This report was automatically generated by the Time Tracking System.</em></p>
            </body>
            </html>
            """
            
            plain_content = f"""
            Time Tracking Report
            
            Report Period: {date_range}
            
            Please find the attached CSV file containing detailed time tracking records for all employees.
            
            Report Summary:
            - Generated on: {date_range}
            - Format: CSV (Comma Separated Values)
            - Contains: Employee names, dates, clock in/out times, and duration
            
            If you have any questions about this report, please contact the system administrator.
            
            This report was automatically generated by the Time Tracking System.
            """
            
            # Create the email
            message = Mail(
                from_email=(self.config.email.from_email, self.config.email.from_name),
                to_emails=self.config.email.report_recipients,
                subject=subject,
                html_content=html_content,
                plain_text_content=plain_content
            )
            
            # Add CSV attachment
            csv_attachment = Attachment(
                FileContent(base64.b64encode(csv_data.encode()).decode()),
                FileName(f'time_report_{date_range.replace("/", "-").replace(" - ", "_to_")}.csv'),
                FileType('text/csv'),
                Disposition('attachment')
            )
            message.attachment = csv_attachment
            
            # Send the email
            response = sg.send(message)
            
            return response.status_code == 202
            
        except Exception as e:
            print(f"Error sending email: {str(e)}")
            return False
    
    def test_email_configuration(self) -> bool:
        """Test if email configuration is valid"""
        try:
            if not self.config.email.sendgrid_api_key or self.config.email.sendgrid_api_key == "your_sendgrid_api_key_here":
                return False
            
            if not self.config.email.report_recipients:
                return False
            
            # Test API key validity (this would require a test email)
            sg = sendgrid.SendGridAPIClient(api_key=self.config.email.sendgrid_api_key)
            
            return True
            
        except Exception:
            return False