import pandas as pd
from datetime import datetime, timedelta
import json
from typing import Dict, List, Tuple

class DrugTestTracker:
    def __init__(self, csv_path: str):
        self.df = pd.read_csv(csv_path)
        self.df['Date Hired'] = pd.to_datetime(self.df['Date Hired'])
        self.df['Date Re-Hired'] = pd.to_datetime(self.df['Date Re-Hired'])
        
    def get_latest_start_date(self, row: pd.Series) -> datetime:
        """Returns the most recent hire or re-hire date."""
        if pd.isna(row['Date Re-Hired']):
            return row['Date Hired']
        return max(row['Date Hired'], row['Date Re-Hired'])
    
    def get_notifications(self, current_date: datetime = None) -> Dict[str, List[Dict]]:
        """
        Returns notifications for initial and follow-up drug tests.
        
        Returns:
        Dict with two keys:
        - 'initial_tests': List of notifications for new hires
        - 'followup_tests': List of notifications for regular 5-month tests
        """
        if current_date is None:
            current_date = datetime.now()
            
        initial_notifications = []
        followup_notifications = []
        
        for _, row in self.df.iterrows():
            if row['Employee Status'] != 'Active':
                continue
                
            start_date = self.get_latest_start_date(row)
            employee_info = {
                'name': f"{row['First Name']} {row['Last Name']}",
                'id': row['Account Id'],
                'hire_date': start_date.strftime('%Y-%m-%d')
            }
            
            # Check for initial 90-day test notifications
            days_since_hire = (current_date - start_date).days
            
            if days_since_hire <= 90:  # Only check if within initial period
                if 76 <= days_since_hire <= 77:  # 2-week warning
                    employee_info['notification_type'] = '2_week_warning'
                    employee_info['deadline'] = (start_date + timedelta(days=90)).strftime('%Y-%m-%d')
                    initial_notifications.append(employee_info.copy())
                elif 83 <= days_since_hire <= 84:  # 1-week warning
                    employee_info['notification_type'] = '1_week_warning'
                    employee_info['deadline'] = (start_date + timedelta(days=90)).strftime('%Y-%m-%d')
                    initial_notifications.append(employee_info.copy())
            
            # Check for 5-month follow-up tests
            months_since_hire = (current_date - start_date).days / 30.44  # Average days in a month
            if months_since_hire > 5:  # Only start follow-ups after 5 months
                last_test_due = start_date + timedelta(days=int(5 * 30.44 * (months_since_hire // (5 * 30.44))))
                next_test_due = last_test_due + timedelta(days=int(5 * 30.44))
                
                days_until_next = (next_test_due - current_date).days
                
                if 0 <= days_until_next <= 7:  # Notification window for follow-ups
                    employee_info['notification_type'] = 'followup'
                    employee_info['deadline'] = next_test_due.strftime('%Y-%m-%d')
                    followup_notifications.append(employee_info.copy())
        
        return {
            'initial_tests': sorted(initial_notifications, key=lambda x: x['deadline']),
            'followup_tests': sorted(followup_notifications, key=lambda x: x['deadline'])
        }

def create_zapier_payload(notifications: Dict[str, List[Dict]]) -> Dict:
    """Creates a formatted payload for Zapier."""
    all_notifications = []
    
    for initial in notifications['initial_tests']:
        message = (
            f"INITIAL TEST NOTIFICATION - {initial['notification_type'].replace('_', ' ').title()}\n"
            f"Employee: {initial['name']} (ID: {initial['id']})\n"
            f"Hire Date: {initial['hire_date']}\n"
            f"Test Deadline: {initial['deadline']}"
        )
        all_notifications.append({
            'type': 'initial',
            'priority': 'high',
            'message': message
        })
    
    for followup in notifications['followup_tests']:
        message = (
            f"5-MONTH FOLLOW-UP TEST DUE\n"
            f"Employee: {followup['name']} (ID: {followup['id']})\n"
            f"Last Hire/Rehire Date: {followup['hire_date']}\n"
            f"Test Deadline: {followup['deadline']}"
        )
        all_notifications.append({
            'type': 'followup',
            'priority': 'medium',
            'message': message
        })
    
    return {'notifications': all_notifications}

# Example usage
if __name__ == "__main__":
    tracker = DrugTestTracker('drug_tests_2024.csv')
    notifications = tracker.get_notifications(datetime(2024, 12, 7))  # Use current date
    zapier_payload = create_zapier_payload(notifications)
    print(json.dumps(zapier_payload, indent=2))
