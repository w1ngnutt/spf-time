from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.clock import Clock
import datetime
from typing import Callable, Optional

class TimeSpinner(BoxLayout):
    def __init__(self, initial_value: int, min_value: int, max_value: int, 
                 label_format: str = "{:02d}", on_value_change: Optional[Callable] = None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.spacing = '5dp'
        self.size_hint_x = None
        self.width = '80dp'
        
        self.value = initial_value
        self.min_value = min_value
        self.max_value = max_value
        self.label_format = label_format
        self.on_value_change = on_value_change
        
        # Up button
        self.up_btn = Button(
            text='▲',
            size_hint_y=None,
            height='40dp',
            font_size='20sp',
            background_color=[0.3, 0.6, 1, 1]
        )
        self.up_btn.bind(on_press=self.increment_value)
        
        # Value label
        self.value_label = Label(
            text=self.label_format.format(self.value),
            size_hint_y=None,
            height='50dp',
            font_size='24sp',
            bold=True
        )
        
        # Down button
        self.down_btn = Button(
            text='▼',
            size_hint_y=None,
            height='40dp',
            font_size='20sp',
            background_color=[0.3, 0.6, 1, 1]
        )
        self.down_btn.bind(on_press=self.decrement_value)
        
        self.add_widget(self.up_btn)
        self.add_widget(self.value_label)
        self.add_widget(self.down_btn)
    
    def increment_value(self, instance):
        self.value = self.value + 1 if self.value < self.max_value else self.min_value
        self.update_display()
        if self.on_value_change:
            self.on_value_change(self.value)
    
    def decrement_value(self, instance):
        self.value = self.value - 1 if self.value > self.min_value else self.max_value
        self.update_display()
        if self.on_value_change:
            self.on_value_change(self.value)
    
    def set_value(self, value: int):
        if self.min_value <= value <= self.max_value:
            self.value = value
            self.update_display()
            if self.on_value_change:
                self.on_value_change(self.value)
    
    def update_display(self):
        self.value_label.text = self.label_format.format(self.value)

class DatePicker(BoxLayout):
    def __init__(self, initial_date: datetime.date, on_date_change: Optional[Callable] = None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.spacing = '10dp'
        self.size_hint_y = None
        self.height = '150dp'
        
        self.current_date = initial_date
        self.on_date_change = on_date_change
        
        # Month spinner
        self.add_widget(Label(text='Month', size_hint_x=None, width='80dp', size_hint_y=None, height='20dp'))
        self.month_spinner = TimeSpinner(
            initial_value=initial_date.month,
            min_value=1,
            max_value=12,
            on_value_change=self.on_month_change
        )
        
        # Day spinner
        self.add_widget(Label(text='Day', size_hint_x=None, width='80dp', size_hint_y=None, height='20dp'))
        self.day_spinner = TimeSpinner(
            initial_value=initial_date.day,
            min_value=1,
            max_value=self.get_days_in_month(initial_date.year, initial_date.month),
            on_value_change=self.on_day_change
        )
        
        # Year spinner
        self.add_widget(Label(text='Year', size_hint_x=None, width='80dp', size_hint_y=None, height='20dp'))
        current_year = datetime.date.today().year
        self.year_spinner = TimeSpinner(
            initial_value=initial_date.year,
            min_value=current_year - 2,
            max_value=current_year + 1,
            label_format="{:04d}",
            on_value_change=self.on_year_change
        )
        
        # Layout the spinners
        month_layout = BoxLayout(orientation='vertical', size_hint_x=None, width='80dp')
        month_layout.add_widget(Label(text='Month', size_hint_y=None, height='20dp', font_size='12sp'))
        month_layout.add_widget(self.month_spinner)
        
        day_layout = BoxLayout(orientation='vertical', size_hint_x=None, width='80dp')
        day_layout.add_widget(Label(text='Day', size_hint_y=None, height='20dp', font_size='12sp'))
        day_layout.add_widget(self.day_spinner)
        
        year_layout = BoxLayout(orientation='vertical', size_hint_x=None, width='80dp')
        year_layout.add_widget(Label(text='Year', size_hint_y=None, height='20dp', font_size='12sp'))
        year_layout.add_widget(self.year_spinner)
        
        self.add_widget(month_layout)
        self.add_widget(day_layout)
        self.add_widget(year_layout)
    
    def get_days_in_month(self, year: int, month: int) -> int:
        if month in [1, 3, 5, 7, 8, 10, 12]:
            return 31
        elif month in [4, 6, 9, 11]:
            return 30
        else:  # February
            return 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28
    
    def on_month_change(self, value):
        # Update day spinner range when month changes
        max_days = self.get_days_in_month(self.year_spinner.value, value)
        self.day_spinner.max_value = max_days
        if self.day_spinner.value > max_days:
            self.day_spinner.set_value(max_days)
        self.update_current_date()
    
    def on_day_change(self, value):
        self.update_current_date()
    
    def on_year_change(self, value):
        # Update day spinner range when year changes (for leap years)
        max_days = self.get_days_in_month(value, self.month_spinner.value)
        self.day_spinner.max_value = max_days
        if self.day_spinner.value > max_days:
            self.day_spinner.set_value(max_days)
        self.update_current_date()
    
    def update_current_date(self):
        try:
            self.current_date = datetime.date(
                self.year_spinner.value,
                self.month_spinner.value,
                self.day_spinner.value
            )
            if self.on_date_change:
                self.on_date_change(self.current_date)
        except ValueError:
            # Invalid date, don't update
            pass
    
    def get_selected_date(self) -> datetime.date:
        return self.current_date

class TimePicker(BoxLayout):
    def __init__(self, initial_time: datetime.time, on_time_change: Optional[Callable] = None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.spacing = '10dp'
        self.size_hint_y = None
        self.height = '150dp'
        
        self.current_time = initial_time
        self.on_time_change = on_time_change
        
        # Hour spinner
        hour_layout = BoxLayout(orientation='vertical', size_hint_x=None, width='80dp')
        hour_layout.add_widget(Label(text='Hour', size_hint_y=None, height='20dp', font_size='12sp'))
        self.hour_spinner = TimeSpinner(
            initial_value=initial_time.hour,
            min_value=0,
            max_value=23,
            on_value_change=self.on_hour_change
        )
        hour_layout.add_widget(self.hour_spinner)
        
        # Minute spinner
        minute_layout = BoxLayout(orientation='vertical', size_hint_x=None, width='80dp')
        minute_layout.add_widget(Label(text='Minute', size_hint_y=None, height='20dp', font_size='12sp'))
        self.minute_spinner = TimeSpinner(
            initial_value=initial_time.minute,
            min_value=0,
            max_value=59,
            on_value_change=self.on_minute_change
        )
        minute_layout.add_widget(self.minute_spinner)
        
        self.add_widget(hour_layout)
        self.add_widget(Label(text=':', size_hint_x=None, width='20dp', font_size='24sp', bold=True))
        self.add_widget(minute_layout)
        
        # Quick time buttons
        quick_buttons_layout = BoxLayout(orientation='vertical', spacing='5dp', size_hint_x=None, width='100dp')
        quick_buttons_layout.add_widget(Label(text='Quick', size_hint_y=None, height='20dp', font_size='12sp'))
        
        now_btn = Button(text='Now', size_hint_y=None, height='30dp', font_size='12sp')
        now_btn.bind(on_press=self.set_current_time)
        
        start_btn = Button(text='8:00', size_hint_y=None, height='30dp', font_size='12sp')
        start_btn.bind(on_press=lambda x: self.set_time(8, 0))
        
        lunch_btn = Button(text='12:00', size_hint_y=None, height='30dp', font_size='12sp')
        lunch_btn.bind(on_press=lambda x: self.set_time(12, 0))
        
        end_btn = Button(text='17:00', size_hint_y=None, height='30dp', font_size='12sp')
        end_btn.bind(on_press=lambda x: self.set_time(17, 0))
        
        quick_buttons_layout.add_widget(now_btn)
        quick_buttons_layout.add_widget(start_btn)
        quick_buttons_layout.add_widget(lunch_btn)
        quick_buttons_layout.add_widget(end_btn)
        
        self.add_widget(quick_buttons_layout)
    
    def on_hour_change(self, value):
        self.update_current_time()
    
    def on_minute_change(self, value):
        self.update_current_time()
    
    def update_current_time(self):
        self.current_time = datetime.time(
            self.hour_spinner.value,
            self.minute_spinner.value
        )
        if self.on_time_change:
            self.on_time_change(self.current_time)
    
    def set_current_time(self, instance):
        now = datetime.datetime.now().time()
        self.hour_spinner.set_value(now.hour)
        self.minute_spinner.set_value(now.minute)
    
    def set_time(self, hour: int, minute: int):
        self.hour_spinner.set_value(hour)
        self.minute_spinner.set_value(minute)
    
    def get_selected_time(self) -> datetime.time:
        return self.current_time

class DateTimePickerDialog(Popup):
    def __init__(self, initial_datetime: datetime.datetime, title: str, 
                 on_save_callback: Callable[[datetime.datetime], None], **kwargs):
        super().__init__(**kwargs)
        self.initial_datetime = initial_datetime
        self.on_save_callback = on_save_callback
        
        self.title = title
        self.size_hint = (0.9, 0.8)
        self.auto_dismiss = False
        
        main_layout = BoxLayout(orientation='vertical', spacing='20dp', padding='20dp')
        
        # Date picker
        date_label = Label(
            text='Select Date:',
            size_hint_y=None,
            height='30dp',
            font_size='16sp',
            bold=True
        )
        main_layout.add_widget(date_label)
        
        self.date_picker = DatePicker(
            initial_date=initial_datetime.date(),
            on_date_change=self.on_date_change
        )
        main_layout.add_widget(self.date_picker)
        
        # Time picker
        time_label = Label(
            text='Select Time:',
            size_hint_y=None,
            height='30dp',
            font_size='16sp',
            bold=True
        )
        main_layout.add_widget(time_label)
        
        self.time_picker = TimePicker(
            initial_time=initial_datetime.time(),
            on_time_change=self.on_time_change
        )
        main_layout.add_widget(self.time_picker)
        
        # Current selection display
        self.selection_label = Label(
            text=f'Selected: {initial_datetime.strftime("%Y-%m-%d %H:%M")}',
            size_hint_y=None,
            height='30dp',
            font_size='14sp'
        )
        main_layout.add_widget(self.selection_label)
        
        # Buttons
        button_layout = BoxLayout(
            orientation='horizontal',
            spacing='10dp',
            size_hint_y=None,
            height='50dp'
        )
        
        save_btn = Button(
            text='Save',
            background_color=[0.3, 1, 0.3, 1],
            font_size='16sp'
        )
        save_btn.bind(on_press=self.save_datetime)
        
        cancel_btn = Button(
            text='Cancel',
            background_color=[1, 0.3, 0.3, 1],
            font_size='16sp'
        )
        cancel_btn.bind(on_press=self.dismiss)
        
        button_layout.add_widget(save_btn)
        button_layout.add_widget(cancel_btn)
        main_layout.add_widget(button_layout)
        
        self.content = main_layout
        
        # Initialize current selection
        self.update_selection_display()
    
    def on_date_change(self, new_date):
        self.update_selection_display()
    
    def on_time_change(self, new_time):
        self.update_selection_display()
    
    def update_selection_display(self):
        selected_date = self.date_picker.get_selected_date()
        selected_time = self.time_picker.get_selected_time()
        selected_datetime = datetime.datetime.combine(selected_date, selected_time)
        self.selection_label.text = f'Selected: {selected_datetime.strftime("%Y-%m-%d %H:%M")}'
    
    def save_datetime(self, instance):
        selected_date = self.date_picker.get_selected_date()
        selected_time = self.time_picker.get_selected_time()
        selected_datetime = datetime.datetime.combine(selected_date, selected_time)
        
        self.on_save_callback(selected_datetime)
        self.dismiss()

# Quick time picker for common scenarios
class QuickTimePickerDialog(Popup):
    def __init__(self, current_time: datetime.datetime, time_type: str,
                 on_save_callback: Callable[[datetime.datetime], None], **kwargs):
        super().__init__(**kwargs)
        self.current_time = current_time
        self.time_type = time_type  # 'clock_in' or 'clock_out'
        self.on_save_callback = on_save_callback
        
        self.title = f'Edit {time_type.replace("_", " ").title()} Time'
        self.size_hint = (0.7, 0.6)
        self.auto_dismiss = False
        
        main_layout = BoxLayout(orientation='vertical', spacing='15dp', padding='20dp')
        
        # Current time display
        current_label = Label(
            text=f'Current: {current_time.strftime("%Y-%m-%d %H:%M")}',
            size_hint_y=None,
            height='30dp',
            font_size='16sp',
            bold=True
        )
        main_layout.add_widget(current_label)
        
        # Quick adjustment buttons
        quick_layout = GridLayout(cols=2, spacing='10dp', size_hint_y=None, height='200dp')
        
        adjustments = [
            ('-1 Hour', -60),
            ('+1 Hour', 60),
            ('-15 Min', -15),
            ('+15 Min', 15),
            ('-5 Min', -5),
            ('+5 Min', 5),
            ('-1 Min', -1),
            ('+1 Min', 1)
        ]
        
        for text, minutes in adjustments:
            btn = Button(
                text=text,
                font_size='14sp',
                background_color=[0.3, 0.6, 1, 1]
            )
            btn.bind(on_press=lambda x, m=minutes: self.adjust_time(m))
            quick_layout.add_widget(btn)
        
        main_layout.add_widget(quick_layout)
        
        # Updated time display
        self.updated_label = Label(
            text=f'New: {current_time.strftime("%Y-%m-%d %H:%M")}',
            size_hint_y=None,
            height='30dp',
            font_size='16sp'
        )
        main_layout.add_widget(self.updated_label)
        
        # Advanced edit button
        advanced_btn = Button(
            text='Advanced Edit',
            size_hint_y=None,
            height='40dp',
            background_color=[0.8, 0.6, 0.2, 1]
        )
        advanced_btn.bind(on_press=self.open_advanced_picker)
        main_layout.add_widget(advanced_btn)
        
        # Action buttons
        button_layout = BoxLayout(orientation='horizontal', spacing='10dp', size_hint_y=None, height='50dp')
        
        save_btn = Button(text='Save', background_color=[0.3, 1, 0.3, 1])
        save_btn.bind(on_press=self.save_time)
        
        cancel_btn = Button(text='Cancel', background_color=[1, 0.3, 0.3, 1])
        cancel_btn.bind(on_press=self.dismiss)
        
        button_layout.add_widget(save_btn)
        button_layout.add_widget(cancel_btn)
        main_layout.add_widget(button_layout)
        
        self.content = main_layout
        self.new_time = current_time
    
    def adjust_time(self, minutes):
        self.new_time = self.new_time + datetime.timedelta(minutes=minutes)
        self.updated_label.text = f'New: {self.new_time.strftime("%Y-%m-%d %H:%M")}'
    
    def open_advanced_picker(self, instance):
        self.dismiss()
        advanced_picker = DateTimePickerDialog(
            initial_datetime=self.new_time,
            title=f'Edit {self.time_type.replace("_", " ").title()} Time',
            on_save_callback=self.on_save_callback
        )
        advanced_picker.open()
    
    def save_time(self, instance):
        self.on_save_callback(self.new_time)
        self.dismiss()