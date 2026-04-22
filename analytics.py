"""
Analytics and AI Analysis Module for Car Wash Management System
Provides advanced analytics, insights, and predictions for business optimization
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
import json


class CarWashAnalytics:
    """
    Advanced analytics engine for car wash operations
    Provides AI-powered insights for worker performance, customer behavior, and operational efficiency
    """
    
    def __init__(self, database):
        """Initialize analytics with database connection"""
        self.db = database
    
    def analyze_worker_attendance(self, worker_id: str = None, 
                                   date_from: str = None, 
                                   date_to: str = None) -> Dict:
        """
        Comprehensive worker attendance analysis with patterns and predictions
        Analyzes check-in/check-out times, punctuality, overtime patterns, and predicted availability
        """
        attendance_records = self.db.get_attendance_records(worker_id, date_from, date_to)
        
        if not attendance_records:
            return {
                'summary': 'No attendance data available for the selected period',
                'metrics': {},
                'patterns': {},
                'recommendations': []
            }
        
        df = pd.DataFrame(attendance_records)
        
        # Calculate basic metrics
        total_days = len(df)
        present_days = len(df[df['status'] == 'present'])
        absent_days = len(df[df['status'] == 'absent'])
        late_arrivals = len(df[df['check_in'].notna()])
        
        # Calculate average check-in time
        if 'check_in' in df.columns:
            df['check_in_time'] = pd.to_datetime(df['check_in'], errors='coerce')
            avg_check_in = df['check_in_time'].mean()
            earliest_check_in = df['check_in_time'].min()
            latest_check_in = df['check_in_time'].max()
        else:
            avg_check_in = earliest_check_in = latest_check_in = None
        
        # Calculate work hours
        if 'check_in' in df.columns and 'check_out' in df.columns:
            df['work_hours'] = (pd.to_datetime(df['check_out'], errors='coerce') - 
                               pd.to_datetime(df['check_in'], errors='coerce')).dt.total_seconds() / 3600
            avg_work_hours = df['work_hours'].mean()
            total_work_hours = df['work_hours'].sum()
        else:
            avg_work_hours = total_work_hours = 0
        
        # Detect attendance patterns
        patterns = self._detect_attendance_patterns(df)
        
        # Generate predictions and recommendations
        predictions = self._predict_attendance_trends(df)
        recommendations = self._generate_attendance_recommendations(
            present_days, total_days, avg_check_in, patterns
        )
        
        return {
            'summary': f"Analyzed {total_days} days of attendance records",
            'metrics': {
                'total_days_analyzed': total_days,
                'days_present': present_days,
                'days_absent': absent_days,
                'attendance_rate': round((present_days / total_days * 100), 2) if total_days > 0 else 0,
                'avg_check_in_time': avg_check_in.strftime("%H:%M") if avg_check_in else "N/A",
                'earliest_check_in': earliest_check_in.strftime("%H:%M") if earliest_check_in else "N/A",
                'latest_check_in': latest_check_in.strftime("%H:%M") if latest_check_in else "N/A",
                'avg_work_hours': round(avg_work_hours, 2) if avg_work_hours else 0,
                'total_work_hours': round(total_work_hours, 2)
            },
            'patterns': patterns,
            'predictions': predictions,
            'recommendations': recommendations
        }
    
    def _detect_attendance_patterns(self, df: pd.DataFrame) -> Dict:
        """Detect recurring patterns in attendance data"""
        patterns = {}
        
        # Day of week analysis
        if 'date' in df.columns:
            df['day_of_week'] = pd.to_datetime(df['date']).dt.day_name()
            day_counts = df['day_of_week'].value_counts()
            patterns['most_active_days'] = day_counts.to_dict()
        
        # Time-based patterns
        if 'check_in_time' in df.columns and not df['check_in_time'].isna().all():
            df['hour'] = df['check_in_time'].dt.hour
            hour_counts = df['hour'].value_counts()
            patterns['common_check_in_hours'] = hour_counts.head(3).to_dict()
        
        # Trend analysis (comparing recent vs older records)
        if len(df) >= 10:
            midpoint = len(df) // 2
            older = df.iloc[:midpoint]
            newer = df.iloc[midpoint:]
            
            older_rate = len(older[older['status'] == 'present']) / len(older) * 100
            newer_rate = len(newer[newer['status'] == 'present']) / len(newer) * 100
            
            if newer_rate > older_rate + 5:
                patterns['trend'] = 'improving'
            elif newer_rate < older_rate - 5:
                patterns['trend'] = 'declining'
            else:
                patterns['trend'] = 'stable'
        
        return patterns
    
    def _predict_attendance_trends(self, df: pd.DataFrame) -> Dict:
        """Simple prediction model for attendance trends"""
        predictions = {}
        
        if len(df) >= 7:
            # Calculate rolling average attendance rate
            df_sorted = df.sort_values('date')
            df_sorted['is_present'] = (df_sorted['status'] == 'present').astype(int)
            df_sorted['rolling_avg'] = df_sorted['is_present'].rolling(window=7, min_periods=1).mean()
            
            current_trend = df_sorted['rolling_avg'].iloc[-1]
            predictions['next_week_probability'] = round(current_trend * 100, 1)
            
            # Detect if trend is increasing or decreasing
            if len(df_sorted) >= 14:
                recent_avg = df_sorted['is_present'].iloc[-7:].mean()
                older_avg = df_sorted['is_present'].iloc[:-7].mean()
                predictions['trend_direction'] = 'increasing' if recent_avg > older_avg else 'decreasing'
        
        return predictions
    
    def _generate_attendance_recommendations(self, present_days: int, total_days: int,
                                             avg_check_in, patterns: Dict) -> List[str]:
        """Generate actionable recommendations based on attendance analysis"""
        recommendations = []
        
        attendance_rate = (present_days / total_days * 100) if total_days > 0 else 0
        
        if attendance_rate < 80:
            recommendations.append(
                f"Attendance rate ({attendance_rate:.1f}%) is below target. Consider implementing "
                "an attendance incentive program to boost worker engagement and reliability."
            )
        
        if avg_check_in:
            check_in_hour = avg_check_in.hour if hasattr(avg_check_in, 'hour') else 8
            if check_in_hour >= 9:
                recommendations.append(
                    f"Average check-in time ({avg_check_in.strftime('%H:%M')}) is later than ideal. "
                    "Consider flexible start times or morning shift adjustments."
                )
        
        if patterns.get('trend') == 'declining':
            recommendations.append(
                "Attendance trend is declining. Schedule one-on-one meetings with workers "
                "to identify underlying issues and improve morale."
            )
        
        if not recommendations:
            recommendations.append(
                "Excellent attendance performance! Continue current practices and "
                "consider recognizing high-performing workers."
            )
        
        return recommendations
    
    def analyze_worker_time_performance(self, worker_id: str = None,
                                        date_from: str = None,
                                        date_to: str = None) -> Dict:
        """
        Analyze time spent on jobs by workers
        Calculates average completion times, efficiency metrics, and provides optimization suggestions
        """
        work_orders = self.db.get_all_work_orders(worker_id=worker_id, date_from=date_from, date_to=date_to)
        
        if not work_orders:
            return {
                'summary': 'No completed work orders found for analysis',
                'metrics': {},
                'efficiency_scores': {},
                'recommendations': []
            }
        
        df = pd.DataFrame(work_orders)
        
        # Filter to completed orders with both start and end times
        completed_df = df[
            (df['status'] == 'completed') & 
            (df['started_at'].notna()) & 
            (df['ended_at'].notna())
        ].copy()
        
        if completed_df.empty:
            return {
                'summary': 'No completed orders with time tracking data available',
                'metrics': {},
                'efficiency_scores': {},
                'recommendations': []
            }
        
        # Calculate completion times in minutes
        completed_df['started_dt'] = pd.to_datetime(completed_df['started_at'])
        completed_df['ended_dt'] = pd.to_datetime(completed_df['ended_at'])
        completed_df['completion_minutes'] = (
            (completed_df['ended_dt'] - completed_df['started_dt']).dt.total_seconds() / 60
        )
        
        # Calculate service complexity (number of services)
        completed_df['service_count'] = completed_df['services'].str.count(',') + 1
        
        # Individual worker metrics
        if worker_id:
            worker_orders = completed_df[completed_df['assigned_worker_id'] == worker_id]
            metrics = self._calculate_time_metrics(worker_orders)
        else:
            metrics = self._calculate_aggregate_metrics(completed_df)
        
        # Calculate efficiency scores
        efficiency_scores = self._calculate_efficiency_scores(completed_df)
        
        # Generate service time benchmarks
        benchmarks = self._calculate_service_benchmarks(completed_df)
        
        # Generate recommendations
        recommendations = self._generate_time_recommendations(
            completed_df, efficiency_scores, metrics
        )
        
        return {
            'summary': f"Analyzed {len(completed_df)} completed work orders",
            'metrics': metrics,
            'benchmarks': benchmarks,
            'efficiency_scores': efficiency_scores,
            'recommendations': recommendations,
            'time_distribution': self._get_time_distribution(completed_df)
        }
    
    def _calculate_time_metrics(self, df: pd.DataFrame) -> Dict:
        """Calculate time metrics for a single worker or aggregate"""
        if df.empty:
            return {}
        
        metrics = {
            'total_orders': len(df),
            'avg_completion_time': round(df['completion_minutes'].mean(), 1),
            'median_completion_time': round(df['completion_minutes'].median(), 1),
            'min_completion_time': round(df['completion_minutes'].min(), 1),
            'max_completion_time': round(df['completion_minutes'].max(), 1),
            'std_deviation': round(df['completion_minutes'].std(), 1),
            'total_hours_worked': round(df['completion_minutes'].sum() / 60, 2),
            'avg_services_per_order': round(df['service_count'].mean(), 1)
        }
        
        # Calculate time per service
        metrics['avg_minutes_per_service'] = round(
            metrics['avg_completion_time'] / metrics['avg_services_per_order'], 1
        )
        
        return metrics
    
    def _calculate_aggregate_metrics(self, df: pd.DataFrame) -> Dict:
        """Calculate aggregate metrics across all workers"""
        by_worker = df.groupby('assigned_worker_id').agg({
            'completion_minutes': ['mean', 'count', 'std'],
            'total_cost': 'sum',
            'service_count': 'mean'
        }).round(2)
        
        return {
            'by_worker': by_worker.to_dict(),
            'overall_avg': round(df['completion_minutes'].mean(), 1),
            'total_orders': len(df),
            'total_hours': round(df['completion_minutes'].sum() / 60, 2)
        }
    
    def _calculate_efficiency_scores(self, df: pd.DataFrame) -> Dict:
        """Calculate efficiency scores for each worker"""
        if df.empty:
            return {}
        
        worker_stats = df.groupby('assigned_worker_id').agg({
            'completion_minutes': 'mean',
            'service_count': 'mean',
            'total_cost': 'sum',
            'customer_rating': 'mean'
        }).round(2)
        
        # Calculate efficiency score (lower time = higher efficiency)
        avg_time = worker_stats['completion_minutes'].mean()
        worker_stats['efficiency_score'] = (
            (avg_time / worker_stats['completion_minutes']) * 100
        ).round(1)
        
        # Get worker names
        workers = self.db.get_all_workers(active_only=False)
        worker_names = {w['id']: w['name'] for w in workers}
        
        return {
            worker_id: {
                'name': worker_names.get(worker_id, 'Unknown'),
                'avg_completion_time': round(row['completion_minutes'], 1),
                'orders_completed': int(row['service_count'] * 0),  # Placeholder
                'total_revenue': round(row['total_cost'], 2),
                'avg_rating': round(row['customer_rating'], 1) if pd.notna(row['customer_rating']) else None,
                'efficiency_score': round(row['efficiency_score'], 1)
            }
            for worker_id, row in worker_stats.iterrows()
        }
    
    def _calculate_service_benchmarks(self, df: pd.DataFrame) -> Dict:
        """Calculate average time benchmarks for each service type"""
        benchmarks = {}
        
        for service in df['services'].str.split(',').explode().unique():
            service_orders = df[df['services'].str.contains(service.strip())]
            benchmarks[service.strip()] = {
                'avg_time': round(service_orders['completion_minutes'].mean(), 1),
                'min_time': round(service_orders['completion_minutes'].min(), 1),
                'max_time': round(service_orders['completion_minutes'].max(), 1),
                'order_count': len(service_orders)
            }
        
        return benchmarks
    
    def _get_time_distribution(self, df: pd.DataFrame) -> Dict:
        """Get distribution of completion times"""
        if df.empty:
            return {}
        
        percentiles = [25, 50, 75, 90]
        distribution = {
            f'p{p}': round(df['completion_minutes'].quantile(p/100), 1)
            for p in percentiles
        }
        
        # Create histogram bins
        bins = [0, 30, 60, 90, 120, 180, float('inf')]
        labels = ['0-30min', '30-60min', '60-90min', '90-120min', '2-3hrs', '3hrs+']
        df['time_bin'] = pd.cut(df['completion_minutes'], bins=bins, labels=labels)
        
        distribution['histogram'] = df['time_bin'].value_counts().to_dict()
        
        return distribution
    
    def _generate_time_recommendations(self, df: pd.DataFrame,
                                       efficiency_scores: Dict,
                                       metrics: Dict) -> List[str]:
        """Generate recommendations based on time analysis"""
        recommendations = []
        
        if df.empty:
            return ["No data available for recommendations"]
        
        avg_time = df['completion_minutes'].mean()
        std_time = df['completion_minutes'].std()
        
        # Identify outliers
        outliers = df[df['completion_minutes'] > avg_time + 2*std_time]
        if len(outliers) > 0:
            recommendations.append(
                f"Identified {len(outliers)} orders taking significantly longer than average. "
                "Review these orders for process improvements or worker training needs."
            )
        
        # Identify top performers
        if efficiency_scores:
            sorted_workers = sorted(
                efficiency_scores.items(),
                key=lambda x: x[1].get('efficiency_score', 0),
                reverse=True
            )
            
            if sorted_workers:
                top_worker = sorted_workers[0][1]
                recommendations.append(
                    f"{top_worker['name']} is the most efficient worker with an efficiency score of "
                    f"{top_worker['efficiency_score']:.1f}. Consider having them mentor other workers."
                )
            
            # Identify workers needing improvement
            low_performers = [
                (wid, data) for wid, data in sorted_workers
                if data.get('efficiency_score', 100) < 80
            ]
            
            if low_performers:
                names = [f"{data['name']} ({data['efficiency_score']:.1f})" 
                        for _, data in low_performers[:3]]
                recommendations.append(
                    f"Workers {', '.join(names)} could benefit from additional training "
                    "to improve their time efficiency."
                )
        
        # Service-based recommendations
        service_times = df.groupby('services')['completion_minutes'].mean()
        slow_services = service_times[service_times > avg_time].head(3)
        
        if not slow_services.empty:
            recommendations.append(
                f"Services taking longer than average: {', '.join(slow_services.index[:3].tolist())}. "
                "Consider breaking these into smaller tasks or providing additional resources."
            )
        
        if not recommendations:
            recommendations.append(
                "Current time performance is within acceptable ranges. Continue monitoring "
                "for any deviations from established benchmarks."
            )
        
        return recommendations
    
    def analyze_customer_experience(self, date_from: str = None,
                                   date_to: str = None) -> Dict:
        """
        Analyze customer experience through ratings, feedback, and order patterns
        Provides insights for improving customer satisfaction and retention
        """
        work_orders = self.db.get_all_work_orders(date_from=date_from, date_to=date_to)
        
        if not work_orders:
            return {
                'summary': 'No customer feedback data available',
                'metrics': {},
                'sentiment_analysis': {},
                'recommendations': []
            }
        
        df = pd.DataFrame(work_orders)
        
        # Filter orders with customer feedback
        feedback_df = df[
            (df['customer_rating'].notna()) | 
            (df['customer_feedback'].notna())
        ].copy()
        
        metrics = self._calculate_customer_metrics(df, feedback_df)
        patterns = self._detect_customer_patterns(df, feedback_df)
        sentiment = self._analyze_feedback_sentiment(feedback_df)
        predictions = self._predict_customer_behavior(df)
        recommendations = self._generate_customer_recommendations(
            metrics, patterns, sentiment
        )
        
        return {
            'summary': f"Analyzed feedback from {len(feedback_df)} orders out of {len(df)} total",
            'metrics': metrics,
            'patterns': patterns,
            'sentiment_analysis': sentiment,
            'predictions': predictions,
            'recommendations': recommendations
        }
    
    def _calculate_customer_metrics(self, df: pd.DataFrame, feedback_df: pd.DataFrame) -> Dict:
        """Calculate customer satisfaction metrics"""
        completed_df = df[df['status'] == 'completed']
        
        metrics = {
            'total_orders': len(df),
            'completed_orders': len(completed_df),
            'completion_rate': round(len(completed_df) / len(df) * 100, 1) if len(df) > 0 else 0,
            'feedback_count': len(feedback_df),
            'feedback_rate': round(len(feedback_df) / len(completed_df) * 100, 1) if len(completed_df) > 0 else 0
        }
        
        if not feedback_df.empty and 'customer_rating' in feedback_df.columns:
            ratings = feedback_df['customer_rating'].dropna()
            if len(ratings) > 0:
                metrics['avg_rating'] = round(ratings.mean(), 2)
                metrics['rating_distribution'] = ratings.value_counts().to_dict()
                metrics['five_star_rate'] = round(
                    len(ratings[ratings == 5]) / len(ratings) * 100, 1
                )
                metrics['low_rating_count'] = len(ratings[ratings <= 2])
        
        return metrics
    
    def _detect_customer_patterns(self, df: pd.DataFrame, feedback_df: pd.DataFrame) -> Dict:
        """Detect patterns in customer behavior"""
        patterns = {}
        
        # Repeat customers
        customer_orders = df.groupby('customer_name').size()
        repeat_customers = customer_orders[customer_orders > 1]
        patterns['repeat_customer_rate'] = round(
            len(repeat_customers) / len(customer_orders) * 100, 1
        ) if len(customer_orders) > 0 else 0
        
        # Average order value by customer
        avg_order_value = df.groupby('customer_name')['total_cost'].mean()
        patterns['avg_order_value'] = round(avg_order_value.mean(), 2)
        
        # Service preferences
        all_services = df['services'].str.split(',').explode().str.strip()
        patterns['most_popular_services'] = all_services.value_counts().head(5).to_dict()
        
        # Peak hours for customer arrivals
        if 'created_at' in df.columns:
            df['hour'] = pd.to_datetime(df['created_at']).dt.hour
            peak_hours = df['hour'].value_counts().head(3)
            patterns['peak_service_hours'] = {
                f"{hour}:00": count for hour, count in peak_hours.items()
            }
        
        return patterns
    
    def _analyze_feedback_sentiment(self, feedback_df: pd.DataFrame) -> Dict:
        """Perform basic sentiment analysis on customer feedback"""
        if feedback_df.empty or 'customer_feedback' not in feedback_df.columns:
            return {'summary': 'No text feedback available for analysis'}
        
        # Filter to non-empty feedback
        text_feedback = feedback_df[
            feedback_df['customer_feedback'].notna() & 
            (feedback_df['customer_feedback'].str.len() > 0)
        ]['customer_feedback'].tolist()
        
        if not text_feedback:
            return {'summary': 'No text feedback available for analysis'}
        
        # Simple keyword-based sentiment
        positive_keywords = ['great', 'excellent', 'amazing', 'good', 'fast', 'professional', 
                           'friendly', 'recommend', 'love', 'perfect', 'best', 'satisfied']
        negative_keywords = ['bad', 'slow', 'poor', 'terrible', 'worst', 'disappointed', 
                            'rude', 'expensive', 'problem', 'issue', 'unhappy', 'never']
        
        positive_count = sum(
            1 for text in text_feedback 
            if any(kw in text.lower() for kw in positive_keywords)
        )
        negative_count = sum(
            1 for text in text_feedback 
            if any(kw in text.lower() for kw in negative_keywords)
        )
        
        total = len(text_feedback)
        sentiment_score = ((positive_count - negative_count) / total * 100) if total > 0 else 0
        
        return {
            'summary': f"Analyzed {total} text reviews",
            'positive_reviews': positive_count,
            'negative_reviews': negative_count,
            'neutral_reviews': total - positive_count - negative_count,
            'sentiment_score': round(sentiment_score, 1),
            'sample_feedback': text_feedback[:3]  # Return sample for reference
        }
    
    def _predict_customer_behavior(self, df: pd.DataFrame) -> Dict:
        """Predict customer behavior patterns"""
        predictions = {}
        
        if len(df) < 10:
            return {'summary': 'Insufficient data for predictions'}
        
        # Customer retention prediction
        customer_orders = df.groupby('customer_name').agg({
            'id': 'count',
            'total_cost': ['sum', 'mean'],
            'status': lambda x: (x == 'completed').sum()
        })
        
        active_customers = len(customer_orders[customer_orders[('id', 'count')] >= 2])
        churned_customers = len(customer_orders[customer_orders[('status', '<lambda_0>')] == 0])
        
        predictions['customer_retention_rate'] = round(
            active_customers / len(customer_orders) * 100, 1
        ) if len(customer_orders) > 0 else 0
        
        # Order frequency prediction
        if len(df) >= 30:
            recent_orders = df.tail(30)
            avg_daily_orders = len(recent_orders) / 30
            predictions['predicted_daily_orders'] = round(avg_daily_orders, 1)
        
        return predictions
    
    def _generate_customer_recommendations(self, metrics: Dict, patterns: Dict,
                                          sentiment: Dict) -> List[str]:
        """Generate recommendations for improving customer experience"""
        recommendations = []
        
        # Rating-based recommendations
        if metrics.get('avg_rating', 0) < 4.0:
            recommendations.append(
                f"Average rating ({metrics.get('avg_rating', 0)}) could be improved. Focus on "
                
                "service quality consistency and customer interaction training."
            )
        
        if metrics.get('low_rating_count', 0) > 0:
            recommendations.append(
                f"Received {metrics['low_rating_count']} low ratings (2 or below). "
                "Review these orders individually to identify specific issues."
            )
        
        # Feedback-based recommendations
        if isinstance(sentiment, dict) and sentiment.get('sentiment_score', 0) < 0:
            recommendations.append(
                "Negative sentiment detected in customer feedback. Consider implementing "
                "a follow-up process for dissatisfied customers."
            )
        
        # Pattern-based recommendations
        if patterns.get('repeat_customer_rate', 0) < 30:
            recommendations.append(
                "Low repeat customer rate suggests opportunities for loyalty programs "
                "or targeted marketing to encourage return visits."
            )
        
        # Peak hour recommendations
        if patterns.get('peak_service_hours'):
            peak = list(patterns['peak_service_hours'].keys())[0]
            recommendations.append(
                f"Peak service hour is {peak}. Consider adding staff during this time "
                "to reduce wait times and improve customer satisfaction."
            )
        
        if not recommendations:
            recommendations.append(
                "Customer experience metrics are positive. Continue excellent service "
                "and consider a referral program to leverage satisfied customers."
            )
        
        return recommendations
    
    def generate_business_insights(self, date_from: str = None,
                                  date_to: str = None) -> Dict:
        """
        Generate comprehensive business insights combining all analytics
        Provides executive-level summary and strategic recommendations
        """
        # Gather all data
        order_stats = self.db.get_order_statistics(date_from, date_to)
        worker_performance = self.db.get_worker_performance(date_from, date_to)
        service_popularity = self.db.get_service_popularity(date_from, date_to)
        daily_revenue = self.db.get_daily_revenue(days=30)
        
        insights = {
            'executive_summary': self._generate_executive_summary(order_stats, worker_performance),
            'key_metrics': order_stats,
            'top_performers': self._get_top_performers(worker_performance),
            'revenue_trends': self._analyze_revenue_trends(daily_revenue),
            'strategic_recommendations': self._generate_strategic_recommendations(
                order_stats, worker_performance, service_popularity
            )
        }
        
        return insights
    
    def _generate_executive_summary(self, stats: Dict, workers: List[Dict]) -> str:
        """Generate executive-level summary"""
        total = stats.get('total_orders', 0)
        revenue = stats.get('total_revenue', 0)
        today_rev = stats.get('today_revenue', 0)
        completion_rate = (
            stats.get('by_status', {}).get('completed', {}).get('count', 0) / total * 100
            if total > 0 else 0
        )
        
        # Find most productive worker
        top_worker = max(workers, key=lambda w: w.get('completed_orders', 0)) if workers else None
        
        summary = f"""
        This period recorded {total} work orders generating GHS {revenue:,.2f} in total revenue.
        Today's revenue stands at GHS {today_rev:,.2f} with a {completion_rate:.1f}% completion rate.
        """
        
        if top_worker and top_worker.get('name'):
            summary += f" {top_worker['name']} leads in completed orders."
        
        return summary.strip()
    
    def _get_top_performers(self, workers: List[Dict]) -> List[Dict]:
        """Identify top performing workers"""
        if not workers:
            return []
        
        sorted_workers = sorted(workers, 
                               key=lambda w: w.get('total_revenue', 0), 
                               reverse=True)
        
        return [
            {
                'name': w['name'],
                'role': w['role'],
                'orders_completed': w.get('completed_orders', 0),
                'revenue': round(w.get('total_revenue', 0), 2),
                'avg_rating': round(w.get('avg_rating', 0), 1) if w.get('avg_rating') else None
            }
            for w in sorted_workers[:5]
        ]
    
    def _analyze_revenue_trends(self, daily_revenue: List[Dict]) -> Dict:
        """Analyze revenue trends over time"""
        if not daily_revenue:
            return {'trend': 'insufficient_data'}
        
        df = pd.DataFrame(daily_revenue)
        if 'revenue' in df.columns and len(df) > 1:
            recent = df.tail(7)['revenue'].mean()
            older = df.head(7)['revenue'].mean() if len(df) > 7 else recent
            
            if recent > older * 1.1:
                trend = 'growing'
            elif recent < older * 0.9:
                trend = 'declining'
            else:
                trend = 'stable'
            
            return {
                'trend': trend,
                'avg_daily_revenue': round(df['revenue'].mean(), 2),
                'best_day': df.loc[df['revenue'].idxmax(), 'date'] if 'date' in df.columns else None,
                'best_day_revenue': round(df['revenue'].max(), 2)
            }
        
        return {'trend': 'stable'}
    
    def _generate_strategic_recommendations(self, stats: Dict, 
                                           workers: List[Dict],
                                           services: List[Dict]) -> List[str]:
        """Generate strategic business recommendations"""
        recommendations = []
        
        # Revenue-based recommendations
        total_revenue = stats.get('total_revenue', 0)
        avg_order = stats.get('avg_order_value', 0)
        
        if avg_order < 100:
            recommendations.append(
                "Consider introducing premium service packages to increase average order value."
            )
        
        # Service recommendations
        if services:
            top_services = [s['name'] for s in services[:3]]
            recommendations.append(
                f"Focus marketing on top services: {', '.join(top_services)}"
            )
        
        # Staffing recommendations
        in_progress = stats.get('by_status', {}).get('in_progress', {}).get('count', 0)
        pending = stats.get('by_status', {}).get('pending', {}).get('count', 0)
        
        if pending > in_progress * 2:
            recommendations.append(
                "High pending order backlog detected. Consider adding more workers or "
                "extending operating hours to improve throughput."
            )
        
        # Worker recommendations
        if workers:
            avg_completion = (
    sum((w.get('avg_completion_minutes') or 0) for w in workers) / len(workers)
    if workers else 0)
            if avg_completion > 120:
                recommendations.append(
                    "Average job completion time is high. Consider workflow optimization "
                    "or additional equipment to improve efficiency."
                )
        
        return recommendations
