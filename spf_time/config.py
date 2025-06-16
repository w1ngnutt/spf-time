import toml
import os
from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class PayrollConfig:
    start_day: int = 1

@dataclass 
class TimeTrackingConfig:
    auto_clock_out_hours: int = 12
    min_break_time_minutes: int = 1
    grace_period_minutes: int = 5

@dataclass
class EmployeeConfig:
    names: List[str] = None

@dataclass
class DatabaseConfig:
    db_path: str = "time_tracking.db"

@dataclass
class UIConfig:
    window_title: str = "Employee Time Tracking"
    window_width: int = 800
    window_height: int = 600
    clock_in_color: List[float] = None
    clock_out_color: List[float] = None
    disabled_color: List[float] = None

@dataclass
class ReportsConfig:
    default_date_range_days: int = 14
    export_formats: List[str] = None

@dataclass
class NotificationsConfig:
    enable_break_reminders: bool = True
    break_reminder_hours: int = 4
    enable_overtime_alerts: bool = True
    overtime_threshold_hours: int = 8

@dataclass
class SecurityConfig:
    require_admin_for_employee_management: bool = False
    session_timeout_minutes: int = 60

@dataclass
class AdminConfig:
    pin: str = "1234"

@dataclass
class EmailConfig:
    sendgrid_api_key: str = ""
    from_email: str = "noreply@company.com"
    from_name: str = "Time Tracking System"
    report_recipients: List[str] = None
    subject_template: str = "Time Tracking Report - {date_range}"
    enable_email_reports: bool = True

class Config:
    def __init__(self, config_path: str = "settings.toml"):
        self.config_path = config_path
        self._load_config()
    
    def _load_config(self):
        if not os.path.exists(self.config_path):
            self._create_default_config()
        
        with open(self.config_path, 'r') as f:
            config_data = toml.load(f)
        
        self.payroll = PayrollConfig(**config_data.get('payroll', {}))
        self.time_tracking = TimeTrackingConfig(**config_data.get('time_tracking', {}))
        
        employee_data = config_data.get('employees', {})
        self.employees = EmployeeConfig(
            names=employee_data.get('names', [])
        )
        
        self.database = DatabaseConfig(**config_data.get('database', {}))
        
        ui_data = config_data.get('ui', {})
        self.ui = UIConfig(
            window_title=ui_data.get('window_title', 'Employee Time Tracking'),
            window_width=ui_data.get('window_width', 800),
            window_height=ui_data.get('window_height', 600),
            clock_in_color=ui_data.get('clock_in_color', [0.2, 0.8, 0.2, 1]),
            clock_out_color=ui_data.get('clock_out_color', [0.8, 0.2, 0.2, 1]),
            disabled_color=ui_data.get('disabled_color', [0.5, 0.5, 0.5, 1])
        )
        
        reports_data = config_data.get('reports', {})
        self.reports = ReportsConfig(
            default_date_range_days=reports_data.get('default_date_range_days', 14),
            export_formats=reports_data.get('export_formats', ['csv'])
        )
        
        self.notifications = NotificationsConfig(**config_data.get('notifications', {}))
        self.security = SecurityConfig(**config_data.get('security', {}))
        self.admin = AdminConfig(**config_data.get('admin', {}))
        
        email_data = config_data.get('email', {})
        self.email = EmailConfig(
            sendgrid_api_key=email_data.get('sendgrid_api_key', ''),
            from_email=email_data.get('from_email', 'noreply@company.com'),
            from_name=email_data.get('from_name', 'Time Tracking System'),
            report_recipients=email_data.get('report_recipients', []),
            subject_template=email_data.get('subject_template', 'Time Tracking Report - {date_range}'),
            enable_email_reports=email_data.get('enable_email_reports', True)
        )
    
    def _create_default_config(self):
        default_config = {
            'payroll': {'start_day': 1},
            'time_tracking': {
                'auto_clock_out_hours': 12,
                'min_break_time_minutes': 1,
                'grace_period_minutes': 5
            },
            'employees': {
                'names': ['John Smith', 'Jane Doe', 'Bob Johnson']
            },
            'database': {'db_path': 'time_tracking.db'},
            'ui': {
                'window_title': 'Employee Time Tracking',
                'window_width': 800,
                'window_height': 600,
                'clock_in_color': [0.2, 0.8, 0.2, 1],
                'clock_out_color': [0.8, 0.2, 0.2, 1],
                'disabled_color': [0.5, 0.5, 0.5, 1]
            },
            'reports': {
                'default_date_range_days': 14,
                'export_formats': ['csv']
            },
            'notifications': {
                'enable_break_reminders': True,
                'break_reminder_hours': 4,
                'enable_overtime_alerts': True,
                'overtime_threshold_hours': 8
            },
            'security': {
                'require_admin_for_employee_management': False,
                'session_timeout_minutes': 60
            }
        }
        
        with open(self.config_path, 'w') as f:
            toml.dump(default_config, f)
    
    def reload(self):
        self._load_config()
    
    def get_employee_names(self) -> List[str]:
        return self.employees.names or []