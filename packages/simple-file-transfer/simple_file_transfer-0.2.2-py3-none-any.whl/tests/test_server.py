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


class TestCustomFileId:
    def test_store_file_with_custom_id(self, file_storage, storage_dir):
        """Test storing a file with a custom file ID."""
        from io import BytesIO
        from werkzeug.datastructures import FileStorage as WerkzeugFileStorage
        
        test_content = b"test content for custom id"
        file_obj = WerkzeugFileStorage(
            stream=BytesIO(test_content),
            filename="test.txt"
        )
        
        result = file_storage.store_file(file_obj, "test.txt", 3600, custom_file_id="myid123")
        
        assert result["file_id"] == "myid123"
        assert "myid123" in file_storage.metadata
        assert (Path(storage_dir) / "myid123").exists()
    
    def test_store_file_duplicate_custom_id(self, file_storage, storage_dir):
        """Test that duplicate custom file IDs are rejected."""
        from io import BytesIO
        from werkzeug.datastructures import FileStorage as WerkzeugFileStorage
        
        test_content = b"test content"
        file_obj1 = WerkzeugFileStorage(
            stream=BytesIO(test_content),
            filename="test1.txt"
        )
        file_obj2 = WerkzeugFileStorage(
            stream=BytesIO(test_content),
            filename="test2.txt"
        )
        
        file_storage.store_file(file_obj1, "test1.txt", 3600, custom_file_id="duplicate")
        
        with pytest.raises(ValueError, match="already exists"):
            file_storage.store_file(file_obj2, "test2.txt", 3600, custom_file_id="duplicate")
    
    def test_upload_with_custom_id_endpoint(self, client, storage_dir):
        """Test upload endpoint with custom file ID."""
        from io import BytesIO
        
        data = {
            'file': (BytesIO(b'test content'), 'test.txt'),
            'expiry': '3600',
            'file_id': 'custom456'
        }
        response = client.post('/upload', data=data, content_type='multipart/form-data')
        
        assert response.status_code == 200
        assert response.json['file_id'] == 'custom456'
