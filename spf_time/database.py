import sqlite3
import datetime
from typing import List, Optional, Tuple
from dataclasses import dataclass

@dataclass
class Employee:
    id: Optional[int]
    name: str
    is_active: bool = True

@dataclass
class TimeRecord:
    id: Optional[int]
    employee_id: int
    clock_in: datetime.datetime
    clock_out: Optional[datetime.datetime] = None
    created_at: Optional[datetime.datetime] = None

class DatabaseManager:
    def __init__(self, db_path: str = "time_tracking.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS employees (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS time_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    employee_id INTEGER NOT NULL,
                    clock_in TIMESTAMP NOT NULL,
                    clock_out TIMESTAMP NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (employee_id) REFERENCES employees (id)
                )
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_employee_id 
                ON time_records(employee_id)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_clock_in 
                ON time_records(clock_in)
            ''')
            
            conn.commit()
    
    def add_employee(self, name: str) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO employees (name) VALUES (?)', (name,))
            conn.commit()
            return cursor.lastrowid
    
    def get_employees(self, active_only: bool = True) -> List[Employee]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            if active_only:
                cursor.execute('SELECT id, name, is_active FROM employees WHERE is_active = 1')
            else:
                cursor.execute('SELECT id, name, is_active FROM employees')
            
            return [Employee(id=row[0], name=row[1], is_active=bool(row[2])) 
                   for row in cursor.fetchall()]
    
    def clock_in(self, employee_id: int) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            clock_in_time = datetime.datetime.now()
            cursor.execute(
                'INSERT INTO time_records (employee_id, clock_in) VALUES (?, ?)',
                (employee_id, clock_in_time)
            )
            conn.commit()
            return cursor.lastrowid
    
    def clock_out(self, employee_id: int) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            clock_out_time = datetime.datetime.now()
            
            # First, find the most recent clock-in record without a clock-out
            cursor.execute('''
                SELECT id FROM time_records 
                WHERE employee_id = ? AND clock_out IS NULL
                ORDER BY clock_in DESC LIMIT 1
            ''', (employee_id,))
            
            result = cursor.fetchone()
            if result:
                record_id = result[0]
                cursor.execute('''
                    UPDATE time_records 
                    SET clock_out = ? 
                    WHERE id = ?
                ''', (clock_out_time, record_id))
                conn.commit()
                return cursor.rowcount > 0
            
            return False
    
    def is_clocked_in(self, employee_id: int) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT COUNT(*) FROM time_records 
                WHERE employee_id = ? AND clock_out IS NULL
            ''', (employee_id,))
            return cursor.fetchone()[0] > 0
    
    def get_current_session(self, employee_id: int) -> Optional[TimeRecord]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, employee_id, clock_in, clock_out, created_at
                FROM time_records 
                WHERE employee_id = ? AND clock_out IS NULL
                ORDER BY clock_in DESC LIMIT 1
            ''', (employee_id,))
            
            row = cursor.fetchone()
            if row:
                return TimeRecord(
                    id=row[0],
                    employee_id=row[1],
                    clock_in=datetime.datetime.fromisoformat(row[2]),
                    clock_out=datetime.datetime.fromisoformat(row[3]) if row[3] else None,
                    created_at=datetime.datetime.fromisoformat(row[4]) if row[4] else None
                )
            return None
    
    def get_time_records(self, employee_id: Optional[int] = None, 
                        start_date: Optional[datetime.date] = None,
                        end_date: Optional[datetime.date] = None) -> List[TimeRecord]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            query = '''
                SELECT id, employee_id, clock_in, clock_out, created_at
                FROM time_records WHERE 1=1
            '''
            params = []
            
            if employee_id:
                query += ' AND employee_id = ?'
                params.append(employee_id)
            
            if start_date:
                query += ' AND DATE(clock_in) >= ?'
                params.append(start_date.isoformat())
            
            if end_date:
                query += ' AND DATE(clock_in) <= ?'
                params.append(end_date.isoformat())
            
            query += ' ORDER BY clock_in DESC'
            
            cursor.execute(query, params)
            
            records = []
            for row in cursor.fetchall():
                records.append(TimeRecord(
                    id=row[0],
                    employee_id=row[1],
                    clock_in=datetime.datetime.fromisoformat(row[2]),
                    clock_out=datetime.datetime.fromisoformat(row[3]) if row[3] else None,
                    created_at=datetime.datetime.fromisoformat(row[4]) if row[4] else None
                ))
            
            return records
    
    def auto_clock_out_expired_sessions(self, max_hours: int = 12):
        cutoff_time = datetime.datetime.now() - datetime.timedelta(hours=max_hours)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE time_records 
                SET clock_out = ? 
                WHERE clock_out IS NULL AND clock_in < ?
            ''', (datetime.datetime.now(), cutoff_time))
            
            conn.commit()
            return cursor.rowcount
    
    def update_time_record(self, record_id: int, clock_in: datetime.datetime, 
                          clock_out: Optional[datetime.datetime] = None) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE time_records 
                SET clock_in = ?, clock_out = ?
                WHERE id = ?
            ''', (clock_in, clock_out, record_id))
            
            conn.commit()
            return cursor.rowcount > 0
    
    def delete_time_record(self, record_id: int) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM time_records WHERE id = ?', (record_id,))
            conn.commit()
            return cursor.rowcount > 0