import pytest
import sys
import os
import datetime
import io
from unittest.mock import patch, MagicMock
from botocore.exceptions import NoCredentialsError

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


def test_feature3(client):
    """Test that /feature3 page loads and contains S3 header text."""
    response = client.get('/feature3')
    assert response.status_code == 200
    assert "S3 雲端檔案管理".encode('utf-8') in response.data


@patch('SRC.app.get_s3_client')
def test_list_s3_files_success(mock_get_s3_client, client):
    """Test listing files from S3 successfully (mocked)."""
    mock_s3 = MagicMock()
    mock_s3.list_objects_v2.return_value = {
        'Contents': [
            {
                'Key': 'test_file.txt',
                'Size': 1024,
                'LastModified': datetime.datetime(2026, 5, 28, 12, 0, 0, tzinfo=datetime.timezone.utc)
            }
        ]
    }
    mock_get_s3_client.return_value = mock_s3
    
    response = client.get('/api/s3/files')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]['key'] == 'test_file.txt'
    assert data[0]['size'] == 1024
    assert 'last_modified' in data[0]


@patch('SRC.app.get_s3_client')
def test_list_s3_files_no_credentials(mock_get_s3_client, client):
    """Test that list API handles missing credentials properly (returns 403)."""
    mock_get_s3_client.side_effect = NoCredentialsError()
    
    response = client.get('/api/s3/files')
    assert response.status_code == 403
    data = response.get_json()
    assert data['error'] == 'Credentials missing'


@patch('SRC.app.get_s3_client')
def test_upload_s3_file_success(mock_get_s3_client, client):
    """Test file upload to S3 (mocked)."""
    mock_s3 = MagicMock()
    mock_get_s3_client.return_value = mock_s3
    
    data = {
        'file': (io.BytesIO(b"my test file content"), 'test_upload.txt')
    }
    response = client.post('/api/s3/upload', data=data, content_type='multipart/form-data')
    assert response.status_code == 201
    assert response.get_json()['success'] is True
    mock_s3.upload_fileobj.assert_called_once()


@patch('SRC.app.get_s3_client')
def test_download_s3_file_redirect(mock_get_s3_client, client):
    """Test S3 download redirects to a presigned URL (mocked)."""
    mock_s3 = MagicMock()
    mock_s3.generate_presigned_url.return_value = "https://s3.amazonaws.com/ckc101-23/test.txt?presigned"
    mock_get_s3_client.return_value = mock_s3
    
    response = client.get('/api/s3/download/test.txt')
    assert response.status_code == 302
    assert response.headers['Location'] == "https://s3.amazonaws.com/ckc101-23/test.txt?presigned"


@patch('SRC.app.get_s3_client')
def test_delete_s3_file_success(mock_get_s3_client, client):
    """Test deleting an object from S3 (mocked)."""
    mock_s3 = MagicMock()
    mock_get_s3_client.return_value = mock_s3
    
    response = client.delete('/api/s3/delete/test.txt')
    assert response.status_code == 200
    assert response.get_json()['success'] is True
    mock_s3.delete_object.assert_called_once_with(Bucket='ckc101-23', Key='test.txt')

