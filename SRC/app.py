import os
import boto3
import multiprocessing
import threading
import time
import math
import psutil
import atexit
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError
from flask import Flask, jsonify, request, render_template, redirect

app = Flask(__name__)

# S3 Configuration
S3_BUCKET = "ckc101-23"
S3_REGION = "ap-east-2"  # The bucket is located in Hong Kong region

def get_s3_client():
    """
    Initialize and return a boto3 S3 client.
    Rely on boto3's default credential provider chain.
    Configured with the correct region and Signature Version 4.
    """
    from botocore.client import Config
    return boto3.client(
        's3',
        region_name=S3_REGION,
        config=Config(signature_version='s3v4')
    )

# In-memory storage for tasks
tasks = [
    {
        "id": 1,
        "title": "Welcome to Flask Dashboard! 🚀",
        "completed": False,
    },
    {
        "id": 2,
        "title": "Explore the code structure (src and test)",
        "completed": True,
    },
    {
        "id": 3,
        "title": "Run pytest to verify backend logic",
        "completed": False,
    }
]
next_id = 4

@app.route('/')
def index():
    """Render the dashboard UI."""
    return render_template('index.html')

@app.route('/feature1')
def feature1():
    """Feature 1 page: Morning Stock Viewing."""
    return render_template(
        'feature.html',
        title="早上看股票",
        message="早上要看股票 📈",
        icon="trending-up"
    )

@app.route('/feature2')
def feature2():
    """Feature 2 page: Afternoon Job Search."""
    return render_template(
        'feature.html',
        title="找下午上班公司",
        message="要找下午上班的公司 💼",
        icon="briefcase"
    )

@app.route('/feature3')
def feature3():
    """Feature 3 page: S3 File Manager."""
    return render_template('s3_manager.html')

@app.route('/api/s3/files', methods=['GET'])
def list_s3_files():
    """List all objects inside the S3 bucket."""
    try:
        s3 = get_s3_client()
        response = s3.list_objects_v2(Bucket=S3_BUCKET)
        files = []
        if 'Contents' in response:
            for obj in response['Contents']:
                files.append({
                    'key': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'].isoformat()
                })
        return jsonify(files)
    except (NoCredentialsError, PartialCredentialsError) as e:
        return jsonify({
            "error": "Credentials missing",
            "error_type": type(e).__name__,
            "message": "AWS credentials not configured. Please configure them locally or run in EC2 with an IAM Role."
        }), 403
    except ClientError as e:
        return jsonify({
            "error": "AWS client error",
            "error_type": "ClientError",
            "message": str(e)
        }), 400
    except Exception as e:
        return jsonify({
            "error": "Internal server error",
            "error_type": type(e).__name__,
            "message": str(e)
        }), 500

@app.route('/api/s3/upload', methods=['POST'])
def upload_s3_file():
    """Upload a file directly to S3."""
    if 'file' not in request.files:
        return jsonify({"error": "No file part in request"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
        
    try:
        s3 = get_s3_client()
        s3.upload_fileobj(file, S3_BUCKET, file.filename)
        return jsonify({"success": True, "message": f"File '{file.filename}' uploaded successfully."}), 201
    except (NoCredentialsError, PartialCredentialsError) as e:
        return jsonify({
            "error": "Credentials missing",
            "error_type": type(e).__name__,
            "message": "AWS credentials not configured."
        }), 403
    except ClientError as e:
        return jsonify({
            "error": "AWS client error",
            "error_type": "ClientError",
            "message": str(e)
        }), 400
    except Exception as e:
        return jsonify({
            "error": "Internal server error",
            "error_type": type(e).__name__,
            "message": str(e)
        }), 500

@app.route('/api/s3/download/<path:filename>', methods=['GET'])
def download_s3_file(filename):
    """Generate a secure presigned URL and redirect the client."""
    try:
        s3 = get_s3_client()
        presigned_url = s3.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': S3_BUCKET,
                'Key': filename,
                'ResponseContentDisposition': f'attachment; filename="{filename}"'
            },
            ExpiresIn=3600
        )
        return redirect(presigned_url)
    except (NoCredentialsError, PartialCredentialsError) as e:
        return jsonify({
            "error": "Credentials missing",
            "error_type": type(e).__name__,
            "message": "AWS credentials not configured."
        }), 403
    except ClientError as e:
        return jsonify({
            "error": "AWS client error",
            "error_type": "ClientError",
            "message": str(e)
        }), 400
    except Exception as e:
        return jsonify({
            "error": "Internal server error",
            "error_type": type(e).__name__,
            "message": str(e)
        }), 500

@app.route('/api/s3/delete/<path:filename>', methods=['DELETE'])
def delete_s3_file(filename):
    """Delete a file from S3."""
    try:
        s3 = get_s3_client()
        s3.delete_object(Bucket=S3_BUCKET, Key=filename)
        return jsonify({"success": True, "message": f"File '{filename}' deleted successfully."})
    except (NoCredentialsError, PartialCredentialsError) as e:
        return jsonify({
            "error": "Credentials missing",
            "error_type": type(e).__name__,
            "message": "AWS credentials not configured."
        }), 403
    except ClientError as e:
        return jsonify({
            "error": "AWS client error",
            "error_type": "ClientError",
            "message": str(e)
        }), 400
    except Exception as e:
        return jsonify({
            "error": "Internal server error",
            "error_type": type(e).__name__,
            "message": str(e)
        }), 500


@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    """Retrieve all tasks."""
    return jsonify(tasks)

@app.route('/api/tasks', methods=['POST'])
def create_task():
    """Create a new task."""
    global next_id
    data = request.get_json() or {}
    title = data.get('title', '').strip()
    
    if not title:
        return jsonify({"error": "Task title cannot be empty"}), 400
        
    new_task = {
        "id": next_id,
        "title": title,
        "completed": False
    }
    tasks.append(new_task)
    next_id += 1
    return jsonify(new_task), 201

@app.route('/api/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    """Toggle a task's completed status or rename it."""
    data = request.get_json() or {}
    task = next((t for t in tasks if t['id'] == task_id), None)
    
    if not task:
        return jsonify({"error": "Task not found"}), 404
        
    if 'completed' in data:
        task['completed'] = bool(data['completed'])
        
    if 'title' in data:
        title = data['title'].strip()
        if title:
            task['title'] = title
            
    return jsonify(task)

@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    """Delete a task."""
    global tasks
    task = next((t for t in tasks if t['id'] == task_id), None)
    
    if not task:
        return jsonify({"error": "Task not found"}), 404
        
    tasks = [t for t in tasks if t['id'] != task_id]
    return jsonify({"success": True, "message": f"Task {task_id} deleted"})


# ==========================================================================
# Stress Testing (Feature 4) Backend & API
# ==========================================================================

# Global variables to manage stress tests
stress_lock = threading.Lock()
stress_active = False
stress_cores = 0
stress_ram_mb = 0
stress_start_time = None
stress_duration = 0
stress_processes = []
stress_ram_holder = None
stress_stop_event = None
stress_timer = None

def cpu_stress_worker(duration, stop_event):
    """Run calculations to utilize 100% CPU on a core until stopped or duration expires."""
    start_time = time.time()
    # Initialize CPU usage interval
    psutil.cpu_percent(interval=None)
    while not stop_event.is_set():
        if duration and (time.time() - start_time > duration):
            break
        # Perform intensive float operations
        x = 0.0001
        for _ in range(1000):
            x += math.sqrt(x)

def stop_stress_test():
    """Stop all active stress tests and clean up memory/processes."""
    global stress_active, stress_cores, stress_ram_mb, stress_start_time, stress_duration
    global stress_processes, stress_ram_holder, stress_stop_event, stress_timer
    
    with stress_lock:
        if not stress_active:
            return
            
        stress_active = False
        stress_cores = 0
        stress_ram_mb = 0
        stress_start_time = None
        stress_duration = 0
        
        # Trigger event for processes to stop
        if stress_stop_event:
            stress_stop_event.set()
            
        # Terminate CPU processes
        for p in stress_processes:
            try:
                if p.is_alive():
                    p.terminate()
                    p.join(timeout=1.0)
            except Exception:
                pass
        stress_processes = []
        
        # Deallocate memory
        stress_ram_holder = None
        
        # Cancel auto-stop timer
        if stress_timer:
            try:
                stress_timer.cancel()
            except Exception:
                pass
            stress_timer = None

# Ensure cleanup on process exit
atexit.register(stop_stress_test)

def start_stress_test(cores, ram_mb, duration):
    """Start CPU and RAM stress testing."""
    global stress_active, stress_cores, stress_ram_mb, stress_start_time, stress_duration
    global stress_processes, stress_ram_holder, stress_stop_event, stress_timer
    
    with stress_lock:
        if stress_active:
            return False, "Stress test already running"
            
        # Verify resource limits
        max_cores = multiprocessing.cpu_count()
        if cores < 1 or cores > max_cores:
            return False, f"Invalid CPU cores. System max is {max_cores}"
            
        # We enforce up to 75% of available memory to prevent OS crash
        mem_info = psutil.virtual_memory()
        available_mb = mem_info.available // (1024 * 1024)
        safe_limit_mb = int(available_mb * 0.75)
        if ram_mb < 0 or ram_mb > safe_limit_mb:
            return False, f"Invalid RAM size. Safe limit is {safe_limit_mb} MB"
            
        stress_active = True
        stress_cores = cores
        stress_ram_mb = ram_mb
        stress_duration = duration
        stress_start_time = time.time()
        
        # Create multiprocessing manager and stop event
        manager = multiprocessing.Manager()
        stress_stop_event = manager.Event()
        
        # 1. Start CPU stress processes
        stress_processes = []
        for _ in range(cores):
            p = multiprocessing.Process(target=cpu_stress_worker, args=(duration, stress_stop_event))
            p.daemon = True
            p.start()
            stress_processes.append(p)
            
        # 2. Start RAM stress (allocate memory)
        if ram_mb > 0:
            try:
                size_bytes = ram_mb * 1024 * 1024
                # Allocate a large bytearray and touch memory to map pages
                ram_data = bytearray(size_bytes)
                for i in range(0, size_bytes, 4096):
                    ram_data[i] = 1
                stress_ram_holder = ram_data
            except MemoryError:
                # Clean up CPU processes if RAM allocation fails
                stress_active = False
                for p in stress_processes:
                    p.terminate()
                stress_processes = []
                return False, "Failed to allocate requested RAM"
                
        # 3. Schedule auto-stop timer
        if duration > 0:
            stress_timer = threading.Timer(duration, stop_stress_test)
            stress_timer.daemon = True
            stress_timer.start()
            
        return True, "Stress test started successfully"

@app.route('/feature4')
def feature4():
    """Feature 4 page: CPU and RAM Stress Test."""
    max_cores = multiprocessing.cpu_count()
    mem_info = psutil.virtual_memory()
    available_mb = mem_info.available // (1024 * 1024)
    safe_limit_mb = int(available_mb * 0.75)
    total_gb = round(mem_info.total / (1024 * 1024 * 1024), 1)
    
    return render_template(
        'stress_test.html',
        max_cores=max_cores,
        max_mem_mb=safe_limit_mb,
        total_mem_gb=total_gb
    )

@app.route('/api/stress/start', methods=['POST'])
def api_start_stress():
    """API endpoint to start stress testing."""
    data = request.get_json() or {}
    cores = int(data.get('cores', 1))
    ram_mb = int(data.get('ram_mb', 0))
    duration = int(data.get('duration', 10))
    
    success, message = start_stress_test(cores, ram_mb, duration)
    if not success:
        return jsonify({"error": message}), 400
        
    return jsonify({"success": True, "message": message})

@app.route('/api/stress/stop', methods=['POST'])
def api_stop_stress():
    """API endpoint to stop stress testing."""
    stop_stress_test()
    return jsonify({"success": True, "message": "Stress test stopped"})

@app.route('/api/stress/status', methods=['GET'])
def api_stress_status():
    """API endpoint to retrieve real-time resource utilization."""
    remaining = None
    if stress_active and stress_start_time and stress_duration:
        elapsed = time.time() - stress_start_time
        remaining = max(0.0, stress_duration - elapsed)
        
    cpu_percent = psutil.cpu_percent(interval=None)
    mem = psutil.virtual_memory()
    
    return jsonify({
        "active": stress_active,
        "cores": stress_cores,
        "ram_mb": stress_ram_mb,
        "remaining_time": remaining,
        "cpu_usage": cpu_percent,
        "memory_usage": mem.percent,
        "memory_used": mem.used // (1024 * 1024),
        "memory_total": mem.total // (1024 * 1024)
    })


if __name__ == '__main__':
    # Deploy on port 19191
    port = int(os.environ.get('PORT', 19191))
    print(f"Starting Flask server on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=True)
