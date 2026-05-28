import os
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError
from flask import Flask, jsonify, request, render_template, redirect

app = Flask(__name__)

# S3 Configuration
S3_BUCKET = "ckc101-23"
S3_REGION = os.environ.get('AWS_DEFAULT_REGION', 'ap-east-2')

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

if __name__ == '__main__':
    # Deploy on port 19191
    port = int(os.environ.get('PORT', 19191))
    print(f"Starting Flask server on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=True)
