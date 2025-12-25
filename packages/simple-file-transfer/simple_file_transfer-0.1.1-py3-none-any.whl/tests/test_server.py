import os
import tempfile
import pytest
from pathlib import Path
from datetime import datetime, timedelta
from sft.server import FileStorage, app


@pytest.fixture
def storage_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def file_storage(storage_dir):
    return FileStorage(storage_dir)


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


class TestFileStorage:
    def test_generate_file_id(self, file_storage):
        file_id = file_storage._generate_file_id()
        assert len(file_id) == 6
        assert file_id.isdigit()
    
    def test_generate_unique_file_ids(self, file_storage):
        ids = set()
        for _ in range(100):
            file_id = file_storage._generate_file_id()
            ids.add(file_id)
        assert len(ids) == 100
    
    def test_calculate_sha256(self, file_storage, storage_dir):
        test_file = Path(storage_dir) / "test.txt"
        test_file.write_text("test content")
        
        sha256 = file_storage._calculate_sha256(test_file)
        assert len(sha256) == 64
        assert sha256 == "6ae8a75555209fd6c44157c0aed8016e763ff435a19cf186f76863140143ff72"
    
    def test_metadata_persistence(self, storage_dir):
        storage1 = FileStorage(storage_dir)
        storage1.metadata["test"] = {"data": "value"}
        storage1._save_metadata()
        
        storage2 = FileStorage(storage_dir)
        assert "test" in storage2.metadata
        assert storage2.metadata["test"]["data"] == "value"
    
    def test_cleanup_expired(self, file_storage, storage_dir):
        test_file = Path(storage_dir) / "123456"
        test_file.write_text("test content")
        
        past_time = datetime.now() - timedelta(hours=1)
        file_storage.metadata["123456"] = {
            "filename": "test.txt",
            "size": 12,
            "sha256": "abc123",
            "expiry": past_time.isoformat(),
            "uploaded": past_time.isoformat()
        }
        file_storage._save_metadata()
        
        file_storage.cleanup_expired()
        
        assert "123456" not in file_storage.metadata
        assert not test_file.exists()


class TestServerEndpoints:
    def test_health_endpoint(self, client):
        response = client.get('/health')
        assert response.status_code == 200
        assert response.json == {"status": "ok"}
    
    def test_upload_no_file(self, client):
        response = client.post('/upload')
        assert response.status_code == 400
        assert "error" in response.json
    
    def test_upload_empty_filename(self, client):
        data = {'file': (b'', '')}
        response = client.post('/upload', data=data)
        assert response.status_code == 400
    
    def test_download_nonexistent(self, client):
        response = client.get('/download/999999')
        assert response.status_code == 404
    
    def test_info_nonexistent(self, client):
        response = client.get('/info/999999')
        assert response.status_code == 404
