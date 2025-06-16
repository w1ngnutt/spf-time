import datetime
from typing import List, Optional, Tuple
from .database import DatabaseManager, TimeRecord
from .config import Config

class TimeTrackingRules:
    def __init__(self, db_manager: DatabaseManager, config: Config):
        self.db_manager = db_manager
        self.config = config
    
    def can_clock_in(self, employee_id: int) -> Tuple[bool, str]:
        if self.db_manager.is_clocked_in(employee_id):
            return False, "Employee is already clocked in"
        
        last_clock_out = self._get_last_clock_out(employee_id)
        if last_clock_out:
            time_since_last = datetime.datetime.now() - last_clock_out
            min_break_minutes = self.config.time_tracking.min_break_time_minutes
            
            if time_since_last.total_seconds() < (min_break_minutes * 60):
                return False, f"Must wait {min_break_minutes} minutes between clock in/out"
        
        return True, "OK"
    
    def can_clock_out(self, employee_id: int) -> Tuple[bool, str]:
        if not self.db_manager.is_clocked_in(employee_id):
            return False, "Employee is not clocked in"
        
        current_session = self.db_manager.get_current_session(employee_id) 
        if current_session:
            time_worked = datetime.datetime.now() - current_session.clock_in
            min_break_minutes = self.config.time_tracking.min_break_time_minutes
            
            if time_worked.total_seconds() < (min_break_minutes * 60):
                return False, f"Must work at least {min_break_minutes} minutes before clocking out"
        
        return True, "OK"
    
    def _get_last_clock_out(self, employee_id: int) -> Optional[datetime.datetime]:
        records = self.db_manager.get_time_records(employee_id=employee_id)
        for record in records:
            if record.clock_out:
                return record.clock_out
        return None
    
    def calculate_daily_hours(self, employee_id: int, date: datetime.date) -> float:
        start_of_day = datetime.datetime.combine(date, datetime.time.min)
        end_of_day = datetime.datetime.combine(date, datetime.time.max)
        
        records = self.db_manager.get_time_records(
            employee_id=employee_id,
            start_date=date,
            end_date=date
        )
        
        total_hours = 0.0
        for record in records:
            if record.clock_in >= start_of_day and record.clock_in <= end_of_day:
                end_time = record.clock_out or datetime.datetime.now()
                if end_time > end_of_day:
                    end_time = end_of_day
                
                duration = end_time - record.clock_in
                total_hours += duration.total_seconds() / 3600
        
        return total_hours
    
    def calculate_weekly_hours(self, employee_id: int, week_start: datetime.date) -> float:
        total_hours = 0.0
        for i in range(7):
            day = week_start + datetime.timedelta(days=i)
            total_hours += self.calculate_daily_hours(employee_id, day)
        return total_hours
    
    def is_overtime_approaching(self, employee_id: int, date: datetime.date) -> bool:
        daily_hours = self.calculate_daily_hours(employee_id, date)
        overtime_threshold = self.config.notifications.overtime_threshold_hours
        return daily_hours >= (overtime_threshold - 1)
    
    def needs_break_reminder(self, employee_id: int) -> bool:
        current_session = self.db_manager.get_current_session(employee_id)
        if not current_session:
            return False
        
        time_worked = datetime.datetime.now() - current_session.clock_in
        break_reminder_hours = self.config.notifications.break_reminder_hours
        
        return time_worked.total_seconds() >= (break_reminder_hours * 3600)
    
    def get_payroll_week_dates(self, date: datetime.date) -> Tuple[datetime.date, datetime.date]:
        start_day = self.config.payroll.start_day  # 0=Monday, 6=Sunday
        
        days_since_start = (date.weekday() - start_day) % 7
        week_start = date - datetime.timedelta(days=days_since_start)
        week_end = week_start + datetime.timedelta(days=6)
        
        return week_start, week_end
    
    def validate_time_entry(self, clock_in: datetime.datetime, 
                          clock_out: Optional[datetime.datetime] = None) -> Tuple[bool, str]:
        if clock_out and clock_out <= clock_in:
            return False, "Clock out time must be after clock in time"
        
        now = datetime.datetime.now()
        grace_period = datetime.timedelta(minutes=self.config.time_tracking.grace_period_minutes)
        
        if clock_in > now + grace_period:
            return False, "Clock in time cannot be in the future"
        
        if clock_out and clock_out > now + grace_period:
            return False, "Clock out time cannot be in the future"
        
        max_shift_hours = 24
        if clock_out:
            shift_duration = clock_out - clock_in
            if shift_duration.total_seconds() > (max_shift_hours * 3600):
                return False, f"Shift cannot exceed {max_shift_hours} hours"
        
        return True, "OK"

class ReportGenerator:
    def __init__(self, db_manager: DatabaseManager, rules: TimeTrackingRules):
        self.db_manager = db_manager
        self.rules = rules
    
    def generate_daily_report(self, employee_id: int, date: datetime.date) -> dict:
        records = self.db_manager.get_time_records(
            employee_id=employee_id,
            start_date=date,
            end_date=date
        )
        
        total_hours = self.rules.calculate_daily_hours(employee_id, date)
        
        return {
            'date': date.isoformat(),
            'total_hours': round(total_hours, 2),
            'records': len(records),
            'sessions': [
                {
                    'clock_in': record.clock_in.strftime('%H:%M:%S'),
                    'clock_out': record.clock_out.strftime('%H:%M:%S') if record.clock_out else 'Still clocked in',
                    'duration_hours': round((
                        (record.clock_out or datetime.datetime.now()) - record.clock_in
                    ).total_seconds() / 3600, 2)
                }
                for record in records
            ]
        }
    
    def generate_weekly_report(self, employee_id: int, week_start: datetime.date) -> dict:
        daily_reports = []
        total_weekly_hours = 0.0
        
        for i in range(7):
            day = week_start + datetime.timedelta(days=i)
            daily_report = self.generate_daily_report(employee_id, day)
            daily_reports.append(daily_report)
            total_weekly_hours += daily_report['total_hours']
        
        return {
            'week_start': week_start.isoformat(),
            'week_end': (week_start + datetime.timedelta(days=6)).isoformat(),
            'total_weekly_hours': round(total_weekly_hours, 2),
            'daily_reports': daily_reports
        }