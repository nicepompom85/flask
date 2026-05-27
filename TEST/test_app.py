import pytest
import sys
import os

# Ensure the root directory (containing src/) is in the python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from SRC.app import app, tasks

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        # Reset task list state before each test
        global tasks
        tasks.clear()
        tasks.extend([
            {"id": 1, "title": "Test Task 1", "completed": False},
            {"id": 2, "title": "Test Task 2", "completed": True}
        ])
        yield client

def test_index_page(client):
    """Test that the index dashboard page loads successfully."""
    response = client.get('/')
    assert response.status_code == 200
    assert b"Antigravity Dashboard" in response.data

def test_get_tasks(client):
    """Test retrieving tasks through the API."""
    response = client.get('/api/tasks')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 2
    assert data[0]['title'] == "Test Task 1"
    assert data[1]['completed'] is True

def test_create_task_success(client):
    """Test creating a new task successfully."""
    response = client.post('/api/tasks', json={"title": "New Integration Test Task"})
    assert response.status_code == 201
    data = response.get_json()
    assert data['title'] == "New Integration Test Task"
    assert data['completed'] is False
    assert 'id' in data

def test_create_task_empty_title(client):
    """Test that creating a task with empty title returns 400 bad request."""
    response = client.post('/api/tasks', json={"title": ""})
    assert response.status_code == 400
    assert "error" in response.get_json()

def test_update_task_status(client):
    """Test toggling task completed status."""
    response = client.put('/api/tasks/1', json={"completed": True})
    assert response.status_code == 200
    data = response.get_json()
    assert data['completed'] is True

def test_update_task_not_found(client):
    """Test that updating a non-existent task returns 404."""
    response = client.put('/api/tasks/999', json={"completed": True})
    assert response.status_code == 404

def test_delete_task_success(client):
    """Test deleting a task."""
    response = client.delete('/api/tasks/1')
    assert response.status_code == 200
    assert response.get_json()['success'] is True
    
    # Verify it is deleted from list
    get_res = client.get('/api/tasks')
    assert len(get_res.get_json()) == 1

def test_delete_task_not_found(client):
    """Test that deleting a non-existent task returns 404."""
    response = client.delete('/api/tasks/999')
    assert response.status_code == 404

def test_feature1(client):
    """Test that /feature1 page loads and contains stock viewing text."""
    response = client.get('/feature1')
    assert response.status_code == 200
    assert "早上要看股票".encode('utf-8') in response.data

def test_feature2(client):
    """Test that /feature2 page loads and contains job search text."""
    response = client.get('/feature2')
    assert response.status_code == 200
    assert "要找下午上班的公司".encode('utf-8') in response.data

