from flask import Flask, request, jsonify
import subprocess
import uiautomator2 as u2
import time
import pytesseract
import threading
import os
from queue import Queue
import uuid
import json
from datetime import datetime

# Try to import CORS, if not available, create a dummy decorator
try:
    from flask_cors import CORS
    app = Flask(__name__)
    CORS(app)
except ImportError:
    app = Flask(__name__)
    # CORS not available, but API will still work
    print("Warning: flask_cors not installed. CORS headers will not be set.")

# Queue untuk antrian login requests
login_queue = Queue()
queue_lock = threading.Lock()

# Thread-safe storage untuk pending login requests
pending_logins = {}
pending_lock = threading.Lock()

# Direktori untuk temp files
TEMP_DIR = "temp_requests"
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

TAP_USERID_INPUT = 600, 260
TAP_PWD_INPUT = 600, 350
TAP_LOGIN = 640, 456
TAP_TENTUKAN = 630, 444
TAP_ID_LOGIN = 60, 155

OCR_AREA = (370, 235, 890, 381)  # x1, y1, x2, y2
OCR_RESPONSE = False  # True: tampilkan semua log OCR, False: hanya tampilkan yang terdeteksi keyword

# Emulator management
emulators = {}  # {device_id: {'device': u2_device, 'busy': False, 'lock': threading.Lock()}}
emulators_lock = threading.Lock()

def detect_all_emulators():
    """Deteksi semua emulator yang aktif"""
    result = subprocess.run("adb devices", shell=True, capture_output=True, text=True)
    detected_devices = []
    
    for line in result.stdout.split('\n'):
        parts = line.split()
        if len(parts) >= 2 and 'List' not in line:
            device_id, status = parts[0], parts[1]
            if status == 'offline':
                subprocess.run(f"adb connect {device_id}", shell=True, capture_output=True)
                time.sleep(0.5)  # Tunggu koneksi
            if status in ('device', 'offline'):
                detected_devices.append(device_id)
    
    return detected_devices

def initialize_emulators():
    """Inisialisasi semua emulator yang terdeteksi"""
    device_ids = detect_all_emulators()
    
    with emulators_lock:
        for device_id in device_ids:
            try:
                device = u2.connect(device_id)
                # Test connection
                device.info
                emulators[device_id] = {
                    'device': device,
                    'busy': False,
                    'lock': threading.Lock(),
                    'current_request_id': None
                }
                print(f"[EMULATOR] Connected: {device_id}")
            except Exception as e:
                print(f"[EMULATOR] Failed to connect {device_id}: {e}")
    
    if not emulators:
        print("[WARNING] No emulators found!")
    else:
        print(f"[EMULATOR] Total {len(emulators)} emulator(s) ready")

# Inisialisasi emulator saat startup
initialize_emulators()

def ocr_area(device, area):
    screenshot = device.screenshot()
    x1, y1, x2, y2 = area
    cropped = screenshot.crop((x1, y1, x2, y2))
    text = pytesseract.image_to_string(cropped)
    return text.strip()

def retry_until_edittext(device, userid, password, request_id):
    while True:
        device.click(*TAP_TENTUKAN)
        time.sleep(0.1)
        device.click(*TAP_ID_LOGIN)
        time.sleep(0.1)
        device.click(*TAP_USERID_INPUT)
        time.sleep(0.1)
        focused = device(focused=True)
        if focused.exists and ('EditText' in focused.info.get('className', '') or 'TextInput' in focused.info.get('className', '')):
            # Login berhasil, tapi tunggu response dari mitm.py
            break
        time.sleep(0.1)

def retry_until_edittext_failed(device):
    while True:
        device.click(*TAP_TENTUKAN)
        time.sleep(0.1)
        device.click(*TAP_USERID_INPUT)
        time.sleep(0.1)
        focused = device(focused=True)
        if focused.exists and ('EditText' in focused.info.get('className', '') or 'TextInput' in focused.info.get('className', '')):
            break
        time.sleep(0.1)

def ocr_realtime(device, area, userid, password, request_id):
    while True:
        text = ocr_area(device, area)
        if text:
            # Cek keyword dan lakukan tap jika ditemukan
            text_lower = text.lower()
            keyword_success = 'koneksi jaringan' in text_lower or 'beberapa saat' in text_lower
            keyword_failed = 'parameter salah' in text_lower
            
            if keyword_success:
                device.click(*TAP_TENTUKAN)
                time.sleep(0.5)
                device.click(*TAP_ID_LOGIN)
                time.sleep(0.5)
                # Tap USERID_INPUT dan cek EditText
                device.click(*TAP_USERID_INPUT)
                time.sleep(0.5)
                focused = device(focused=True)
                if focused.exists and ('EditText' in focused.info.get('className', '') or 'TextInput' in focused.info.get('className', '')):
                    # Login berhasil, tapi tunggu response dari mitm.py
                    break
                else:
                    # Retry tanpa batas sampai menemukan EditText
                    retry_until_edittext(device, userid, password, request_id)
            
            elif keyword_failed:
                device.click(*TAP_TENTUKAN)
                time.sleep(0.5)
                # Tap USERID_INPUT dan cek EditText
                device.click(*TAP_USERID_INPUT)
                time.sleep(0.5)
                focused = device(focused=True)
                if focused.exists and ('EditText' in focused.info.get('className', '') or 'TextInput' in focused.info.get('className', '')):
                    break
                else:
                    # Retry tanpa batas sampai menemukan EditText
                    retry_until_edittext_failed(device)
        time.sleep(0.2)

def _get_temp_file_path(request_id):
    """Mendapatkan path temp file untuk request_id"""
    return os.path.join(TEMP_DIR, f"{request_id}.json")

def _save_request_to_file(request_id, userid, password, timestamp):
    """Menyimpan request data ke temp file"""
    temp_file = _get_temp_file_path(request_id)
    data = {
        'request_id': request_id,
        'userid': userid,
        'password': password,
        'timestamp': timestamp,
        'status': 'pending',
        'result': None
    }
    with open(temp_file, 'w') as f:
        json.dump(data, f)

def _load_request_from_file(request_id):
    """Memuat request data dari temp file"""
    temp_file = _get_temp_file_path(request_id)
    if os.path.exists(temp_file):
        with open(temp_file, 'r') as f:
            return json.load(f)
    return None

def _update_request_file(request_id, result):
    """Update result di temp file"""
    temp_file = _get_temp_file_path(request_id)
    if os.path.exists(temp_file):
        data = _load_request_from_file(request_id)
        if data:
            data['result'] = result
            data['status'] = 'completed'
            with open(temp_file, 'w') as f:
                json.dump(data, f)

def _delete_temp_file(request_id):
    """Hapus temp file setelah selesai"""
    temp_file = _get_temp_file_path(request_id)
    if os.path.exists(temp_file):
        try:
            os.remove(temp_file)
        except Exception:
            pass

def get_idle_emulator():
    """Mendapatkan emulator yang tidak busy (idle)"""
    with emulators_lock:
        for device_id, emu_data in emulators.items():
            with emu_data['lock']:
                if not emu_data['busy']:
                    return device_id, emu_data['device']
    return None, None

def set_emulator_busy(device_id, request_id, busy=True):
    """Set status emulator menjadi busy atau idle"""
    with emulators_lock:
        if device_id in emulators:
            with emulators[device_id]['lock']:
                emulators[device_id]['busy'] = busy
                emulators[device_id]['current_request_id'] = request_id if busy else None

def perform_login(userid, password, request_id, device, device_id):
    """Melakukan login automation di background thread"""
    if not device:
        result = {
            'status': 'login_failed',
            'userId': userid,
            'error': 'Device not available'
        }
        _update_request_file(request_id, result)
        with pending_lock:
            if request_id in pending_logins:
                pending_logins[request_id]['result'] = result
                pending_logins[request_id]['event'].set()
        return
    
    try:
        # Set emulator sebagai busy
        set_emulator_busy(device_id, request_id, busy=True)
        
        # Jalankan OCR realtime di background thread
        ocr_thread = threading.Thread(target=ocr_realtime, args=(device, OCR_AREA, userid, password, request_id))
        ocr_thread.daemon = True
        ocr_thread.start()
        
        # Tap dan paste ID
        while True:
            device.click(*TAP_USERID_INPUT)
            time.sleep(0.05)
            focused = device(focused=True)
            if focused.exists and ('EditText' in focused.info.get('className', '') or 'TextInput' in focused.info.get('className', '')):
                focused.set_text('')
                focused.set_text(userid)
                break
        
        # Tap dan paste Password
        while True:
            device.click(*TAP_PWD_INPUT)
            time.sleep(0.05)
            focused = device(focused=True)
            if focused.exists and ('EditText' in focused.info.get('className', '') or 'TextInput' in focused.info.get('className', '')):
                focused.set_text('')
                focused.set_text(password)
                break
        
        time.sleep(0.2)
        device.click(*TAP_LOGIN)
        
        # Tunggu hasil dari mitm.py (akan di-set via callback endpoint)
        ocr_thread.join(timeout=60)  # Timeout 60 detik
    finally:
        # Set emulator sebagai idle setelah selesai
        set_emulator_busy(device_id, request_id, busy=False)

def process_login_request(request_id, userid, password, event, timestamp):
    """Memproses login request dengan load balancing"""
    # Cari emulator yang idle
    device_id, device = get_idle_emulator()
    
    if device_id and device:
        # Ada emulator yang idle, langsung proses
        print(f"[LOAD BALANCER] Using emulator {device_id} for request {request_id}")
        perform_login(userid, password, request_id, device, device_id)
    else:
        # Semua emulator busy, masukkan ke queue
        print(f"[LOAD BALANCER] All emulators busy, queuing request {request_id}")
        login_queue.put((request_id, userid, password, event, timestamp))

def queue_worker():
    """Worker thread untuk memproses queue ketika semua emulator busy"""
    while True:
        try:
            # Ambil item dari queue (blocking)
            item = login_queue.get()
            if item is None:  # Sentinel untuk stop
                break
            
            request_id, userid, password, event, timestamp = item
            
            # Tunggu sampai ada emulator yang idle
            device_id, device = None, None
            max_wait = 300  # Max 5 menit menunggu
            wait_time = 0
            
            while wait_time < max_wait:
                device_id, device = get_idle_emulator()
                if device_id and device:
                    break
                time.sleep(0.5)  # Check setiap 0.5 detik
                wait_time += 0.5
            
            if device_id and device:
                print(f"[QUEUE WORKER] Processing queued request {request_id} on emulator {device_id}")
                perform_login(userid, password, request_id, device, device_id)
            else:
                # Timeout, set error
                result = {
                    'status': 'login_failed',
                    'userId': userid,
                    'error': 'All emulators busy, request timeout'
                }
                _update_request_file(request_id, result)
                with pending_lock:
                    if request_id in pending_logins:
                        pending_logins[request_id]['result'] = result
                        pending_logins[request_id]['event'].set()
            
            login_queue.task_done()
        except Exception as e:
            print(f"Error in queue worker: {e}")
            login_queue.task_done()

# Start queue worker thread
queue_worker_thread = threading.Thread(target=queue_worker, daemon=True)
queue_worker_thread.start()

@app.route('/v1/login', methods=['GET'])
def login():
    """API endpoint untuk request login"""
    userid = request.args.get('userid')
    password = request.args.get('password')
    
    if not userid or not password:
        return jsonify({
            'status': 'error',
            'message': 'userid and password are required'
        }), 400
    
    # Generate unique request ID dengan timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    request_id = f"{timestamp}_{uuid.uuid4().hex[:8]}"
    
    # Simpan ke temp file
    _save_request_to_file(request_id, userid, password, timestamp)
    
    # Buat event untuk menunggu response
    event = threading.Event()
    with pending_lock:
        pending_logins[request_id] = {
            'userid': userid,
            'password': password,
            'event': event,
            'result': None,
            'timestamp': timestamp
        }
    
    # Coba proses langsung dengan load balancing
    # Jika semua emulator busy, akan masuk ke queue
    process_login_request(request_id, userid, password, event, timestamp)
    
    # Tunggu response dari mitm.py (max 60 detik)
    event.wait(timeout=60)
    
    # Ambil result dari memory atau file
    with pending_lock:
        result = pending_logins.get(request_id, {}).get('result')
        if not result:
            # Coba load dari file jika tidak ada di memory
            file_data = _load_request_from_file(request_id)
            if file_data and file_data.get('result'):
                result = file_data['result']
        
        # Cleanup
        if request_id in pending_logins:
            del pending_logins[request_id]
        _delete_temp_file(request_id)
    
    if result:
        return jsonify(result)
    else:
        return jsonify({
            'status': 'error',
            'message': 'Login request timeout'
        }), 408

@app.route('/api/v1/emulators/status', methods=['GET'])
def emulators_status():
    """Endpoint untuk melihat status semua emulator"""
    with emulators_lock:
        status_list = []
        for device_id, emu_data in emulators.items():
            with emu_data['lock']:
                status_list.append({
                    'device_id': device_id,
                    'busy': emu_data['busy'],
                    'current_request_id': emu_data['current_request_id']
                })
        
        queue_size = login_queue.qsize()
        
        return jsonify({
            'total_emulators': len(emulators),
            'emulators': status_list,
            'queue_size': queue_size
        })

@app.route('/api/v1/callback', methods=['POST'])
def callback():
    """Endpoint untuk menerima callback dari mitm.py"""
    data = request.json
    
    if not data:
        return jsonify({'status': 'error', 'message': 'No data provided'}), 400
    
    status = data.get('status')
    userid = data.get('userId')
    chip = data.get('chip', '')
    error = data.get('error', '')
    
    # Buat result object
    if status == 'login_success':
        result = {
            'status': 'login_success',
            'userId': userid,
            'chip': chip
        }
    elif status == 'login_failed':
        result = {
            'status': 'login_failed',
            'userId': userid,
            'error': error
        }
    else:
        return jsonify({'status': 'error', 'message': 'Invalid status'}), 400
    
    # Cari pending login berdasarkan userid (dari memory)
    found_request_id = None
    with pending_lock:
        for req_id, req_data in pending_logins.items():
            if req_data['userid'] == userid:
                found_request_id = req_id
                break
    
    # Jika tidak ditemukan di memory, cari dari temp files
    if not found_request_id:
        # Scan semua temp files untuk mencari userid yang cocok
        try:
            for filename in os.listdir(TEMP_DIR):
                if filename.endswith('.json'):
                    request_id_from_file = filename.replace('.json', '')
                    file_data = _load_request_from_file(request_id_from_file)
                    if file_data and file_data.get('userid') == userid and file_data.get('status') == 'pending':
                        found_request_id = file_data.get('request_id')
                        # Restore ke memory jika ditemukan
                        if found_request_id:
                            event = threading.Event()
                            with pending_lock:
                                pending_logins[found_request_id] = {
                                    'userid': userid,
                                    'password': file_data.get('password', ''),
                                    'event': event,
                                    'result': None,
                                    'timestamp': file_data.get('timestamp', '')
                                }
                            break
        except Exception:
            pass  # Ignore errors saat scan files
    
    if found_request_id:
        # Update file
        _update_request_file(found_request_id, result)
        
        # Update memory dan set event
        with pending_lock:
            if found_request_id in pending_logins:
                pending_logins[found_request_id]['result'] = result
                pending_logins[found_request_id]['event'].set()
        
        return jsonify({'status': 'ok'})
    else:
        return jsonify({'status': 'error', 'message': 'No pending request found for this userid'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
