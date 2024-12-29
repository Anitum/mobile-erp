import os
import pytest
from datetime import datetime, timedelta
from io import BytesIO
from flask import url_for
from app import create_app, db
from app.models.user import User
from app.models.homework import Homework, SubjectEnum
from app.models.attendance import Attendance

@pytest.fixture
def app():
    app = create_app('testing')
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['UPLOAD_FOLDER'] = 'tests/uploads'
    return app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def init_database(app):
    with app.app_context():
        db.create_all()
        
        # Create test teacher
        teacher = User(
            username='test_teacher',
            email='teacher@test.com',
            role='teacher'
        )
        teacher.set_password('password123')
        
        # Create test student
        student = User(
            username='test_student',
            email='student@test.com',
            role='student'
        )
        student.set_password('password123')
        
        db.session.add_all([teacher, student])
        db.session.commit()
        
        yield db
        
        db.session.remove()
        db.drop_all()

@pytest.fixture
def auth_teacher_client(client, init_database):
    client.post(url_for('auth.login'), data={
        'email': 'teacher@test.com',
        'password': 'password123'
    }, follow_redirects=True)
    return client

class TestTeacherRoutes:
    def test_teacher_dashboard_access(self, auth_teacher_client):
        """Test teacher dashboard access"""
        response = auth_teacher_client.get(url_for('teacher.dashboard'))
        assert response.status_code == 200
        assert b'Teacher Dashboard' in response.data

    def test_homework_creation(self, auth_teacher_client, app):
        """Test homework creation with file upload"""
        # Create test file
        file_data = BytesIO(b'Test file content')
        
        data = {
            'title': 'Test Homework',
            'description': 'Test Description',
            'subject': SubjectEnum.MATHEMATICS.value,
            'due_date': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%dT%H:%M'),
            'file': (file_data, 'test.pdf')
        }
        
        response = auth_teacher_client.post(
            url_for('teacher.homework'),
            data=data,
            content_type='multipart/form-data',
            follow_redirects=True
        )
        
        assert response.status_code == 200
        assert b'Homework assigned successfully!' in response.data
        
        # Verify database entry
        with app.app_context():
            homework = Homework.query.filter_by(title='Test Homework').first()
            assert homework is not None
            assert homework.subject == SubjectEnum.MATHEMATICS
            assert os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], 
                                             os.path.basename(homework.file_path)))

    def test_attendance_marking(self, auth_teacher_client, app):
        """Test attendance marking functionality"""
        with app.app_context():
            student = User.query.filter_by(role='student').first()
            
            data = {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'students': [str(student.id)],
                f'status_{student.id}': 'present',
                'remarks': 'Test remarks'
            }
            
            response = auth_teacher_client.post(
                url_for('teacher.attendance'),
                data=data,
                follow_redirects=True
            )
            
            assert response.status_code == 200
            assert b'Student attendance marked successfully!' in response.data
            
            # Verify attendance record
            attendance = Attendance.query.filter_by(user_id=student.id).first()
            assert attendance is not None
            assert attendance.status == 'present'

    def test_invalid_homework_creation(self, auth_teacher_client):
        """Test homework creation with invalid data"""
        data = {
            'title': '',  # Invalid: empty title
            'description': 'Test Description',
            'subject': 'INVALID_SUBJECT',  # Invalid subject
            'due_date': 'invalid-date'  # Invalid date format
        }
        
        response = auth_teacher_client.post(
            url_for('teacher.homework'),
            data=data,
            follow_redirects=True
        )
        
        assert response.status_code == 200
        assert b'Please fill in all required fields' in response.data

    def test_unique_filename_generation(self, auth_teacher_client, app):
        """Test unique filename generation for multiple uploads"""
        file_data = BytesIO(b'Test file content')
        
        # Submit same file twice
        for i in range(2):
            data = {
                'title': f'Test Homework {i}',
                'description': 'Test Description',
                'subject': SubjectEnum.MATHEMATICS.value,
                'due_date': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%dT%H:%M'),
                'file': (file_data, 'test.pdf')
            }
            
            auth_teacher_client.post(
                url_for('teacher.homework'),
                data=data,
                content_type='multipart/form-data',
                follow_redirects=True
            )
        
        # Verify unique filenames
        with app.app_context():
            homeworks = Homework.query.all()
            filenames = [hw.file_path for hw in homeworks]
            assert len(set(filenames)) == 2  # All filenames should be unique

class TestErrorHandling:
    def test_unauthorized_access(self, client):
        """Test unauthorized access to teacher routes"""
        response = client.get(url_for('teacher.dashboard'))
        assert response.status_code == 302  # Should redirect to login
        
    def test_student_access_denied(self, client, init_database):
        """Test student cannot access teacher routes"""
        # Login as student
        client.post(url_for('auth.login'), data={
            'email': 'student@test.com',
            'password': 'password123'
        }, follow_redirects=True)
        
        response = client.get(url_for('teacher.dashboard'))
        assert response.status_code == 302
        assert b'You need to be a teacher to access this page.' in response.follow_redirects().data 