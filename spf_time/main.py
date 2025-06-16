from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from kivy.uix.popup import Popup
import threading
import datetime
from typing import Dict

from .database import DatabaseManager
from .config import Config
from .admin_ui import PinEntryDialog, AdminUI

class EmployeeRow(BoxLayout):
    def __init__(self, employee, database_manager, config, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = '48dp'
        self.spacing = '10dp'
        self.padding = ['10dp', '5dp']
        
        self.employee = employee
        self.db_manager = database_manager
        self.config = config
        
        self.name_label = Label(
            text=employee.name,
            size_hint_x = 0.6,
            text_size=(None, None),
            halign='left',
            valign='middle'
        )
        
        self.status_label = Label(
            text='Clocked Out',
            size_hint_x = 0.2,
            text_size=(None, None),
            halign='center',
            valign='middle'
        )
        
        self.clock_button = Button(
            text='Clock In',
            size_hint_x = 0.2,
            background_color=config.ui.clock_in_color
        )
        self.clock_button.bind(on_press=self.toggle_clock)
        
        self.add_widget(self.name_label)
        self.add_widget(self.status_label)
        self.add_widget(self.clock_button)
        
        self.update_status()
    
    def update_status(self):
        is_clocked_in = self.db_manager.is_clocked_in(self.employee.id)
        
        if is_clocked_in:
            self.status_label.text = 'Clocked In'
            self.clock_button.text = 'Clock Out'
            self.clock_button.background_color = self.config.ui.clock_out_color
            
            current_session = self.db_manager.get_current_session(self.employee.id)
            if current_session:
                duration = datetime.datetime.now() - current_session.clock_in
                hours, remainder = divmod(duration.total_seconds(), 3600)
                minutes, _ = divmod(remainder, 60)
                self.status_label.text = f'Clocked In ({int(hours):02d}:{int(minutes):02d})'
        else:
            self.status_label.text = 'Clocked Out'
            self.clock_button.text = 'Clock In'
            self.clock_button.background_color = self.config.ui.clock_in_color
    
    def toggle_clock(self, instance):
        if self.db_manager.is_clocked_in(self.employee.id):
            self.clock_out()
        else:
            self.clock_in()
        
        self.update_status()
    
    def clock_in(self):
        try:
            record_id = self.db_manager.clock_in(self.employee.id)
            print(f"{self.employee.name} clocked in at {datetime.datetime.now().strftime('%H:%M:%S')}")
        except Exception as e:
            self.show_error_popup(f"Failed to clock in: {str(e)}")
    
    def clock_out(self):
        try:
            success = self.db_manager.clock_out(self.employee.id)
            if success:
                print(f"{self.employee.name} clocked out at {datetime.datetime.now().strftime('%H:%M:%S')}")
            else:
                self.show_error_popup("No active clock-in session found")
        except Exception as e:
            self.show_error_popup(f"Failed to clock out: {str(e)}")
    
    def show_error_popup(self, message):
        popup = Popup(
            title='Error',
            content=Label(text=message),
            size_hint=(0.6, 0.4)
        )
        popup.open()

class TimeTrackingApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.config_manager = Config()
        self.db_manager = DatabaseManager(self.config_manager.database.db_path)
        self.employee_rows = {}
        
        self.title = self.config_manager.ui.window_title
    
    def build(self):
        main_layout = BoxLayout(orientation='vertical', padding='10dp', spacing='10dp')
        
        header = Label(
            text=self.config_manager.ui.window_title,
            size_hint_y=None,
            height='50dp',
            font_size='20sp'
        )
        main_layout.add_widget(header)
        
        scroll_view = ScrollView()
        self.employee_grid = GridLayout(
            cols=1,
            size_hint_y=None,
            spacing='5dp'
        )
        self.employee_grid.bind(minimum_height=self.employee_grid.setter('height'))
        
        scroll_view.add_widget(self.employee_grid)
        main_layout.add_widget(scroll_view)
        
        # Admin settings button at bottom
        admin_btn = Button(
            text='Admin Settings',
            size_hint_y=None,
            height='50dp',
            background_color=[0.6, 0.6, 0.6, 1]
        )
        admin_btn.bind(on_press=self.show_admin_login)
        main_layout.add_widget(admin_btn)
        
        self.load_employees()
        
        Clock.schedule_interval(self.update_employee_statuses, 60)
        
        Clock.schedule_interval(self.auto_clock_out_check, 3600)
        
        return main_layout
    
    def load_employees(self):
        employees = self.db_manager.get_employees()
        
        configured_names = set(self.config_manager.get_employee_names())
        existing_names = set(emp.name for emp in employees)
        
        for name in configured_names - existing_names:
            self.db_manager.add_employee(name)
        
        employees = self.db_manager.get_employees()
        
        for employee in employees:
            if employee.name in configured_names:
                employee_row = EmployeeRow(
                    employee, 
                    self.db_manager, 
                    self.config_manager
                )
                self.employee_rows[employee.id] = employee_row
                self.employee_grid.add_widget(employee_row)
    
    def update_employee_statuses(self, dt):
        for employee_row in self.employee_rows.values():
            employee_row.update_status()
    
    def auto_clock_out_check(self, dt):
        def run_auto_clock_out():
            count = self.db_manager.auto_clock_out_expired_sessions(
                self.config_manager.time_tracking.auto_clock_out_hours
            )
            if count > 0:
                print(f"Auto-clocked out {count} expired sessions")
        
        threading.Thread(target=run_auto_clock_out, daemon=True).start()
    
    def show_admin_login(self, instance):
        pin_dialog = PinEntryDialog(
            config=self.config_manager,
            on_success_callback=self.show_admin_ui
        )
        pin_dialog.open()
    
    def show_admin_ui(self):
        admin_popup = Popup(
            title='Admin Panel',
            size_hint=(0.95, 0.95)
        )
        
        admin_ui = AdminUI(
            db_manager=self.db_manager,
            config=self.config_manager
        )
        
        # Add close button
        main_layout = BoxLayout(orientation='vertical')
        main_layout.add_widget(admin_ui)
        
        close_btn = Button(
            text='Close Admin Panel',
            size_hint_y=None,
            height='50dp',
            background_color=[0.8, 0.2, 0.2, 1]
        )
        close_btn.bind(on_press=admin_popup.dismiss)
        main_layout.add_widget(close_btn)
        
        admin_popup.content = main_layout
        admin_popup.open()

def main():
    app = TimeTrackingApp()
    app.run()

if __name__ == '__main__':
    main()