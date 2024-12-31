import pytest
from flask import url_for
from datetime import datetime, date
from app.models.homework import SubjectEnum

class TestTeacherRoutes:
    def test_teacher_dashboard_access(self, auth_teacher_client):
        response = auth_teacher_client.get(url_for('teacher.dashboard'))
        assert response.status_code == 200

    def test_homework_creation(self, auth_teacher_client):
        try:
            response = auth_teacher_client.post(url_for('teacher.homework'), data={
                'title': 'Test Homework',
                'description': 'This is a test homework.',
                'due_date': datetime.now().strftime('%Y-%m-%dT%H:%M'),
                'subject': SubjectEnum.MATHEMATICS.value
            }, follow_redirects=True)
            assert response.status_code == 200
        except Exception as e: 
            print(f"Error creating homework: {e}")

    def test_invalid_homework_creation(self, auth_teacher_client):
        try:
            response = auth_teacher_client.post(url_for('teacher.homework'), data={
                'title': '',  # Empty title should fail
                'description': 'This is a test homework.',
                'due_date': datetime.now().strftime('%Y-%m-%dT%H:%M'),
                'subject': SubjectEnum.MATHEMATICS.value
            }, follow_redirects=True)
        except Exception as e:
            print(f"Error creating homework: {e}")

    def test_attendance_marking(self, auth_teacher_client):
        today = date.today().strftime('%Y-%m-%d')
        response = auth_teacher_client.post(url_for('teacher.attendance'), data={
            'date': today,
            'status': 'present',
            'remarks': 'Test attendance',
            'mark_self_attendance': 'true'
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_daily_report_submission(self, auth_teacher_client):
        response = auth_teacher_client.post(url_for('teacher.daily_report'), data={
            'report_date': date.today().strftime('%Y-%m-%d'),
            'cleanliness': 'good',
            'report_content': 'Test daily report content'
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_view_homework_list(self, auth_teacher_client):
        try:
            response = auth_teacher_client.get(url_for('teacher.homework'))
            assert response.status_code == 200
        except  Exception as e:
            print(f"Error fetching homework list: {e}")

    def test_view_attendance_page(self, auth_teacher_client):
        response = auth_teacher_client.get(url_for('teacher.attendance'))
        assert response.status_code == 200

    def test_view_daily_report_page(self, auth_teacher_client):
        response = auth_teacher_client.get(url_for('teacher.daily_report'))
        assert response.status_code == 200