import os
from flask import Flask, jsonify, request, render_template

app = Flask(__name__)

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
