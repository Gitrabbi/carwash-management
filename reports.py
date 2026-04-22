"""
Report Generation Module for Car Wash Management System
Handles export of data to CSV and PDF formats with professional formatting
"""

import pandas as pd
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import io
import base64
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT


class ReportGenerator:
    """
    Professional report generation engine for car wash operations
    Supports multiple report types with both CSV and PDF output formats
    """
    
    def __init__(self, database):
        """Initialize report generator with database connection"""
        self.db = database
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles for reports"""
        self.styles.add(ParagraphStyle(
            name='ReportTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#1a365d')
        ))
        
        self.styles.add(ParagraphStyle(
            name='SectionTitle',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceBefore=20,
            spaceAfter=10,
            textColor=colors.HexColor('#2d3748')
        ))
        
        self.styles.add(ParagraphStyle(
            name='SubTitle',
            parent=self.styles['Normal'],
            fontSize=12,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#718096')
        ))
        
        self.styles.add(ParagraphStyle(
            name='BodyText',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=10,
            alignment=TA_LEFT
        ))
    
    def generate_work_orders_report(self, date_from: str = None, date_to: str = None,
                                   status: str = None, format: str = 'csv') -> Dict:
        """
        Generate comprehensive work orders report
        Includes order details, customer information, services, and financial summary
        """
        # Fetch data
        orders = self.db.get_all_work_orders(status=status, date_from=date_from, date_to=date_to)
        
        if not orders:
            return {'success': False, 'message': 'No orders found for the specified criteria'}
        
        # Prepare DataFrame
        df = pd.DataFrame(orders)
        df['created_at'] = pd.to_datetime(df['created_at']).dt.strftime('%Y-%m-%d %H:%M')
        
        # Select and rename columns for report
        report_df = df[[
            'id', 'customer_name', 'customer_phone', 'vehicle_type',
            'vehicle_make', 'vehicle_model', 'plate_number', 'services',
            'total_cost', 'status', 'assigned_worker_name', 'created_at',
            'started_at', 'ended_at', 'customer_rating'
        ]].copy()
        
        report_df.columns = [
            'Order ID', 'Customer Name', 'Phone', 'Vehicle Type', 'Make', 'Model',
            'Plate Number', 'Services', 'Total (GHS)', 'Status', 'Assigned Worker',
            'Created', 'Started', 'Ended', 'Rating'
        ]
        
        # Calculate summary statistics
        summary = {
            'total_orders': len(report_df),
            'total_revenue': report_df['Total (GHS)'].sum(),
            'avg_order_value': report_df['Total (GHS)'].mean(),
            'completed_orders': len(report_df[report_df['Status'] == 'completed']),
            'pending_orders': len(report_df[report_df['Status'] == 'pending']),
            'in_progress_orders': len(report_df[report_df['Status'] == 'in_progress'])
        }
        
        # Generate report in requested format
        if format == 'csv':
            return self._generate_csv_report(
                report_df, summary, 'Work Orders Report', date_from, date_to
            )
        elif format == 'pdf':
            return self._generate_pdf_report(
                report_df, summary, 'Work Orders Report', date_from, date_to
            )
        else:
            return {'success': False, 'message': 'Unsupported format'}
    
    def generate_worker_performance_report(self, date_from: str = None,
                                           date_to: str = None,
                                           format: str = 'csv') -> Dict:
        """
        Generate detailed worker performance report
        Includes productivity metrics, efficiency scores, and customer ratings
        """
        workers = self.db.get_all_workers(active_only=False)
        performance = self.db.get_worker_performance(date_from, date_to)
        
        if not performance:
            return {'success': False, 'message': 'No worker data found'}
        
        # Prepare DataFrame
        df = pd.DataFrame(performance)
        
        report_df = df[[
            'name', 'role', 'total_orders', 'completed_orders',
            'total_revenue', 'avg_completion_minutes', 'avg_rating'
        ]].copy()
        
        report_df.columns = [
            'Worker Name', 'Role', 'Total Orders', 'Completed Orders',
            'Total Revenue (GHS)', 'Avg Completion Time (min)', 'Avg Rating'
        ]
        
        # Fill NaN values
        report_df = report_df.fillna(0)
        
        # Calculate worker efficiency
        report_df['Efficiency Score'] = (
            (report_df['Completed Orders'] / report_df['Total Orders'] * 100)
        ).round(1)
        
        # Summary statistics
        summary = {
            'total_workers': len(report_df),
            'active_workers': len(workers[workers['is_active'] == 1]) if isinstance(workers, list) else len(workers),
            'total_orders_handled': int(report_df['Total Orders'].sum()),
            'total_revenue_generated': report_df['Total Revenue (GHS)'].sum(),
            'avg_completion_time': report_df['Avg Completion Time (min)'].mean()
        }
        
        if format == 'csv':
            return self._generate_csv_report(
                report_df, summary, 'Worker Performance Report', date_from, date_to
            )
        elif format == 'pdf':
            return self._generate_pdf_report(
                report_df, summary, 'Worker Performance Report', date_from, date_to
            )
        else:
            return {'success': False, 'message': 'Unsupported format'}
    
    def generate_financial_report(self, date_from: str = None,
                                 date_to: str = None,
                                 format: str = 'csv') -> Dict:
        """
        Generate comprehensive financial report
        Includes revenue breakdown, profit analysis, and trends
        """
        orders = self.db.get_all_work_orders(date_from=date_from, date_to=date_to)
        
        if not orders:
            return {'success': False, 'message': 'No financial data found'}
        
        df = pd.DataFrame(orders)
        completed_df = df[df['status'] == 'completed']
        
        # Revenue by status
        revenue_by_status = df.groupby('status')['total_cost'].agg(['sum', 'count']).reset_index()
        revenue_by_status.columns = ['Status', 'Revenue (GHS)', 'Orders']
        
        # Daily revenue analysis
        if 'created_at' in df.columns:
            df['date'] = pd.to_datetime(df['created_at']).dt.date
            daily_revenue = df[df['status'] == 'completed'].groupby('date')['total_cost'].agg(['sum', 'count']).reset_index()
            daily_revenue.columns = ['Date', 'Revenue (GHS)', 'Orders']
        
        # Service revenue breakdown
        all_services = []
        for services_str, cost in zip(df['services'], df['total_cost']):
            services = services_str.split(',')
            for service in services:
                all_services.append({
                    'service': service.strip(),
                    'revenue': cost / len(services)  # Split revenue among services
                })
        
        service_df = pd.DataFrame(all_services).groupby('service')['revenue'].sum().reset_index()
        service_df.columns = ['Service', 'Total Revenue (GHS)']
        service_df = service_df.sort_values('Total Revenue (GHS)', ascending=False)
        
        # Financial summary
        summary = {
            'period_revenue': completed_df['total_cost'].sum() if not completed_df.empty else 0,
            'total_orders': len(df),
            'completed_orders': len(completed_df),
            'cancelled_orders': len(df[df['status'] == 'cancelled']),
            'avg_order_value': df['total_cost'].mean(),
            'avg_completed_value': completed_df['total_cost'].mean() if not completed_df.empty else 0,
            'completion_rate': len(completed_df) / len(df) * 100 if len(df) > 0 else 0
        }
        
        # Create main report DataFrame
        report_df = service_df
        
        if format == 'csv':
            # For CSV, include multiple sheets as separate dictionaries
            return {
                'success': True,
                'format': 'csv',
                'main_report': self._create_csv_string(report_df),
                'revenue_by_status': self._create_csv_string(revenue_by_status),
                'daily_revenue': self._create_csv_string(daily_revenue) if 'daily_revenue' in dir() else None,
                'summary': summary,
                'filename': f'financial_report_{datetime.now().strftime("%Y%m%d")}'
            }
        elif format == 'pdf':
            return self._generate_financial_pdf(
                report_df, revenue_by_status, summary, date_from, date_to
            )
        else:
            return {'success': False, 'message': 'Unsupported format'}
    
    def generate_attendance_report(self, worker_id: str = None,
                                   date_from: str = None,
                                   date_to: str = None,
                                   format: str = 'csv') -> Dict:
        """
        Generate worker attendance report
        Includes check-in/out times, absences, and overtime
        """
        attendance = self.db.get_attendance_records(worker_id, date_from, date_to)
        
        if not attendance:
            return {'success': False, 'message': 'No attendance records found'}
        
        df = pd.DataFrame(attendance)
        
        # Calculate work hours
        if 'check_in' in df.columns and 'check_out' in df.columns:
            df['check_in_dt'] = pd.to_datetime(df['check_in'], errors='coerce')
            df['check_out_dt'] = pd.to_datetime(df['check_out'], errors='coerce')
            df['hours_worked'] = (
                (df['check_out_dt'] - df['check_in_dt']).dt.total_seconds() / 3600
            ).fillna(0)
        
        # Get worker names
        workers = self.db.get_all_workers(active_only=False)
        worker_dict = {w['id']: w['name'] for w in workers}
        df['worker_name'] = df['worker_id'].map(worker_dict)
        
        report_df = df[[
            'worker_name', 'date', 'check_in', 'check_out',
            'hours_worked', 'status', 'notes'
        ]].copy()
        
        report_df.columns = [
            'Worker Name', 'Date', 'Check In', 'Check Out',
            'Hours Worked', 'Status', 'Notes'
        ]
        
        # Summary statistics
        summary = {
            'total_records': len(report_df),
            'present_days': len(report_df[report_df['Status'] == 'present']),
            'absent_days': len(report_df[report_df['Status'] == 'absent']),
            'total_hours': report_df['Hours Worked'].sum(),
            'avg_hours_per_day': report_df['Hours Worked'].mean()
        }
        
        if format == 'csv':
            return self._generate_csv_report(
                report_df, summary, 'Attendance Report', date_from, date_to
            )
        elif format == 'pdf':
            return self._generate_pdf_report(
                report_df, summary, 'Attendance Report', date_from, date_to
            )
        else:
            return {'success': False, 'message': 'Unsupported format'}
    
    def generate_daily_summary_report(self, date: str = None,
                                      format: str = 'pdf') -> Dict:
        """
        Generate daily operations summary
        Quick overview of daily activity for management review
        """
        date = date or datetime.now().strftime('%Y-%m-%d')
        
        # Get all data for the date
        orders = self.db.get_all_work_orders(date_from=date, date_to=date)
        workers = self.db.get_all_workers()
        attendance = self.db.get_attendance_records(date_from=date, date_to=date)
        
        # Calculate daily metrics
        df = pd.DataFrame(orders) if orders else pd.DataFrame()
        
        if df.empty:
            return {'success': False, 'message': f'No data found for {date}'}
        
        daily_stats = {
            'date': date,
            'total_orders': len(df),
            'pending': len(df[df['status'] == 'pending']),
            'in_progress': len(df[df['status'] == 'in_progress']),
            'completed': len(df[df['status'] == 'completed']),
            'cancelled': len(df[df['status'] == 'cancelled']),
            'revenue': df[df['status'] == 'completed']['total_cost'].sum(),
            'avg_order_value': df[df['status'] == 'completed']['total_cost'].mean() if len(df[df['status'] == 'completed']) > 0 else 0
        }
        
        # Worker summary
        workers_present = len([a for a in attendance if a.get('status') == 'present'])
        
        if format == 'pdf':
            return self._generate_daily_summary_pdf(daily_stats, workers_present, workers)
        elif format == 'csv':
            return self._generate_csv_report(
                pd.DataFrame([daily_stats]), daily_stats, f'Daily Summary - {date}', date, date
            )
        else:
            return {'success': False, 'message': 'Unsupported format'}
    
    def _generate_csv_report(self, df: pd.DataFrame, summary: Dict,
                            title: str, date_from: str, date_to: str) -> Dict:
        """Generate CSV report with embedded metadata"""
        # Add metadata rows
        metadata = pd.DataFrame([
            {'Report': title},
            {'Period': f"{date_from or 'All time'} to {date_to or 'Present'}"},
            {'Generated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')},
            {'': ''}
        ])
        
        summary_df = pd.DataFrame([summary])
        
        # Combine all
        csv_data = pd.concat([metadata, summary_df, df], ignore_index=True)
        
        return {
            'success': True,
            'format': 'csv',
            'data': self._create_csv_string(csv_data),
            'filename': f'{title.lower().replace(" ", "_")}_{datetime.now().strftime("%Y%m%d")}'
        }
    
    def _create_csv_string(self, df: pd.DataFrame) -> str:
        """Convert DataFrame to CSV string"""
        return df.to_csv(index=False)
    
    def _generate_pdf_report(self, df: pd.DataFrame, summary: Dict,
                            title: str, date_from: str, date_to: str) -> Dict:
        """Generate professional PDF report"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, 
                               leftMargin=cm, rightMargin=cm,
                               topMargin=cm, bottomMargin=cm)
        
        elements = []
        
        # Title
        elements.append(Paragraph(title, self.styles['ReportTitle']))
        elements.append(Paragraph(
            f"Period: {date_from or 'Beginning'} to {date_to or 'Present'}",
            self.styles['SubTitle']
        ))
        elements.append(Paragraph(
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            self.styles['SubTitle']
        ))
        elements.append(Spacer(1, 20))
        
        # Summary section
        elements.append(Paragraph("Summary", self.styles['SectionTitle']))
        
        summary_data = [[key.replace('_', ' ').title(), str(value)] 
                        for key, value in summary.items()]
        
        summary_table = Table(summary_data, colWidths=[4*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f7fafc')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2d3748')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0'))
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 20))
        
        # Data table
        elements.append(Paragraph("Detailed Data", self.styles['SectionTitle']))
        
        # Prepare table data
        table_data = [list(df.columns)]
        for _, row in df.iterrows():
            table_data.append([str(val) if pd.notna(val) else '' for val in row.values])
        
        # Create table
        col_count = len(df.columns)
        col_width = (doc.width - 1*inch) / col_count
        table = Table(table_data, colWidths=[col_width] * col_count)
        
        table.setStyle(TableStyle([
            # Header styling
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d3748')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            
            # Body styling
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#2d3748')),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            
            # Grid
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fafc')])
        ]))
        
        elements.append(table)
        
        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        
        # Convert to base64 for transport
        pdf_base64 = base64.b64encode(buffer.read()).decode()
        
        return {
            'success': True,
            'format': 'pdf',
            'data': pdf_base64,
            'filename': f'{title.lower().replace(" ", "_")}_{datetime.now().strftime("%Y%m%d")}.pdf'
        }
    
    def _generate_financial_pdf(self, service_df: pd.DataFrame,
                               revenue_by_status: pd.DataFrame,
                               summary: Dict,
                               date_from: str, date_to: str) -> Dict:
        """Generate specialized financial PDF report"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4,
                               leftMargin=cm, rightMargin=cm)
        
        elements = []
        
        # Title
        elements.append(Paragraph("Financial Report", self.styles['ReportTitle']))
        elements.append(Paragraph(
            f"Period: {date_from or 'Beginning'} to {date_to or 'Present'}",
            self.styles['SubTitle']
        ))
        elements.append(Spacer(1, 20))
        
        # Key metrics
        elements.append(Paragraph("Key Financial Metrics", self.styles['SectionTitle']))
        
        metrics_data = [
            ['Total Revenue', f"GHS {summary.get('period_revenue', 0):,.2f}"],
            ['Total Orders', str(summary.get('total_orders', 0))],
            ['Completed Orders', str(summary.get('completed_orders', 0))],
            ['Cancelled Orders', str(summary.get('cancelled_orders', 0))],
            ['Average Order Value', f"GHS {summary.get('avg_order_value', 0):,.2f}"],
            ['Average Completed Value', f"GHS {summary.get('avg_completed_value', 0):,.2f}"],
            ['Completion Rate', f"{summary.get('completion_rate', 0):.1f}%"]
        ]
        
        metrics_table = Table(metrics_data, colWidths=[3*inch, 2*inch])
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f7fafc')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2d3748')),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0'))
        ]))
        elements.append(metrics_table)
        elements.append(Spacer(1, 20))
        
        # Revenue by status
        elements.append(Paragraph("Revenue by Order Status", self.styles['SectionTitle']))
        
        status_table_data = [['Status', 'Revenue (GHS)', 'Orders']]
        for _, row in revenue_by_status.iterrows():
            status_table_data.append([
                row['Status'].title(),
                f"{row['Revenue (GHS)']:,.2f}",
                str(row['Orders'])
            ])
        
        status_table = Table(status_table_data, colWidths=[2*inch, 2*inch, 1.5*inch])
        status_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d3748')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fafc')])
        ]))
        elements.append(status_table)
        elements.append(Spacer(1, 20))
        
        # Service revenue breakdown
        elements.append(Paragraph("Revenue by Service", self.styles['SectionTitle']))
        
        service_table_data = [['Service', 'Revenue (GHS)']] + [
            [row['Service'], f"{row['Total Revenue (GHS)']:,.2f}"]
            for _, row in service_df.head(10).iterrows()
        ]
        
        service_table = Table(service_table_data, colWidths=[4*inch, 2*inch])
        service_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d3748')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fafc')])
        ]))
        elements.append(service_table)
        
        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        
        pdf_base64 = base64.b64encode(buffer.read()).decode()
        
        return {
            'success': True,
            'format': 'pdf',
            'data': pdf_base64,
            'filename': f'financial_report_{datetime.now().strftime("%Y%m%d")}.pdf'
        }
    
    def _generate_daily_summary_pdf(self, stats: Dict, workers_present: int,
                                    all_workers: List) -> Dict:
        """Generate daily summary PDF for quick management review"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        
        elements = []
        
        # Title
        elements.append(Paragraph(
            f"Daily Operations Summary",
            self.styles['ReportTitle']
        ))
        elements.append(Paragraph(
            f"Date: {stats['date']}",
            self.styles['SubTitle']
        ))
        elements.append(Spacer(1, 30))
        
        # Order statistics
        elements.append(Paragraph("Order Statistics", self.styles['SectionTitle']))
        
        order_data = [
            ['Metric', 'Value'],
            ['Total Orders', str(stats['total_orders'])],
            ['Pending', str(stats['pending'])],
            ['In Progress', str(stats['in_progress'])],
            ['Completed', str(stats['completed'])],
            ['Cancelled', str(stats['cancelled'])],
            ['Today\'s Revenue', f"GHS {stats['revenue']:,.2f}"],
            ['Average Order Value', f"GHS {stats['avg_order_value']:,.2f}"]
        ]
        
        order_table = Table(order_data, colWidths=[3*inch, 2*inch])
        order_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d3748')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
            ('BACKGROUND', (0, 6), (-1, 6), colors.HexColor('#c6f6d5')),  # Highlight revenue
            ('BACKGROUND', (0, 7), (-1, 7), colors.HexColor('#e9d8fd'))   # Highlight avg
        ]))
        elements.append(order_table)
        elements.append(Spacer(1, 30))
        
        # Staff summary
        elements.append(Paragraph("Staff Summary", self.styles['SectionTitle']))
        
        staff_data = [
            ['Metric', 'Value'],
            ['Workers On Duty', f"{workers_present} / {len(all_workers)}"],
            ['Staff Utilization', f"{workers_present/len(all_workers)*100:.0f}%" if all_workers else "N/A"]
        ]
        
        staff_table = Table(staff_data, colWidths=[3*inch, 2*inch])
        staff_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d3748')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0'))
        ]))
        elements.append(staff_table)
        
        # Footer
        elements.append(Spacer(1, 50))
        elements.append(Paragraph(
            f"Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            self.styles['SubTitle']
        ))
        
        doc.build(elements)
        buffer.seek(0)
        
        pdf_base64 = base64.b64encode(buffer.read()).decode()
        
        return {
            'success': True,
            'format': 'pdf',
            'data': pdf_base64,
            'filename': f'daily_summary_{stats["date"]}.pdf'
        }
    
    def get_download_link(self, report_data: Dict) -> Optional[str]:
        """Generate HTML download link for report"""
        if not report_data.get('success'):
            return None
        
        if report_data['format'] == 'csv':
            href = f"data:text/csv;base64,{base64.b64encode(report_data['data'].encode()).decode()}"
        elif report_data['format'] == 'pdf':
            href = f"data:application/pdf;base64,{report_data['data']}"
        else:
            return None
        
        filename = report_data['filename']
        return f'<a href="{href}" download="{filename}" class="btn">Download {report_data["format"].upper()}</a>'
