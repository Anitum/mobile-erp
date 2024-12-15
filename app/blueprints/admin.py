from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from app.models.user import User
from app.models.report import DailyReport
from app.models.assignment import AdminAssignment
from app.models.message import Message
from app import db
import os
from werkzeug.utils import secure_filename
from functools import wraps

admin = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('You need to be an admin to access this page.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@admin.route('/admin/dashboard')
@login_required
@admin_required
def dashboard():
    reports = DailyReport.query.order_by(DailyReport.date.desc()).limit(5).all()
    unread_messages = Message.query.filter_by(receiver_id=current_user.id, is_read=False).count()
    total_messages = Message.query.count()
    teachers = User.query.filter_by(role='teacher').count()
    students = User.query.filter_by(role='student').count()
    return render_template('admin/dashboard.html', 
                         reports=reports, 
                         unread_messages=unread_messages,
                         total_messages=total_messages,
                         teachers=teachers,
                         students=students)

@admin.route('/admin/reports')
@login_required
@admin_required
def view_reports():
    reports = DailyReport.query.order_by(DailyReport.date.desc()).all()
    return render_template('admin/reports.html', reports=reports)

@admin.route('/admin/assignments', methods=['GET', 'POST'])
@login_required
@admin_required
def assignments():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        deadline = request.form.get('deadline')
        assigned_to = request.form.get('assigned_to')
        file = request.files.get('file')

        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
            file_path = filename
        else:
            file_path = None

        assignment = AdminAssignment(
            title=title,
            content=content,
            deadline=deadline,
            assigned_to=assigned_to,
            file_path=file_path
        )
        db.session.add(assignment)
        db.session.commit()
        flash('Assignment created successfully!', 'success')
        return redirect(url_for('admin.assignments'))

    assignments = AdminAssignment.query.order_by(AdminAssignment.date_posted.desc()).all()
    return render_template('admin/assignments.html', assignments=assignments)

@admin.route('/admin/messages', methods=['GET', 'POST'])
@login_required
@admin_required
def messages():
    if request.method == 'POST':
        receiver_id = request.form.get('receiver_id')
        subject = request.form.get('subject')
        content = request.form.get('content')
        file = request.files.get('file')

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
        return redirect(url_for('admin.messages'))

    received_messages = Message.query.filter_by(receiver_id=current_user.id).order_by(Message.timestamp.desc()).all()
    sent_messages = Message.query.filter_by(sender_id=current_user.id).order_by(Message.timestamp.desc()).all()
    users = User.query.filter(User.id != current_user.id).all()
    return render_template('admin/messages.html', 
                         received_messages=received_messages,
                         sent_messages=sent_messages,
                         users=users)
