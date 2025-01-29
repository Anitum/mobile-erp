from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from app.models.homework import Homework, HomeworkSubmission
from app.models.message import Message
from app.models.user import User
from app import db
import os
import json
from werkzeug.utils import secure_filename
from datetime import datetime
from functools import wraps

student = Blueprint('student', __name__)

def student_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'student':
            flash('You need to be a student to access this page.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

# Add template filter
@student.app_template_filter('parse_json')
def parse_json_filter(s):
    try:
        return json.loads(s) if s else []
    except:
        return []

@student.app_template_filter('datetimeformat')
def datetimeformat_filter(value, format='%Y-%m-%d %H:%M'):
    return value.strftime(format)

@student.route('/student/dashboard')
@login_required
@student_required
def dashboard():
    # Get pending homework
    pending_homework = Homework.query.filter(
        Homework.due_date >= datetime.utcnow()
    ).order_by(Homework.due_date).limit(5).all()
    
    # Get unread messages
    unread_messages = Message.query.filter_by(
        receiver_id=current_user.id,
        is_read=False
    ).count()
    
    return render_template('student/dashboard.html',
                         pending_homework=pending_homework,
                         unread_messages=unread_messages)

@student.route('/student/homework')
@login_required
@student_required
def homework_list():
    homework = Homework.query.order_by(Homework.due_date.desc()).all()
    submissions = HomeworkSubmission.query.filter_by(student_id=current_user.id).all()
    submitted_hw_ids = [sub.homework_id for sub in submissions]
    
    return render_template('student/homework.html',
                         homework=homework,
                         submitted_hw_ids=submitted_hw_ids)

@student.route('/student/submit-homework/<int:homework_id>', methods=['GET', 'POST'])
@login_required
@student_required
def submit_homework(homework_id):
    homework = Homework.query.get_or_404(homework_id)
    
    if request.method == 'POST':
        files = request.files.getlist('homework_files')
        comments = request.form.get('comments')
        
        file_paths = []
        for file in files:
            if file and file.filename:
                filename = secure_filename(file.filename)
                timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
                filename = f"{timestamp}_{filename}"
                file_path = os.path.join('uploads', filename)
                full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                file.save(full_path)
                file_paths.append(file_path)
        
        if file_paths:
            submission = HomeworkSubmission(
                homework_id=homework_id,
                student_id=current_user.id,
                file_path=json.dumps(file_paths),
                comments=comments
            )
            db.session.add(submission)
            db.session.commit()
            flash('Homework submitted successfully!', 'success')
            return redirect(url_for('student.homework_list'))
        else:
            flash('Please upload at least one file', 'danger')
            
    return render_template('student/submit_homework.html', homework=homework)


@student.route('/student/messages')
@login_required
@student_required
def messages():
    received_messages = Message.query.filter_by(receiver_id=current_user.id).order_by(Message.timestamp.desc()).all()
    sent_messages = Message.query.filter_by(sender_id=current_user.id).order_by(Message.timestamp.desc()).all()
    teachers = User.query.filter_by(role='teacher').all()
    admins = User.query.filter_by(role='admin').all()
    unread_messages = Message.query.filter_by(receiver_id=current_user.id, is_read=False).count()
    
    return render_template('student/messages.html',
                         received_messages=received_messages,
                         sent_messages=sent_messages,
                         teachers=teachers,
                         admins=admins,
                         unread_messages=unread_messages)



@student.route('/student/send-message', methods=['POST'])
@login_required
@student_required
def send_message():
    receiver_id = request.form.get('receiver_id')
    subject = request.form.get('subject')
    content = request.form.get('content')
    file = request.files.get('attachment')
    
    if file:
        filename = secure_filename(file.filename)
        file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
        file_path = filename
    else:
        file_path = None
        
    message = Message(
        sender_id=current_user.id,
        receiver_id=receiver_id,
        subject=subject,
        content=content,
        file_path=file_path
    )
    
    db.session.add(message)
    db.session.commit()
    
    flash('Message sent successfully!', 'success')
    return redirect(url_for('student.messages'))


@student.route('/student/mark-message-read/<int:message_id>', methods=['POST'])
@login_required
@student_required
def mark_message_read(message_id):
    message = Message.query.get_or_404(message_id)
    if message.receiver_id == current_user.id:
        message.is_read = True
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False}), 403
