from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.clock import Clock
import datetime
from typing import List, Optional
import csv
import io

from .database import DatabaseManager, TimeRecord
from .config import Config
from .email_service import EmailService
from .time_picker import QuickTimePickerDialog, DateTimePickerDialog

class NumericKeypad(GridLayout):
    def __init__(self, on_digit_press, on_clear, on_enter, **kwargs):
        super().__init__(**kwargs)
        self.cols = 3
        self.spacing = '10dp'
        self.size_hint = (None, None)
        self.width = '300dp'
        self.height = '400dp'
        
        self.on_digit_press = on_digit_press
        self.on_clear = on_clear
        self.on_enter = on_enter
        
        # Number buttons 1-9
        for i in range(1, 10):
            btn = Button(
                text=str(i),
                font_size='24sp',
                size_hint_y=None,
                height='80dp'
            )
            btn.bind(on_press=lambda x, digit=i: self.on_digit_press(str(digit)))
            self.add_widget(btn)
        
        # Bottom row: Clear, 0, Enter
        clear_btn = Button(
            text='Clear',
            font_size='20sp',
            size_hint_y=None,
            height='80dp',
            background_color=[1, 0.5, 0.5, 1]
        )
        clear_btn.bind(on_press=lambda x: self.on_clear())
        self.add_widget(clear_btn)
        
        zero_btn = Button(
            text='0',
            font_size='24sp',
            size_hint_y=None,
            height='80dp'
        )
        zero_btn.bind(on_press=lambda x: self.on_digit_press('0'))
        self.add_widget(zero_btn)
        
        enter_btn = Button(
            text='Enter',
            font_size='20sp',
            size_hint_y=None,
            height='80dp',
            background_color=[0.5, 1, 0.5, 1]
        )
        enter_btn.bind(on_press=lambda x: self.on_enter())
        self.add_widget(enter_btn)

class PinEntryDialog(Popup):
    def __init__(self, config: Config, on_success_callback, **kwargs):
        super().__init__(**kwargs)
        self.config = config
        self.on_success_callback = on_success_callback
        self.entered_pin = ""
        
        self.title = "Admin Access - Enter PIN"
        self.size_hint = (0.6, 0.8)
        self.auto_dismiss = False
        
        main_layout = BoxLayout(orientation='vertical', spacing='20dp', padding='20dp')
        
        # PIN display
        self.pin_display = Label(
            text='Enter 4-digit PIN: ****',
            font_size='20sp',
            size_hint_y=None,
            height='50dp'
        )
        main_layout.add_widget(self.pin_display)
        
        # Keypad
        keypad = NumericKeypad(
            on_digit_press=self.on_digit_press,
            on_clear=self.on_clear_press,
            on_enter=self.on_enter_press
        )
        main_layout.add_widget(keypad)
        
        # Cancel button
        cancel_btn = Button(
            text='Cancel',
            size_hint_y=None,
            height='50dp',
            background_color=[0.8, 0.2, 0.2, 1]
        )
        cancel_btn.bind(on_press=self.dismiss)
        main_layout.add_widget(cancel_btn)
        
        self.content = main_layout
    
    def on_digit_press(self, digit):
        if len(self.entered_pin) < 4:
            self.entered_pin += digit
            self.update_display()
            
            if len(self.entered_pin) == 4:
                Clock.schedule_once(lambda dt: self.verify_pin(), 0.5)
    
    def on_clear_press(self):
        self.entered_pin = ""
        self.update_display()
    
    def on_enter_press(self):
        if len(self.entered_pin) == 4:
            self.verify_pin()
    
    def update_display(self):
        display_text = 'Enter 4-digit PIN: ' + '*' * len(self.entered_pin) + '_' * (4 - len(self.entered_pin))
        self.pin_display.text = display_text
    
    def verify_pin(self):
        if self.entered_pin == self.config.admin.pin:
            self.dismiss()
            self.on_success_callback()
        else:
            self.show_error()
            self.entered_pin = ""
            self.update_display()
    
    def show_error(self):
        error_popup = Popup(
            title='Access Denied',
            content=Label(text='Incorrect PIN. Please try again.'),
            size_hint=(0.4, 0.3)
        )
        error_popup.open() 
        Clock.schedule_once(lambda dt: error_popup.dismiss(), 2)

class TimeRecordRow(BoxLayout):
    def __init__(self, record: TimeRecord, employee_name: str, on_edit_callback, on_delete_callback, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = '50dp'
        self.spacing = '10dp'
        self.padding = ['5dp', '2dp']
        
        self.record = record
        self.employee_name = employee_name
        self.on_edit_callback = on_edit_callback
        self.on_delete_callback = on_delete_callback
        
        # Employee name
        name_label = Label(
            text=employee_name,
            size_hint_x=0.2,
            text_size=(None, None),
            halign='left',
            valign='middle'
        )
        
        # Clock in time
        clock_in_text = record.clock_in.strftime('%m/%d %H:%M')
        clock_in_label = Label(
            text=clock_in_text,
            size_hint_x=0.2,
            text_size=(None, None),
            halign='center',
            valign='middle'
        )
        
        # Clock out time
        clock_out_text = record.clock_out.strftime('%m/%d %H:%M') if record.clock_out else 'Still In'
        clock_out_label = Label(
            text=clock_out_text,
            size_hint_x=0.2,
            text_size=(None, None),
            halign='center',
            valign='middle'
        )
        
        # Duration
        if record.clock_out:
            duration = record.clock_out - record.clock_in
            hours, remainder = divmod(duration.total_seconds(), 3600)
            minutes, _ = divmod(remainder, 60)
            duration_text = f'{int(hours):02d}:{int(minutes):02d}'
        else:
            duration = datetime.datetime.now() - record.clock_in
            hours, remainder = divmod(duration.total_seconds(), 3600)
            minutes, _ = divmod(remainder, 60)
            duration_text = f'{int(hours):02d}:{int(minutes):02d}*'
        
        duration_label = Label(
            text=duration_text,
            size_hint_x=0.15,
            text_size=(None, None),
            halign='center',
            valign='middle'
        )
        
        # Edit button
        edit_btn = Button(
            text='Edit',
            size_hint_x=0.15,
            background_color=[0.3, 0.6, 1, 1]
        )
        edit_btn.bind(on_press=lambda x: self.on_edit_callback(self.record, self.employee_name))
        
        # Delete button
        delete_btn = Button(
            text='Delete',
            size_hint_x=0.1,
            background_color=[1, 0.3, 0.3, 1]
        )
        delete_btn.bind(on_press=lambda x: self.confirm_delete())
        
        self.add_widget(name_label)
        self.add_widget(clock_in_label)
        self.add_widget(clock_out_label)
        self.add_widget(duration_label)
        self.add_widget(edit_btn)
        self.add_widget(delete_btn)
    
    def confirm_delete(self):
        popup = Popup(
            title='Confirm Delete',
            size_hint=(0.6, 0.4)
        )
        
        content = BoxLayout(orientation='vertical', spacing='10dp')
        content.add_widget(Label(text=f'Delete time record for {self.employee_name}?'))
        
        button_layout = BoxLayout(orientation='horizontal', spacing='10dp', size_hint_y=None, height='50dp')
        
        yes_btn = Button(text='Yes', background_color=[1, 0.3, 0.3, 1])
        yes_btn.bind(on_press=lambda x: self.delete_record(popup))
        
        no_btn = Button(text='No', background_color=[0.3, 1, 0.3, 1])
        no_btn.bind(on_press=popup.dismiss)
        
        button_layout.add_widget(yes_btn)
        button_layout.add_widget(no_btn)
        content.add_widget(button_layout)
        
        popup.content = content
        popup.open()
    
    def delete_record(self, popup):
        popup.dismiss()
        self.on_delete_callback(self.record)

class TimeEditDialog(Popup):
    def __init__(self, record: TimeRecord, employee_name: str, on_save_callback, **kwargs):
        super().__init__(**kwargs)
        self.record = record
        self.employee_name = employee_name
        self.on_save_callback = on_save_callback
        
        # Make a copy of the record to edit
        self.working_record = TimeRecord(
            id=record.id,
            employee_id=record.employee_id,
            clock_in=record.clock_in,
            clock_out=record.clock_out,
            created_at=record.created_at
        )
        
        self.title = f'Edit Time Record - {employee_name}'
        self.size_hint = (0.8, 0.7)
        self.auto_dismiss = False
        
        main_layout = BoxLayout(orientation='vertical', spacing='15dp', padding='20dp')
        
        # Clock In section
        clock_in_section = BoxLayout(orientation='vertical', spacing='5dp', size_hint_y=None, height='100dp')
        clock_in_section.add_widget(Label(text='Clock In Time:', size_hint_y=None, height='25dp', font_size='16sp', bold=True))
        
        clock_in_display_layout = BoxLayout(orientation='horizontal', spacing='10dp', size_hint_y=None, height='50dp')
        
        self.clock_in_display = Label(
            text=self.working_record.clock_in.strftime('%Y-%m-%d %H:%M'),
            size_hint_x=0.7,
            font_size='14sp'
        )
        
        edit_in_btn = Button(
            text='Edit Clock In',
            size_hint_x=0.3,
            background_color=[0.3, 0.6, 1, 1]
        )
        edit_in_btn.bind(on_press=lambda x: self.edit_clock_in())
        
        clock_in_display_layout.add_widget(self.clock_in_display)
        clock_in_display_layout.add_widget(edit_in_btn)
        clock_in_section.add_widget(clock_in_display_layout)
        main_layout.add_widget(clock_in_section)
        
        # Clock Out section
        clock_out_section = BoxLayout(orientation='vertical', spacing='5dp', size_hint_y=None, height='100dp')
        clock_out_section.add_widget(Label(text='Clock Out Time:', size_hint_y=None, height='25dp', font_size='16sp', bold=True))
        
        clock_out_display_layout = BoxLayout(orientation='horizontal', spacing='10dp', size_hint_y=None, height='50dp')
        
        clock_out_text = self.working_record.clock_out.strftime('%Y-%m-%d %H:%M') if self.working_record.clock_out else 'Not clocked out'
        self.clock_out_display = Label(
            text=clock_out_text,
            size_hint_x=0.7,
            font_size='14sp'
        )
        
        edit_out_btn = Button(
            text='Edit Clock Out',
            size_hint_x=0.3,
            background_color=[0.3, 0.6, 1, 1]
        )
        edit_out_btn.bind(on_press=lambda x: self.edit_clock_out())
        
        clock_out_display_layout.add_widget(self.clock_out_display)
        clock_out_display_layout.add_widget(edit_out_btn)
        clock_out_section.add_widget(clock_out_display_layout)
        main_layout.add_widget(clock_out_section)
        
        # Duration display
        self.duration_label = Label(
            text=self.calculate_duration_text(),
            size_hint_y=None,
            height='30dp',
            font_size='14sp'
        )
        main_layout.add_widget(self.duration_label)
        
        # Action buttons
        button_layout = BoxLayout(orientation='horizontal', spacing='10dp', size_hint_y=None, height='50dp')
        
        save_btn = Button(text='Save Changes', background_color=[0.3, 1, 0.3, 1], font_size='16sp')
        save_btn.bind(on_press=self.save_changes)
        
        cancel_btn = Button(text='Cancel', background_color=[1, 0.3, 0.3, 1], font_size='16sp')
        cancel_btn.bind(on_press=self.dismiss)
        
        button_layout.add_widget(save_btn)
        button_layout.add_widget(cancel_btn)
        main_layout.add_widget(button_layout)
        
        self.content = main_layout
    
    def edit_clock_in(self):
        time_picker = QuickTimePickerDialog(
            current_time=self.working_record.clock_in,
            time_type='clock_in',
            on_save_callback=self.update_clock_in
        )
        time_picker.open()
    
    def edit_clock_out(self):
        current_time = self.working_record.clock_out or datetime.datetime.now()
        time_picker = QuickTimePickerDialog(
            current_time=current_time,
            time_type='clock_out',
            on_save_callback=self.update_clock_out
        )
        time_picker.open()
    
    def update_clock_in(self, new_time: datetime.datetime):
        self.working_record.clock_in = new_time
        self.clock_in_display.text = new_time.strftime('%Y-%m-%d %H:%M')
        self.duration_label.text = self.calculate_duration_text()
    
    def update_clock_out(self, new_time: datetime.datetime):
        self.working_record.clock_out = new_time
        self.clock_out_display.text = new_time.strftime('%Y-%m-%d %H:%M')
        self.duration_label.text = self.calculate_duration_text()
    
    def calculate_duration_text(self) -> str:
        if self.working_record.clock_out:
            duration = self.working_record.clock_out - self.working_record.clock_in
            if duration.total_seconds() < 0:
                return "Duration: Invalid (Clock out before clock in)"
            hours, remainder = divmod(duration.total_seconds(), 3600)
            minutes, _ = divmod(remainder, 60)
            return f"Duration: {int(hours):02d}:{int(minutes):02d}"
        else:
            return "Duration: Not clocked out"
    
    def save_changes(self, instance):
        # Validate the times
        if self.working_record.clock_out and self.working_record.clock_out <= self.working_record.clock_in:
            error_popup = Popup(
                title='Invalid Time',
                content=Label(text='Clock out time must be after clock in time.'),
                size_hint=(0.6, 0.4)
            )
            error_popup.open()
            Clock.schedule_once(lambda dt: error_popup.dismiss(), 3)
            return
        
        # Update the original record
        self.record.clock_in = self.working_record.clock_in
        self.record.clock_out = self.working_record.clock_out
        
        # Call the save callback
        self.on_save_callback(self.record)
        self.dismiss()

class AdminUI(BoxLayout):
    def __init__(self, db_manager: DatabaseManager, config: Config, **kwargs):
        super().__init__(**kwargs)
        self.db_manager = db_manager
        self.config = config
        self.email_service = EmailService(config)
        
        self.orientation = 'vertical'
        self.spacing = '10dp'
        self.padding = '10dp'
        
        self.setup_ui()
        self.load_time_records()
    
    def setup_ui(self):
        # Header
        header_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height='50dp', spacing='10dp')
        
        title_label = Label(
            text='Admin Panel - Time Records (Last 2 Weeks)',
            font_size='18sp',
            size_hint_x=0.7
        )
        
        refresh_btn = Button(
            text='Refresh',
            size_hint_x=0.15,
            background_color=[0.3, 0.8, 0.3, 1]
        )
        refresh_btn.bind(on_press=lambda x: self.load_time_records())
        
        email_btn = Button(
            text='Send Report',
            size_hint_x=0.15,
            background_color=[0.8, 0.6, 0.2, 1]
        )
        email_btn.bind(on_press=lambda x: self.send_email_report())
        
        header_layout.add_widget(title_label)
        header_layout.add_widget(refresh_btn)
        header_layout.add_widget(email_btn)
        self.add_widget(header_layout)
        
        # Column headers
        headers_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height='40dp', spacing='10dp')
        headers = ['Employee', 'Clock In', 'Clock Out', 'Duration', 'Edit', 'Del']
        sizes = [0.2, 0.2, 0.2, 0.15, 0.15, 0.1]
        
        for header, size in zip(headers, sizes):
            label = Label(
                text=header,
                size_hint_x=size,
                font_size='14sp',
                bold=True
            )
            headers_layout.add_widget(label)
        
        self.add_widget(headers_layout)
        
        # Scrollable records list
        scroll_view = ScrollView()
        self.records_layout = GridLayout(
            cols=1,
            size_hint_y=None,
            spacing='2dp'
        )
        self.records_layout.bind(minimum_height=self.records_layout.setter('height'))
        
        scroll_view.add_widget(self.records_layout)
        self.add_widget(scroll_view)
    
    def load_time_records(self):
        self.records_layout.clear_widgets()
        
        # Get records from last 2 weeks
        end_date = datetime.date.today()
        start_date = end_date - datetime.timedelta(days=14)
        
        records = self.db_manager.get_time_records(
            start_date=start_date,
            end_date=end_date
        )
        
        # Get employee names
        employees = {emp.id: emp.name for emp in self.db_manager.get_employees(active_only=False)}
        
        for record in records:
            employee_name = employees.get(record.employee_id, 'Unknown')
            record_row = TimeRecordRow(
                record=record,
                employee_name=employee_name,
                on_edit_callback=self.edit_record,
                on_delete_callback=self.delete_record
            )
            self.records_layout.add_widget(record_row)
    
    def edit_record(self, record: TimeRecord, employee_name: str):
        edit_dialog = TimeEditDialog(
            record=record,
            employee_name=employee_name,
            on_save_callback=self.save_record_changes
        )
        edit_dialog.open()
    
    def save_record_changes(self, record: TimeRecord):
        try:
            success = self.db_manager.update_time_record(
                record_id=record.id,
                clock_in=record.clock_in,
                clock_out=record.clock_out
            )
            
            if success:
                self.show_message("Time record updated successfully!")
                self.load_time_records()  # Refresh the list
            else:
                self.show_message("Failed to update time record.")
                
        except Exception as e:
            self.show_message(f"Error updating record: {str(e)}")
    
    def delete_record(self, record: TimeRecord):
        try:
            success = self.db_manager.delete_time_record(record.id)
            
            if success:
                self.show_message("Time record deleted successfully!")
                self.load_time_records()  # Refresh the list
            else:
                self.show_message("Failed to delete time record.")
                
        except Exception as e:
            self.show_message(f"Error deleting record: {str(e)}")
    
    def send_email_report(self):
        if not self.config.email.enable_email_reports:
            self.show_message("Email reports are disabled in settings")
            return
        
        if not self.config.email.sendgrid_api_key or self.config.email.sendgrid_api_key == "your_sendgrid_api_key_here":
            self.show_message("SendGrid API key not configured")
            return
        
        try:
            # Generate report data
            end_date = datetime.date.today()
            start_date = end_date - datetime.timedelta(days=14)
            
            records = self.db_manager.get_time_records(
                start_date=start_date,
                end_date=end_date
            )
            
            employees = {emp.id: emp.name for emp in self.db_manager.get_employees(active_only=False)}
            
            # Create CSV report
            csv_data = self.generate_csv_report(records, employees)
            
            # Send email
            date_range = f"{start_date.strftime('%m/%d/%Y')} - {end_date.strftime('%m/%d/%Y')}"
            success = self.email_service.send_report_email(csv_data, date_range, records, employees, start_date, end_date)
            
            if success:
                self.show_message("Report sent successfully!")
            else:
                self.show_message("Failed to send report. Check email configuration.")
                
        except Exception as e:
            self.show_message(f"Error sending report: {str(e)}")
    
    def generate_csv_report(self, records: List[TimeRecord], employees: dict) -> str:
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
    
    def show_message(self, message: str):
        popup = Popup(
            title='Information',
            content=Label(text=message),
            size_hint=(0.6, 0.4)
        )
        popup.open()
        Clock.schedule_once(lambda dt: popup.dismiss(), 3)