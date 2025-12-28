import os
import tempfile
import pytest
from bs4 import BeautifulSoup
from ..commands.lansend import app, init_app

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

def test_template_rendering(client):
    response = client.get('/')
    assert response.status_code == 200
    
    soup = BeautifulSoup(response.data, 'html.parser')
    assert soup.title.text == 'LanSend'
    
    # 测试文件列表容器
    file_container = soup.find('div', class_='file-container')
    assert file_container is not None
    
    # 测试上传容器
    upload_container = soup.find('div', class_='upload-container')
    assert upload_container is not None