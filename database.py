"""
Database module for Car Wash Management System
Handles all SQLite database operations with proper error handling and transactions
"""

import sqlite3
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import uuid


class Database:
    """Main database class handling all SQLite operations for the car wash system"""
    
    def __init__(self, db_path: str = "carwash.db"):
        """Initialize database connection with automatic table creation"""
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self) -> sqlite3.Connection:
        """Get a database connection with row factory for dict-like access"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self) -> None:
        """Initialize all database tables with proper schema"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Workers table with comprehensive fields
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS workers (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                role TEXT NOT NULL,
                phone TEXT,
                email TEXT,
                hire_date TEXT,
                hourly_rate REAL DEFAULT 0,
                skills TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Services table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS services (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                base_price REAL NOT NULL,
                duration_minutes INTEGER DEFAULT 30,
                vehicle_type TEXT NOT NULL,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Vehicle types table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vehicle_types (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Customers table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                phone TEXT,
                email TEXT,
                address TEXT,
                loyalty_points INTEGER DEFAULT 0,
                total_orders INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Work orders table with comprehensive tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS work_orders (
                id TEXT PRIMARY KEY,
                customer_id TEXT,
                customer_name TEXT NOT NULL,
                customer_phone TEXT,
                vehicle_type TEXT NOT NULL,
                vehicle_make TEXT,
                vehicle_model TEXT,
                plate_number TEXT NOT NULL,
                services TEXT NOT NULL,
                total_cost REAL NOT NULL,
                status TEXT DEFAULT 'pending',
                priority TEXT DEFAULT 'normal',
                assigned_worker_id TEXT,
                assigned_worker_name TEXT,
                assigned_at TEXT,
                started_at TEXT,
                ended_at TEXT,
                completion_notes TEXT,
                customer_rating INTEGER,
                customer_feedback TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customers(id),
                FOREIGN KEY (assigned_worker_id) REFERENCES workers(id)
            )
        """)
        
        # Attendance tracking table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS attendance (
                id TEXT PRIMARY KEY,
                worker_id TEXT NOT NULL,
                date TEXT NOT NULL,
                check_in TEXT,
                check_out TEXT,
                status TEXT DEFAULT 'present',
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (worker_id) REFERENCES workers(id),
                UNIQUE(worker_id, date)
            )
        """)
        
        # Create indexes for better query performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_work_orders_status ON work_orders(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_work_orders_date ON work_orders(created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_work_orders_worker ON work_orders(assigned_worker_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_attendance_worker ON attendance(worker_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance(date)")
        
        conn.commit()
        conn.close()
        
        # Seed initial data if tables are empty
        self.seed_initial_data()
    
    def seed_initial_data(self) -> None:
        """Seed initial workers and services if database is empty"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Check if workers exist
        cursor.execute("SELECT COUNT(*) FROM workers")
        if cursor.fetchone()[0] == 0:
            default_workers = [
                (str(uuid.uuid4()), "Kwame Asante", "Senior Washer", "+233244123456", "kwame@carwash.com", 
                 datetime.now().strftime("%Y-%m-%d"), 25.0, " Exterior Wash,Interior Clean,Detailing", 1),
                (str(uuid.uuid4()), "Abena Mensah", "Washer", "+233244234567", "abena@carwash.com",
                 datetime.now().strftime("%Y-%m-%d"), 20.0, " Exterior Wash,Basic Clean", 1),
                (str(uuid.uuid4()), "Kofi Boateng", "Detailing Specialist", "+233244345678", "kofi@carwash.com",
                 datetime.now().strftime("%Y-%m-%d"), 30.0, " Detailing,Engine Clean,Wax Treatment", 1),
                (str(uuid.uuid4()), "Akua Darko", "Washer", "+233244456789", "akua@carwash.com",
                 datetime.now().strftime("%Y-%m-%d"), 20.0, " Exterior Wash,Interior Clean", 1),
            ]
            cursor.executemany(
                "INSERT INTO workers (id, name, role, phone, email, hire_date, hourly_rate, skills, is_active) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                default_workers
            )
        
        # Check if vehicle types exist
        cursor.execute("SELECT COUNT(*) FROM vehicle_types")
        if cursor.fetchone()[0] == 0:
            vehicle_types = [
                (str(uuid.uuid4()), "Sedan", "Standard 4-door sedan"),
                (str(uuid.uuid4()), "SUV", "Sport Utility Vehicle"),
                (str(uuid.uuid4()), "Truck", "Pickup trucks and light trucks"),
                (str(uuid.uuid4()), "Van", "Minivans and full-size vans"),
                (str(uuid.uuid4()), "Luxury", "High-end luxury vehicles"),
            ]
            cursor.executemany(
                "INSERT INTO vehicle_types (id, name, description) VALUES (?, ?, ?)",
                vehicle_types
            )
        
        # Check if services exist
        cursor.execute("SELECT COUNT(*) FROM services")
        if cursor.fetchone()[0] == 0:
            default_services = [
                (str(uuid.uuid4()), "Basic Exterior Wash", "Standard exterior wash with soap and rinse", 50.0, 30, "Sedan", 1),
                (str(uuid.uuid4()), "Interior Clean", "Vacuum, wipe down, and interior cleaning", 40.0, 45, "Sedan", 1),
                (str(uuid.uuid4()), "Full Detailing", "Complete interior and exterior detailing", 150.0, 120, "Sedan", 1),
                (str(uuid.uuid4()), "Engine Clean", "Steam cleaning of engine bay", 80.0, 45, "Sedan", 1),
                (str(uuid.uuid4()), "Wax Treatment", "Application of premium car wax", 100.0, 60, "Sedan", 1),
                (str(uuid.uuid4()), "SUV Exterior Wash", "Exterior wash for SUV vehicles", 65.0, 35, "SUV", 1),
                (str(uuid.uuid4()), "SUV Interior Clean", "Interior cleaning for SUV vehicles", 50.0, 50, "SUV", 1),
                (str(uuid.uuid4()), "Truck Exterior Wash", "Exterior wash for truck vehicles", 70.0, 40, "Truck", 1),
            ]
            cursor.executemany(
                "INSERT INTO services (id, name, description, base_price, duration_minutes, vehicle_type, is_active) VALUES (?, ?, ?, ?, ?, ?, ?)",
                default_services
            )
        
        conn.commit()
        conn.close()
    
    # ==================== WORKER OPERATIONS ====================
    
    def add_worker(self, name: str, role: str, phone: str = None, email: str = None,
                   hire_date: str = None, hourly_rate: float = 0, skills: str = "") -> str:
        """Add a new worker to the system"""
        worker_id = str(uuid.uuid4())
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO workers (id, name, role, phone, email, hire_date, hourly_rate, skills)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (worker_id, name, role, phone, email, hire_date or datetime.now().strftime("%Y-%m-%d"), hourly_rate, skills))
        
        conn.commit()
        conn.close()
        return worker_id
    
    def get_all_workers(self, active_only: bool = True) -> List[Dict]:
        """Get all workers with optional active filter"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if active_only:
            cursor.execute("SELECT * FROM workers WHERE is_active = 1 ORDER BY name")
        else:
            cursor.execute("SELECT * FROM workers ORDER BY name")
        
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def get_worker(self, worker_id: str) -> Optional[Dict]:
        """Get a single worker by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM workers WHERE id = ?", (worker_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    def update_worker(self, worker_id: str, **kwargs) -> bool:
        """Update worker information"""
        allowed_fields = ['name', 'role', 'phone', 'email', 'hourly_rate', 'skills', 'is_active']
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
        
        if not updates:
            return False
        
        updates['updated_at'] = datetime.now().isoformat()
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [worker_id]
        
        cursor.execute(f"UPDATE workers SET {set_clause} WHERE id = ?", values)
        conn.commit()
        conn.close()
        return True
    
    def delete_worker(self, worker_id: str) -> bool:
        """Soft delete a worker by setting is_active to 0"""
        return self.update_worker(worker_id, is_active=0)
    
    # ==================== SERVICE OPERATIONS ====================
    
    def add_service(self, name: str, description: str, base_price: float,
                    duration_minutes: int, vehicle_type: str) -> str:
        """Add a new service to the system"""
        service_id = str(uuid.uuid4())
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO services (id, name, description, base_price, duration_minutes, vehicle_type)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (service_id, name, description, base_price, duration_minutes, vehicle_type))
        
        conn.commit()
        conn.close()
        return service_id
    
    def get_all_services(self, vehicle_type: str = None) -> List[Dict]:
        """Get all services with optional vehicle type filter"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if vehicle_type:
            cursor.execute("SELECT * FROM services WHERE vehicle_type = ? AND is_active = 1 ORDER BY name", (vehicle_type,))
        else:
            cursor.execute("SELECT * FROM services WHERE is_active = 1 ORDER BY vehicle_type, name")
        
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def get_service(self, service_id: str) -> Optional[Dict]:
        """Get a single service by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM services WHERE id = ?", (service_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    def update_service(self, service_id: str, **kwargs) -> bool:
        """Update service information"""
        allowed_fields = ['name', 'description', 'base_price', 'duration_minutes', 'vehicle_type', 'is_active']
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
        
        if not updates:
            return False
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [service_id]
        
        cursor.execute(f"UPDATE services SET {set_clause} WHERE id = ?", values)
        conn.commit()
        conn.close()
        return True
    
    def delete_service(self, service_id: str) -> bool:
        """Soft delete a service"""
        return self.update_service(service_id, is_active=0)
    
    # ==================== VEHICLE TYPE OPERATIONS ====================
    
    def get_all_vehicle_types(self) -> List[Dict]:
        """Get all vehicle types"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM vehicle_types ORDER BY name")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def add_vehicle_type(self, name: str, description: str = "") -> str:
        """Add a new vehicle type"""
        vehicle_type_id = str(uuid.uuid4())
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO vehicle_types (id, name, description) VALUES (?, ?, ?)",
                      (vehicle_type_id, name, description))
        conn.commit()
        conn.close()
        return vehicle_type_id
    
    # ==================== WORK ORDER OPERATIONS ====================
    
    def create_work_order(self, customer_name: str, customer_phone: str, vehicle_type: str,
                          vehicle_make: str, vehicle_model: str, plate_number: str,
                          services: List[str], total_cost: float, priority: str = "normal",
                          assigned_worker_id: str = None, assigned_worker_name: str = None) -> str:
        """Create a new work order"""
        order_id = f"WO-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:4].upper()}"
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO work_orders 
            (id, customer_name, customer_phone, vehicle_type, vehicle_make, vehicle_model, 
             plate_number, services, total_cost, status, priority, assigned_worker_id, 
             assigned_worker_name, assigned_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (order_id, customer_name, customer_phone, vehicle_type, vehicle_make,
              vehicle_model, plate_number, ",".join(services), total_cost, 'pending',
              priority, assigned_worker_id, assigned_worker_name,
              datetime.now().isoformat() if assigned_worker_id else None))
        
        conn.commit()
        conn.close()
        return order_id
    
    def get_all_work_orders(self, status: str = None, worker_id: str = None,
                           date_from: str = None, date_to: str = None) -> List[Dict]:
        """Get work orders with optional filters"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM work_orders WHERE 1=1"
        params = []
        
        if status:
            query += " AND status = ?"
            params.append(status)
        
        if worker_id:
            query += " AND assigned_worker_id = ?"
            params.append(worker_id)
        
        if date_from:
            query += " AND DATE(created_at) >= ?"
            params.append(date_from)
        
        if date_to:
            query += " AND DATE(created_at) <= ?"
            params.append(date_to)
        
        query += " ORDER BY created_at DESC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def get_work_order(self, order_id: str) -> Optional[Dict]:
        """Get a single work order by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM work_orders WHERE id = ?", (order_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    def update_work_order(self, order_id: str, **kwargs) -> bool:
        """Update work order information"""
        allowed_fields = ['status', 'priority', 'assigned_worker_id', 'assigned_worker_name',
                         'assigned_at', 'started_at', 'ended_at', 'completion_notes',
                         'customer_rating', 'customer_feedback', 'total_cost']
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
        
        if not updates:
            return False
        
        updates['updated_at'] = datetime.now().isoformat()
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [order_id]
        
        cursor.execute(f"UPDATE work_orders SET {set_clause} WHERE id = ?", values)
        conn.commit()
        conn.close()
        return True
    
    def assign_worker_to_order(self, order_id: str, worker_id: str, worker_name: str) -> bool:
        """Assign a worker to a work order"""
        return self.update_work_order(order_id, assigned_worker_id=worker_id,
                                     assigned_worker_name=worker_name,
                                     assigned_at=datetime.now().isoformat())
    
    def start_work_order(self, order_id: str) -> bool:
        """Mark a work order as started"""
        return self.update_work_order(order_id, status='in_progress',
                                     started_at=datetime.now().isoformat())
    
    def complete_work_order(self, order_id: str, notes: str = None,
                           rating: int = None, feedback: str = None) -> bool:
        """Mark a work order as completed"""
        return self.update_work_order(order_id, status='completed',
                                     ended_at=datetime.now().isoformat(),
                                     completion_notes=notes,
                                     customer_rating=rating,
                                     customer_feedback=feedback)
    
    def cancel_work_order(self, order_id: str, reason: str = None) -> bool:
        """Cancel a work order"""
        return self.update_work_order(order_id, status='cancelled',
                                     completion_notes=reason)
    
    # ==================== ATTENDANCE OPERATIONS ====================
    
    def record_attendance(self, worker_id: str, date: str = None,
                         check_in: str = None, check_out: str = None,
                         status: str = "present", notes: str = None) -> str:
        """Record or update worker attendance"""
        attendance_id = str(uuid.uuid4())
        date = date or datetime.now().strftime("%Y-%m-%d")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Use INSERT OR REPLACE to update if exists
        cursor.execute("""
            INSERT OR REPLACE INTO attendance 
            (id, worker_id, date, check_in, check_out, status, notes)
            VALUES (
                COALESCE((SELECT id FROM attendance WHERE worker_id = ? AND date = ?), ?),
                ?, ?, ?, ?, ?, ?
            )
        """, (worker_id, date, attendance_id, worker_id, date, check_in, check_out, status, notes))
        
        conn.commit()
        conn.close()
        return attendance_id
    
    def get_attendance_records(self, worker_id: str = None, date_from: str = None,
                               date_to: str = None) -> List[Dict]:
        """Get attendance records with optional filters"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM attendance WHERE 1=1"
        params = []
        
        if worker_id:
            query += " AND worker_id = ?"
            params.append(worker_id)
        
        if date_from:
            query += " AND date >= ?"
            params.append(date_from)
        
        if date_to:
            query += " AND date <= ?"
            params.append(date_to)
        
        query += " ORDER BY date DESC, check_in DESC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    # ==================== ANALYTICS OPERATIONS ====================
    
    def get_order_statistics(self, date_from: str = None, date_to: str = None) -> Dict:
        """Get comprehensive order statistics"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        base_query = "SELECT status, COUNT(*) as count, SUM(total_cost) as revenue FROM work_orders WHERE 1=1"
        params = []
        
        if date_from:
            base_query += " AND DATE(created_at) >= ?"
            params.append(date_from)
        
        if date_to:
            base_query += " AND DATE(created_at) <= ?"
            params.append(date_to)
        
        base_query += " GROUP BY status"
        
        cursor.execute(base_query, params)
        status_stats = {row['status']: {'count': row['count'], 'revenue': row['revenue'] or 0}
                       for row in cursor.fetchall()}
        
        # Get total orders and revenue
        cursor.execute(f"""
            SELECT COUNT(*) as total, SUM(total_cost) as total_revenue,
                   AVG(total_cost) as avg_order_value
            FROM work_orders WHERE 1=1
            {'AND DATE(created_at) >= ?' if date_from else ''}
            {'AND DATE(created_at) <= ?' if date_to else ''}
        """, [p for p in params if p])
        
        totals = cursor.fetchone()
        
        # Get today's stats
        today = datetime.now().strftime("%Y-%m-%d")
        cursor.execute("""
            SELECT COUNT(*) as today_orders, SUM(total_cost) as today_revenue
            FROM work_orders
            WHERE DATE(created_at) = ?
        """, (today,))
        today_stats = cursor.fetchone()
        
        conn.close()
        
        return {
            'by_status': status_stats,
            'total_orders': totals['total'] or 0,
            'total_revenue': totals['total_revenue'] or 0,
            'avg_order_value': totals['avg_order_value'] or 0,
            'today_orders': today_stats['today_orders'] or 0,
            'today_revenue': today_stats['today_revenue'] or 0
        }
    
    def get_worker_performance(self, date_from: str = None, date_to: str = None) -> List[Dict]:
        """Get worker performance metrics"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT w.id, w.name, w.role,
                   COUNT(o.id) as total_orders,
                   SUM(CASE WHEN o.status = 'completed' THEN 1 ELSE 0 END) as completed_orders,
                   SUM(CASE WHEN o.status = 'completed' THEN o.total_cost ELSE 0 END) as total_revenue,
                   AVG(CASE WHEN o.ended_at IS NOT NULL AND o.started_at IS NOT NULL
                       THEN (julianday(o.ended_at) - julianday(o.started_at)) * 24 * 60
                       ELSE NULL END) as avg_completion_minutes,
                   AVG(CASE WHEN o.customer_rating IS NOT NULL THEN o.customer_rating ELSE 0 END) as avg_rating
            FROM workers w
            LEFT JOIN work_orders o ON w.id = o.assigned_worker_id
                AND o.created_at >= COALESCE(?, o.created_at)
                AND o.created_at <= COALESCE(?, o.created_at)
            WHERE w.is_active = 1
            GROUP BY w.id
            ORDER BY total_revenue DESC
        """
        
        cursor.execute(query, (date_from, date_to))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def get_service_popularity(self, date_from: str = None, date_to: str = None) -> List[Dict]:
        """Get service popularity statistics"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Get all orders in date range
        query = """
            SELECT services FROM work_orders
            WHERE 1=1
        """
        params = []
        
        if date_from:
            query += " AND DATE(created_at) >= ?"
            params.append(date_from)
        
        if date_to:
            query += " AND DATE(created_at) <= ?"
            params.append(date_to)
        
        cursor.execute(query, params)
        orders = cursor.fetchall()
        
        # Count service occurrences
        service_counts = {}
        for order in orders:
            services = order['services'].split(',')
            for service in services:
                service = service.strip()
                service_counts[service] = service_counts.get(service, 0) + 1
        
        # Get service details
        result = []
        for service_name, count in sorted(service_counts.items(), key=lambda x: x[1], reverse=True):
            cursor.execute("SELECT * FROM services WHERE name = ? LIMIT 1", (service_name,))
            service = cursor.fetchone()
            if service:
                result.append({
                    'name': service_name,
                    'count': count,
                    'price': service['base_price'],
                    'total_revenue': count * service['base_price']
                })
            else:
                result.append({
                    'name': service_name,
                    'count': count,
                    'price': 0,
                    'total_revenue': 0
                })
        
        conn.close()
        return result
    
    def get_daily_revenue(self, days: int = 30) -> List[Dict]:
        """Get daily revenue for the past N days"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        date_from = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        cursor.execute("""
            SELECT DATE(created_at) as date,
                   COUNT(*) as orders,
                   SUM(total_cost) as revenue
            FROM work_orders
            WHERE status = 'completed'
            AND DATE(created_at) >= ?
            GROUP BY DATE(created_at)
            ORDER BY date
        """, (date_from,))
        
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def get_hourly_distribution(self) -> List[Dict]:
        """Get order distribution by hour of day"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT strftime('%H', created_at) as hour,
                   COUNT(*) as count
            FROM work_orders
            GROUP BY hour
            ORDER BY hour
        """)
        
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]


# Singleton instance
db = Database()
