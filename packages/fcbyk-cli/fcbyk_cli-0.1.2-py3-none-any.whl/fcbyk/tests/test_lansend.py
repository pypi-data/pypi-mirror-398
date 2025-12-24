import os
import tempfile
import pytest
from ..commands.lansend import app, safe_filename, init_app

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as temp_dir:
        # 创建测试文件
        with open(os.path.join(temp_dir, 'test.txt'), 'w') as f:
            f.write('test content')
        yield temp_dir

@pytest.fixture
def client(temp_dir):
    init_app(directory=temp_dir)
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_safe_filename():
    assert safe_filename('test.txt') == 'test.txt'
    assert safe_filename('test*file.txt') == 'testfile.txt'

def test_index_page(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b'test.txt' in response.data

def test_file_download(client):
    response = client.get('/test.txt')
    assert response.status_code == 200
    assert response.data == b'test content'