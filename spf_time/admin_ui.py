from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.clock import Clock
import datetime
from typing import List, Optional, Tuple
import csv
import io

from .database import DatabaseManager, TimeRecord
from .config import Config
from .email_service import EmailService
from .time_picker import QuickTimePickerDialog, DateTimePickerDialog
from .report_generator import ReportGenerator

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
        
        # Touch debouncing - prevent rapid successive presses
        self.last_press_time = {}
        self.debounce_delay = 0.3  # 300ms between presses
        
        # Number buttons 1-9
        for i in range(1, 10):
            btn = Button(
                text=str(i),
                font_size='24sp',
                size_hint_y=None,
                height='80dp'
            )
            btn.bind(on_press=lambda x, digit=i: self.debounced_digit_press(str(digit)))
            self.add_widget(btn)
        
        # Bottom row: Clear, 0, Enter
        clear_btn = Button(
            text='Clear',
            font_size='20sp',
            size_hint_y=None,
            height='80dp',
            background_color=[1, 0.5, 0.5, 1]
        )
        clear_btn.bind(on_press=lambda x: self.debounced_clear())
        self.add_widget(clear_btn)
        
        zero_btn = Button(
            text='0',
            font_size='24sp',
            size_hint_y=None,
            height='80dp'
        )
        zero_btn.bind(on_press=lambda x: self.debounced_digit_press('0'))
        self.add_widget(zero_btn)
        
        enter_btn = Button(
            text='Enter',
            font_size='20sp',
            size_hint_y=None,
            height='80dp',
            background_color=[0.5, 1, 0.5, 1]
        )
        enter_btn.bind(on_press=lambda x: self.debounced_enter())
        self.add_widget(enter_btn)
    
    def debounced_digit_press(self, digit):
        """Prevent rapid successive digit presses"""
        import time
        current_time = time.time()
        
        if digit in self.last_press_time:
            if current_time - self.last_press_time[digit] < self.debounce_delay:
                return  # Ignore this press
        
        self.last_press_time[digit] = current_time
        self.on_digit_press(digit)
    
    def debounced_clear(self):
        """Prevent rapid successive clear presses"""
        import time
        current_time = time.time()
        
        if 'clear' in self.last_press_time:
            if current_time - self.last_press_time['clear'] < self.debounce_delay:
                return
        
        self.last_press_time['clear'] = current_time
        self.on_clear()
    
    def debounced_enter(self):
        """Prevent rapid successive enter presses"""
        import time
        current_time = time.time()
        
        if 'enter' in self.last_press_time:
            if current_time - self.last_press_time['enter'] < self.debounce_delay:
                return
        
        self.last_press_time['enter'] = current_time
        self.on_enter()

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

class TouchKeypad(BoxLayout):
    def __init__(self, on_input_callback, **kwargs):
        super().__init__(**kwargs)
        self.on_input_callback = on_input_callback
        self.orientation = 'vertical'
        self.spacing = '5dp'
        self.size_hint_y = None
        self.height = '300dp'
        
        # Display
        self.display = Label(
            text='8',
            font_size='24sp',
            size_hint_y=None,
            height='60dp'
        )
        self.add_widget(self.display)
        
        # Keypad grid
        keypad_grid = GridLayout(cols=3, spacing='5dp', size_hint_y=None, height='240dp')
        
        # Number buttons
        for i in range(1, 10):
            btn = Button(text=str(i), font_size='20sp')
            btn.bind(on_press=lambda x, num=i: self.add_digit(str(num)))
            keypad_grid.add_widget(btn)
        
        # Bottom row: Clear, 0, Decimal
        clear_btn = Button(text='C', font_size='20sp', background_color=[1, 0.3, 0.3, 1])
        clear_btn.bind(on_press=lambda x: self.clear())
        keypad_grid.add_widget(clear_btn)
        
        zero_btn = Button(text='0', font_size='20sp')
        zero_btn.bind(on_press=lambda x: self.add_digit('0'))
        keypad_grid.add_widget(zero_btn)
        
        decimal_btn = Button(text='.', font_size='20sp')
        decimal_btn.bind(on_press=lambda x: self.add_decimal())
        keypad_grid.add_widget(decimal_btn)
        
        self.add_widget(keypad_grid)
        
        self.current_value = '8.0'
    
    def add_digit(self, digit):
        if self.current_value == '8.0':
            self.current_value = digit
        else:
            self.current_value += digit
        self.display.text = self.current_value
        self.on_input_callback(self.current_value)
    
    def add_decimal(self):
        if '.' not in self.current_value:
            self.current_value += '.'
            self.display.text = self.current_value
            self.on_input_callback(self.current_value)
    
    def clear(self):
        self.current_value = '8.0'
        self.display.text = self.current_value
        self.on_input_callback(self.current_value)
    
    def get_value(self):
        return self.current_value

class TouchDatePicker(BoxLayout):
    def __init__(self, on_date_changed, **kwargs):
        super().__init__(**kwargs)
        self.on_date_changed = on_date_changed
        self.orientation = 'vertical'
        self.spacing = '10dp'
        self.size_hint_y = None
        self.height = '200dp'
        
        self.current_date = datetime.date.today()
        
        # Date display
        self.date_label = Label(
            text=self.current_date.strftime('%Y-%m-%d'),
            font_size='24sp',
            size_hint_y=None,
            height='60dp'
        )
        self.add_widget(self.date_label)
        
        # Navigation buttons
        nav_layout = BoxLayout(orientation='horizontal', spacing='10dp', size_hint_y=None, height='60dp')
        
        prev_day_btn = Button(text='- Day', font_size='16sp')
        prev_day_btn.bind(on_press=lambda x: self.change_date(-1))
        nav_layout.add_widget(prev_day_btn)
        
        prev_week_btn = Button(text='- Week', font_size='16sp')
        prev_week_btn.bind(on_press=lambda x: self.change_date(-7))
        nav_layout.add_widget(prev_week_btn)
        
        today_btn = Button(text='Today', font_size='16sp', background_color=[0.3, 0.8, 0.3, 1])
        today_btn.bind(on_press=lambda x: self.set_today())
        nav_layout.add_widget(today_btn)
        
        next_week_btn = Button(text='Week +', font_size='16sp')
        next_week_btn.bind(on_press=lambda x: self.change_date(7))
        nav_layout.add_widget(next_week_btn)
        
        next_day_btn = Button(text='Day +', font_size='16sp')
        next_day_btn.bind(on_press=lambda x: self.change_date(1))
        nav_layout.add_widget(next_day_btn)
        
        self.add_widget(nav_layout)
        
        # Month navigation
        month_layout = BoxLayout(orientation='horizontal', spacing='10dp', size_hint_y=None, height='60dp')
        
        prev_month_btn = Button(text='- Month', font_size='16sp')
        prev_month_btn.bind(on_press=lambda x: self.change_month(-1))
        month_layout.add_widget(prev_month_btn)
        
        next_month_btn = Button(text='Month +', font_size='16sp')
        next_month_btn.bind(on_press=lambda x: self.change_month(1))
        month_layout.add_widget(next_month_btn)
        
        self.add_widget(month_layout)
    
    def change_date(self, days):
        self.current_date += datetime.timedelta(days=days)
        self.update_display()
    
    def change_month(self, months):
        if months > 0:
            if self.current_date.month == 12:
                self.current_date = self.current_date.replace(year=self.current_date.year + 1, month=1)
            else:
                self.current_date = self.current_date.replace(month=self.current_date.month + 1)
        else:
            if self.current_date.month == 1:
                self.current_date = self.current_date.replace(year=self.current_date.year - 1, month=12)
            else:
                self.current_date = self.current_date.replace(month=self.current_date.month - 1)
        self.update_display()
    
    def set_today(self):
        self.current_date = datetime.date.today()
        self.update_display()
    
    def update_display(self):
        self.date_label.text = self.current_date.strftime('%Y-%m-%d')
        self.on_date_changed(self.current_date)
    
    def get_date(self):
        return self.current_date

class AddEntryDialog(Popup):
    def __init__(self, db_manager: 'DatabaseManager', config: 'Config', on_save_callback, **kwargs):
        super().__init__(**kwargs)
        self.db_manager = db_manager
        self.config = config
        self.on_save_callback = on_save_callback
        
        self.title = 'Add New Time Entry'
        self.size_hint = (0.9, 0.9)
        self.auto_dismiss = False
        
        main_layout = BoxLayout(orientation='vertical', spacing='15dp', padding='20dp')
        
        # Employee selection
        employee_section = BoxLayout(orientation='vertical', spacing='5dp', size_hint_y=None, height='100dp')
        employee_section.add_widget(Label(text='Employee:', size_hint_y=None, height='30dp', font_size='18sp', bold=True))
        
        # Get employee list from config only
        employee_names = self.config.employees.names
        
        self.employee_spinner = Spinner(
            text='Select Employee',
            values=employee_names,
            size_hint_y=None,
            height='60dp',
            font_size='18sp'
        )
        employee_section.add_widget(self.employee_spinner)
        main_layout.add_widget(employee_section)
        
        # Date selection with touch picker
        date_section = BoxLayout(orientation='vertical', spacing='5dp', size_hint_y=None, height='230dp')
        date_section.add_widget(Label(text='Date:', size_hint_y=None, height='30dp', font_size='18sp', bold=True))
        
        self.date_picker = TouchDatePicker(on_date_changed=self.on_date_changed)
        date_section.add_widget(self.date_picker)
        main_layout.add_widget(date_section)
        
        # Hours input with touch keypad
        hours_section = BoxLayout(orientation='vertical', spacing='5dp', size_hint_y=None, height='330dp')
        hours_section.add_widget(Label(text='Hours Worked:', size_hint_y=None, height='30dp', font_size='18sp', bold=True))
        
        self.hours_keypad = TouchKeypad(on_input_callback=self.on_hours_changed)
        hours_section.add_widget(self.hours_keypad)
        main_layout.add_widget(hours_section)
        
        # Action buttons
        button_layout = BoxLayout(orientation='horizontal', spacing='15dp', size_hint_y=None, height='70dp')
        
        save_btn = Button(text='Save Entry', background_color=[0.3, 1, 0.3, 1], font_size='20sp')
        save_btn.bind(on_press=self.save_entry)
        
        cancel_btn = Button(text='Cancel', background_color=[1, 0.3, 0.3, 1], font_size='20sp')
        cancel_btn.bind(on_press=self.dismiss)
        
        button_layout.add_widget(save_btn)
        button_layout.add_widget(cancel_btn)
        main_layout.add_widget(button_layout)
        
        self.content = main_layout
        
        # Initialize values
        self.selected_date = datetime.date.today()
        self.selected_hours = '8.0'
    
    def on_date_changed(self, new_date):
        self.selected_date = new_date
    
    def on_hours_changed(self, new_hours):
        self.selected_hours = new_hours
    
    def save_entry(self, instance):
        try:
            # Validate inputs
            if self.employee_spinner.text == 'Select Employee':
                self.show_error("Please select an employee")
                return
            
            if not self.selected_hours or self.selected_hours == '8.0':
                self.show_error("Please enter hours worked")
                return
            
            # Parse inputs
            employee_name = self.employee_spinner.text
            work_date = self.selected_date
            hours = float(self.selected_hours)
            
            # Get employee ID from database (create if doesn't exist)
            employee_id = self.get_or_create_employee_id(employee_name)
            
            if hours <= 0 or hours > 24:
                self.show_error("Hours must be between 0 and 24")
                return
            
            # Calculate clock in and clock out times
            # Default to 8 AM start time
            clock_in = datetime.datetime.combine(work_date, datetime.time(8, 0))
            clock_out = clock_in + datetime.timedelta(hours=hours)
            
            # Create time record using direct database insertion
            success = self._add_complete_time_record(employee_id, clock_in, clock_out)
            
            if success:
                self.show_success("Time entry added successfully!")
                self.on_save_callback()
                Clock.schedule_once(lambda dt: self.dismiss(), 1)
            else:
                self.show_error("Failed to add time entry")
                
        except ValueError as e:
            self.show_error(f"Invalid input: {str(e)}")
        except Exception as e:
            self.show_error(f"Error: {str(e)}")
    
    def get_or_create_employee_id(self, employee_name: str) -> int:
        """Get employee ID from database, create if doesn't exist"""
        # First try to find existing employee
        employees = self.db_manager.get_employees(active_only=False)
        for emp in employees:
            if emp.name == employee_name:
                return emp.id
        
        # If not found, create new employee
        return self.db_manager.add_employee(employee_name)
    
    def _add_complete_time_record(self, employee_id: int, clock_in: datetime.datetime, clock_out: datetime.datetime) -> bool:
        """Add a complete time record with both clock in and clock out times"""
        import sqlite3
        try:
            with sqlite3.connect(self.db_manager.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO time_records (employee_id, clock_in, clock_out, created_at) 
                    VALUES (?, ?, ?, ?)
                ''', (employee_id, clock_in, clock_out, datetime.datetime.now()))
                conn.commit()
                return cursor.rowcount > 0
        except Exception:
            return False
    
    def show_error(self, message: str):
        error_popup = Popup(
            title='Error',
            content=Label(text=message),
            size_hint=(0.6, 0.4)
        )
        error_popup.open()
        Clock.schedule_once(lambda dt: error_popup.dismiss(), 3)
    
    def show_success(self, message: str):
        success_popup = Popup(
            title='Success',
            content=Label(text=message),
            size_hint=(0.6, 0.4)
        )
        success_popup.open()
        Clock.schedule_once(lambda dt: success_popup.dismiss(), 2)

class AdminUI(BoxLayout):
    def __init__(self, db_manager: DatabaseManager, config: Config, **kwargs):
        super().__init__(**kwargs)
        self.db_manager = db_manager
        self.config = config
        self.email_service = EmailService(config)
        self.report_generator = ReportGenerator(config, db_manager)
        
        self.orientation = 'vertical'
        self.spacing = '10dp'
        self.padding = '10dp'
        
        self.setup_ui()
        self.load_time_records()
    
    def setup_ui(self):
        # Header
        header_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height='50dp', spacing='10dp')
        
        title_label = Label(
            text='Admin Panel - Time Records (Last 14 Days)',
            font_size='18sp',
            size_hint_x=0.55
        )
        
        add_entry_btn = Button(
            text='Add Entry',
            size_hint_x=0.15,
            background_color=[0.2, 0.6, 0.8, 1]
        )
        add_entry_btn.bind(on_press=lambda x: self.show_add_entry_dialog())
        
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
        header_layout.add_widget(add_entry_btn)
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
        
        # Get records from last 14 days (including today)
        end_date = datetime.date.today()
        start_date = end_date - datetime.timedelta(days=13)  # 13 days ago + today = 14 days total
        
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
            # Generate report data for previous two complete work weeks (2 weeks)
            records, employees, start_date, end_date = self.report_generator.get_report_data(2)
            
            # Create CSV report using shared generator
            csv_data = self.report_generator.generate_csv_report(records, employees)
            
            # Generate HTML tables for email
            html_tables = self.report_generator.generate_email_tables(records, employees)
            
            # Send email
            date_range = f"{start_date.strftime('%m/%d/%Y')} - {end_date.strftime('%m/%d/%Y')}"
            success = self.email_service.send_report_email(csv_data, date_range, records, employees, start_date, end_date, html_tables)
            
            if success:
                self.show_message("Report sent successfully!")
            else:
                self.show_message("Failed to send report. Check email configuration.")
                
        except Exception as e:
            self.show_message(f"Error sending report: {str(e)}")
    
    def show_add_entry_dialog(self):
        """Show dialog to add a new time entry"""
        add_dialog = AddEntryDialog(
            db_manager=self.db_manager,
            config=self.config,
            on_save_callback=self.load_time_records
        )
        add_dialog.open()
    
    
    def show_message(self, message: str):
        popup = Popup(
            title='Information',
            content=Label(text=message),
            size_hint=(0.6, 0.4)
        )
        popup.open()
        Clock.schedule_once(lambda dt: popup.dismiss(), 3)
