from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from app.models.user import User
from app import db
from datetime import datetime
from werkzeug.utils import secure_filename
import os
from functools import wraps

teacher = Blueprint('teacher', __name__)

def teacher_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'teacher':
            flash('You need to be a teacher to access this page.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@teacher.route('/teacher/dashboard')
@login_required
@teacher_required
def dashboard():
    return render_template('teacher/dashboard.html')

@teacher.route('/teacher/attendance', methods=['GET', 'POST'])
@login_required
@teacher_required
def attendance():
    if request.method == 'POST':
        # Handle attendance submission
        date = request.form.get('date')
        students = request.form.getlist('students')
        # Save attendance logic here
        flash('Attendance marked successfully!', 'success')
        return redirect(url_for('teacher.attendance'))
    
    students = User.query.filter_by(role='student').all()
    return render_template('teacher/attendance.html', students=students)

@teacher.route('/teacher/homework', methods=['GET', 'POST'])
@login_required
@teacher_required
def homework():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        due_date = request.form.get('due_date')
        file = request.files.get('file')
        
        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
        
        # Save homework logic here
        flash('Homework assigned successfully!', 'success')
        return redirect(url_for('teacher.homework'))
    
    return render_template('teacher/homework.html')

@teacher.route('/teacher/daily-report', methods=['GET', 'POST'])
@login_required
@teacher_required
def daily_report():
    if request.method == 'POST':
        report_content = request.form.get('report')
        cleanliness_rating = request.form.get('cleanliness')
        completed_tasks = request.form.getlist('completed_tasks')
        
        # Save report logic here
        flash('Daily report submitted successfully!', 'success')
        return redirect(url_for('teacher.daily_report'))
    
    return render_template('teacher/daily_report.html')

@teacher.route('/teacher/messages', methods=['GET', 'POST'])
@login_required
@teacher_required
def messages():
    if request.method == 'POST':
        receiver_id = request.form.get('receiver_id')
        message_content = request.form.get('message')
        file = request.files.get('file')
        
        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
        
        # Save message logic here
        flash('Message sent successfully!', 'success')
        return redirect(url_for('teacher.messages'))
    
    return render_template('teacher/messages.html')
