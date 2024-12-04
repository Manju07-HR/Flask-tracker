from flask import Flask, render_template, request, jsonify
import requests
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from collections import defaultdict

# Load environment variables
load_dotenv()
app = Flask(__name__, template_folder='Templates')

# Configuration
API_TOKEN = 'c36dcac846da96b2caf44360593c286b2d9b6b12'
WORKSPACE_ID = 'b165fd42-8970-433b-ae50-9a9fd86b2970'
API_BASE_URL = 'https://hovercode.com/api/v2'
FIXED_URL = 'https://www.datalogicsindia.com/links'
QR_CODE_ID = None

def create_or_get_qr_code():
    """Create QR code if not exists or get existing one"""
    global QR_CODE_ID
    
    if QR_CODE_ID:
        try:
            response = requests.get(
                f'{API_BASE_URL}/hovercode/{QR_CODE_ID}/',
                headers={'Authorization': f'Token {API_TOKEN}'},
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
        except requests.RequestException:
            pass

    try:
        response = requests.post(
            f'{API_BASE_URL}/hovercode/create/',
            headers={'Authorization': f'Token {API_TOKEN}'},
            json={
                'workspace': WORKSPACE_ID,
                'qr_data': FIXED_URL,
                'primary_color': '#3b81f6',
                'background_color': '#FFFFFF',
                'dynamic': True,
                'pattern': 'Diamonds',
                'has_border': True,
                'generate_png': True
            },
            timeout=10
        )
        data = response.json()
        QR_CODE_ID = data.get('id')
        return data
    except requests.RequestException as e:
        return {'error': str(e)}

def get_visitor_identifier(scan):
    """Create a unique identifier for a visitor based on available data"""
    # Combine multiple factors to create a unique identifier
    identifier_parts = [
        scan.get('ip_address', ''),
        scan.get('device', ''),
        scan.get('user_agent', ''),
        scan.get('location', '')
    ]
    return '_'.join(filter(None, identifier_parts))

def should_count_scan(scan):
    """Determine if a scan should be counted in totals"""
    # Safely get device and location with None/empty string handling
    device = scan.get('device', '') or ''
    location = scan.get('location', '') or ''
    
    # Convert to lowercase, handling potential None values
    device = str(device).lower()
    location = str(location).lower()
    
    # Excluded lists
    excluded_devices = ['test-device', 'simulator']
    excluded_locations = ['test-location']
    
    # Check for exclusions
    if any(excluded in device for excluded in excluded_devices):
        return False
    if any(excluded in location for excluded in excluded_locations):
        return False
    
    return True

def process_scan_stats(scans):
    """Process scan statistics by date periods with unique device tracking"""
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    
    stats = {
        'total': 0,
        'total_unique': 0,
        'today': 0,
        'today_unique': 0,
        'yesterday': 0,
        'yesterday_unique': 0,
        'last_7_days': 0,
        'last_7_days_unique': 0,
        'last_30_days': 0,
        'last_30_days_unique': 0,
        'recent_scans': []
    }
    
    if not scans or not scans.get('results'):
        return stats
    
    # Track unique devices
    all_devices = set()
    today_devices = set()
    yesterday_devices = set()
    last_7_days_devices = set()
    last_30_days_devices = set()
    
    for scan in scans.get('results', []):
        try:
            # Parse timestamp
            scan_time = datetime.strptime(scan['time_utc'].split('+')[0], '%Y-%m-%d %H:%M:%S.%f')
        except ValueError:
            try:
                scan_time = datetime.strptime(scan['time_utc'].split('+')[0], '%Y-%m-%d %H:%M:%S')
            except ValueError:
                continue
        
        # Get device identifier
        device_id = scan.get('device', 'Unknown')
        scan_date = scan_time.date()
        
        # Track unique devices
        all_devices.add(device_id)
        
        # Count scans by date
        days_diff = (today - scan_date).days
        
        # Today's scans
        if scan_date == today:
            stats['today'] += 1
            today_devices.add(device_id)
        
        # Yesterday's scans
        elif scan_date == yesterday:
            stats['yesterday'] += 1
            yesterday_devices.add(device_id)
        
        # Last 7 days
        if days_diff < 7:
            stats['last_7_days'] += 1
            last_7_days_devices.add(device_id)
        
        # Last 30 days
        if days_diff < 30:
            stats['last_30_days'] += 1
            last_30_days_devices.add(device_id)
        
        # Recent scans (limited to 10)
        if len(stats['recent_scans']) < 10:
            formatted_time = scan_time.strftime('%Y-%m-%d %H:%M:%S')
            stats['recent_scans'].append({
                'time': formatted_time,
                'location': scan.get('location', 'Unknown'),
                'device': device_id,
                'is_unique': device_id not in (all_devices - {device_id})
            })
    
    # Update unique device counts
    stats['total_unique'] = len(all_devices)
    stats['today_unique'] = len(today_devices)
    stats['yesterday_unique'] = len(yesterday_devices)
    stats['last_7_days_unique'] = len(last_7_days_devices)
    stats['last_30_days_unique'] = len(last_30_days_devices)
    
    return stats

@app.route('/')
def index():
    qr_code = create_or_get_qr_code()
    return render_template('Index.html', qr_code=qr_code)

@app.route('/stats')
def get_stats():
    if not QR_CODE_ID:
        create_or_get_qr_code()
    
    try:
        response = requests.get(
            f'{API_BASE_URL}/hovercode/{QR_CODE_ID}/activity/',
            headers={'Authorization': f'Token {API_TOKEN}'},
            params={'page_size': 200},  # Get more results for better statistics
            timeout=10
        )
        raw_stats = response.json()
        processed_stats = process_scan_stats(raw_stats)
        return jsonify(processed_stats)
    except requests.RequestException as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
