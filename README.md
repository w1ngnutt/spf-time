# Employee Time Tracking Application

A Python-based employee time tracking application built with Kivy for the user interface and SQLite for data storage. This application provides a simple and efficient way to track employee work hours with clock in/out functionality.

## Features

- **Simple Clock In/Out Interface**: Easy-to-use buttons for each employee
- **Real-time Status Display**: Shows current work duration for clocked-in employees
- **Automatic Clock-out**: Prevents excessive work sessions by auto-clocking out after configured hours
- **Configurable Settings**: Customize employee lists, payroll periods, and behavior via TOML configuration
- **SQLite Database**: Reliable local data storage with proper indexing for performance
- **Business Rules**: Built-in validation for minimum break times and shift limits
- **Cross-platform**: Runs on Windows, macOS, and Linux

## Requirements

- Python 3.11 or higher
- uv package manager

## Installation

### 1. Clone or Download the Project

```bash
git clone <repository-url>
cd spf-time
```

### 2. Install Dependencies

This project uses `uv` for dependency management. If you don't have `uv` installed:

```bash
# Install uv (if not already installed)
pip install uv
```

Then install project dependencies:

```bash
uv sync
```

## Configuration

The application is configured via the `settings.toml` file in the project root. Key configuration options include:

### Employee Setup
```toml
[employees]
names = [
    "John Smith",
    "Jane Doe", 
    "Bob Johnson",
    "Alice Wilson",
    "Mike Davis"
]
```

### Time Tracking Settings
```toml
[time_tracking]
# Maximum hours before employee is automatically clocked out
auto_clock_out_hours = 12

# Minimum break time between clock in/out operations (in minutes)
min_break_time_minutes = 1

# Grace period for late clock ins/outs (in minutes)
grace_period_minutes = 5
```

### Payroll Configuration
```toml
[payroll]
# Day of the week when payroll period begins (0=Monday, 6=Sunday)
start_day = 1  # Tuesday
```

### UI Customization
```toml
[ui]
window_title = "Employee Time Tracking"
window_width = 800
window_height = 600

# Button colors (RGBA values)
clock_in_color = [0.2, 0.8, 0.2, 1.0]    # Green
clock_out_color = [0.8, 0.2, 0.2, 1.0]   # Red
disabled_color = [0.5, 0.5, 0.5, 1.0]    # Gray
```

## Running the Application

### Using uv (Recommended)

```bash
uv run python -m spf_time.main
```

### Using the Installed Script

After installation, you can also run:

```bash
uv run spf-time
```

### Direct Python Execution

```bash
# Activate the virtual environment first
source .venv/bin/activate  # On Linux/macOS
# or
.venv\Scripts\activate     # On Windows

python -m spf_time.main
```

## Development

### Project Structure

```
spf-time/
   spf_time/              # Main application package
      __init__.py        # Package initialization
      main.py            # Application entry point and UI
      database.py        # Database operations and models
      config.py          # Configuration management
      business_rules.py  # Business logic and validation
   settings.toml          # Application configuration
   pyproject.toml         # Project metadata and dependencies
   time_tracking.db       # SQLite database (created on first run)
   README.md             # This file
```

### Development Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd spf-time
   ```

2. **Install development dependencies**:
   ```bash
   uv sync --dev
   ```

3. **Run in development mode**:
   ```bash
   uv run python -m spf_time.main
   ```

### Code Architecture

- **`main.py`**: Contains the Kivy application class and UI components
- **`database.py`**: Database models and operations using SQLite
- **`config.py`**: Configuration loading and management from TOML files
- **`business_rules.py`**: Time tracking business logic, validation, and reporting

### Database Schema

The application uses SQLite with the following tables:

#### Employees Table
```sql
CREATE TABLE employees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Time Records Table
```sql
CREATE TABLE time_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER NOT NULL,
    clock_in TIMESTAMP NOT NULL,
    clock_out TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (employee_id) REFERENCES employees (id)
);
```

## Usage

### Basic Operation

1. **Start the application**: Run using one of the methods described above
2. **Clock In**: Click the "Clock In" button next to an employee's name
3. **Monitor Time**: The status column shows "Clocked In" with duration
4. **Clock Out**: Click the "Clock Out" button to end the work session

### Employee Management

Employees are managed through the `settings.toml` file. To add or remove employees:

1. Edit the `[employees]` section in `settings.toml`
2. Restart the application
3. New employees will be automatically added to the database

### Data Storage

- **Database Location**: `time_tracking.db` in the project root
- **Automatic Backup**: Consider implementing regular backups of the database file
- **Data Export**: Use the reporting functions in `business_rules.py` for data export

## Business Rules

The application implements several business rules for hourly employees:

### Time Tracking Rules
- **Minimum Break Time**: Configurable minimum time between clock operations
- **Maximum Shift Length**: Automatic clock-out after configured hours
- **Grace Period**: Allows small timing adjustments for clock operations
- **No Double Clock-in**: Prevents multiple active sessions per employee

### Validation
- Clock-out time must be after clock-in time
- Future timestamps are not allowed (beyond grace period)
- Maximum shift duration enforcement
- Minimum work session duration

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure you're running from the project root directory
2. **Database Permissions**: Check write permissions for the project directory
3. **Configuration Errors**: Validate TOML syntax in `settings.toml`
4. **Display Issues**: Kivy requires proper graphics drivers for optimal performance

### Debug Mode

For development and debugging, you can enable Kivy's debug output:

```bash
export KIVY_LOG_LEVEL=debug
uv run python -m spf_time.main
```

### Database Issues

If you encounter database corruption:

1. Stop the application
2. Backup the current `time_tracking.db` file
3. Delete the corrupted database file
4. Restart the application (a new database will be created)

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Test thoroughly
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Future Enhancements

Potential features for future development:

- **Web Interface**: Browser-based UI for remote access
- **Report Generation**: CSV/PDF export capabilities
- **Employee Photos**: Photo capture during clock operations
- **Department Tracking**: Organize employees by departments
- **Overtime Alerts**: Notifications for approaching overtime
- **Break Reminders**: Automated break time notifications
- **Payroll Integration**: Direct integration with payroll systems
- **Multi-location Support**: GPS-based location verification
- **Supervisor Dashboard**: Management overview interface
- **Time Corrections**: Administrative time entry adjustments