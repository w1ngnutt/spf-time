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
- **`admin_ui.py`**: Admin panel with touch-friendly interface for time entry management
- **`database.py`**: Database models and operations using SQLite
- **`config.py`**: Configuration loading and management from TOML files
- **`business_rules.py`**: Time tracking business logic, validation, and reporting
- **`email_service.py`**: Email report functionality with SendGrid integration
- **`report_generator.py`**: Shared report generation engine for CSV and ASCII output
- **`time_picker.py`**: Touch-friendly time selection UI components
- **`generate_report.py`**: Command-line report generator script

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
- **Data Export**: Use the built-in report generator for CSV and ASCII table exports

## Report Generation

The application includes a powerful command-line report generator that can produce time tracking reports in multiple formats. Reports include only complete work weeks based on your configured payroll start day.

### Quick Start

Generate a 2-week ASCII table report:
```bash
uv run python generate_report.py 2
```

Generate a 4-week CSV report:
```bash
uv run python generate_report.py 4 -o=csv
```

### Usage Options

```bash
uv run python generate_report.py <weeks> [options]
```

**Arguments:**
- `weeks`: Number of complete work weeks to include (1-52)

**Options:**
- `-o=csv`, `--output=csv`: Output in CSV format instead of ASCII table
- `-h`, `--help`: Show help message

### Output Formats

#### ASCII Table (Default)
The default output produces a formatted ASCII table suitable for console viewing:

```
Time Tracking Report - 2 Weeks
Period: 2025-06-16 to 2025-06-29

+----------+------------+----------+----------------+-----------------+
| Employee | Date       | Clock In | Clock Out      | Duration (Hours)|
+----------+------------+----------+----------------+-----------------+
| Edgar    | 2025-06-16 | 08:00:00 | 16:30:00       | 8.50            |
| Edgar    | 2025-06-17 | 07:45:00 | 16:15:00       | 8.50            |
| Jeff     | 2025-06-16 | 09:00:00 | 17:00:00       | 8.00            |
| Jeff     | 2025-06-17 | 09:00:00 | 17:00:00       | 8.00            |
+----------+------------+----------+----------------+-----------------+

Summary:
--------------------------------------------------
Edgar: 17.00 hours
Jeff: 16.00 hours
Total: 33.00 hours
```

#### CSV Format
When using the `-o=csv` option, the output is in standard CSV format suitable for import into spreadsheet applications:

```csv
Employee,Date,Clock In,Clock Out,Duration (Hours)
Edgar,2025-06-16,08:00:00,16:30:00,8.5
Edgar,2025-06-17,07:45:00,16:15:00,8.5
Jeff,2025-06-16,09:00:00,17:00:00,8.0
Jeff,2025-06-17,09:00:00,17:00:00,8.0
```

### Examples

**Generate last 1 week report (ASCII table):**
```bash
uv run python generate_report.py 1
```

**Generate last 3 weeks as CSV:**
```bash
uv run python generate_report.py 3 -o=csv
```

**Save CSV report to file:**
```bash
uv run python generate_report.py 4 -o=csv > timesheet_report.csv
```

**Generate monthly report (4 weeks):**
```bash
uv run python generate_report.py 4
```

### Work Week Calculation

Reports are based on complete work weeks only:
- Uses the `payroll.start_day` setting from `settings.toml`
- Excludes the current incomplete work week
- Only includes fully completed weeks in the date range
- Ensures consistent payroll period reporting

For example, if today is Friday and your work week starts on Wednesday:
- Current week (Wed-Tue) is incomplete and excluded
- Previous complete weeks are included in the report

### Email Integration

The same report generator powers the automated email reports sent by the admin panel. Email reports include:
- CSV attachment with detailed time records
- HTML tables organized by employee and week
- Weekly totals and summaries

### Error Handling

The report generator includes comprehensive error handling:
- Validates week count (1-52 weeks maximum)
- Checks for database and configuration file existence
- Provides clear error messages for troubleshooting

**Common errors and solutions:**
- `Configuration file not found`: Ensure `settings.toml` exists in the project root
- `Database file not found`: Run the main application first to create the database
- `No time records found`: Verify employees have clocked time in the specified period

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

## Deployment to Raspberry Pi

The application includes automated build and deployment scripts for easy installation on Raspberry Pi devices running Raspbian with X11.

### Quick Deployment

1. **Build the application:**
   ```bash
   ./build.sh
   ```

2. **Deploy to Raspberry Pi:**
   ```bash
   ./deploy.sh pi@raspberrypi.local
   ```

### Build Process

The build script (`build.sh`) creates a distribution package that includes:
- All application files
- Launcher script with uv auto-installation
- Desktop file for autostart configuration
- Installation script for target system

```bash
./build.sh
```

This creates `dist/spf-time.tar.gz` ready for deployment.

### Deployment Process

The deployment script (`deploy.sh`) handles the complete installation:

```bash
./deploy.sh user@hostname
```

**What it does:**
- Tests SSH connectivity
- Copies distribution archive to target
- Preserves existing `settings.toml` and `time_tracking.db`
- Installs application to `~/spf-time`
- Configures autostart via desktop file
- Sets up application menu entry

**Prerequisites:**
- SSH key authentication configured
- Target user has home directory access
- Internet connection on target (for uv installation)

### Target System Setup

The application installs to the user's home directory:
```
~/spf-time/
├── spf_time/           # Application code
├── pyproject.toml      # Dependencies
├── settings.toml       # Configuration (preserved)
├── time_tracking.db    # Database (preserved)
├── generate_report.py  # Report generator
└── run.sh             # Launcher script
```

**Autostart Configuration:**
- Desktop file: `~/.config/autostart/spf-time.desktop`
- Application menu: `~/.local/share/applications/spf-time.desktop`

### Manual Installation

If you prefer manual installation:

1. Copy `dist/spf-time.tar.gz` to target system
2. Extract: `tar -xzf spf-time.tar.gz`
3. Run: `cd spf-time && bash install.sh`

### Updating Deployment

To update an existing installation:
1. Run `./build.sh` to create new distribution
2. Run `./deploy.sh user@hostname` 
3. Existing settings and data are automatically preserved

### Troubleshooting Deployment

**SSH Connection Issues:**
```bash
# Test SSH access
ssh pi@raspberrypi.local "echo 'Connection OK'"

# Set up SSH keys if needed
ssh-copy-id pi@raspberrypi.local
```

**Application Won't Start:**
```bash
# Check logs on target system
ssh pi@raspberrypi.local "~/spf-time/run.sh"

# Check X11 environment
ssh pi@raspberrypi.local "echo \$DISPLAY"
```

**Manual Start:**
```bash
# On the Raspberry Pi
cd ~/spf-time
./run.sh
```

