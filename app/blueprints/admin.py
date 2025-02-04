from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from app.models.user import User
from app.models.report import DailyReport
from app.models.assignment import AdminAssignment
from app.models.message import Message
from app.models.TeacherTask import TeacherTask
from app import db
import os
from werkzeug.utils import secure_filename
from functools import wraps
from datetime import datetime
from datetime import timedelta
from app.models.homework import Homework
from app.models.homework import HomeworkSubmission
from app.models.attendance import Attendance

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
    today = datetime.now().date()
    
    # Basic stats
    reports = DailyReport.query.order_by(DailyReport.date.desc()).limit(5).all()
    unread_messages = Message.query.filter_by(receiver_id=current_user.id, is_read=False).count()
    total_messages = Message.query.count()
    teachers = User.query.filter_by(role='teacher').count()
    students = User.query.filter_by(role='student').count()
    tasks = TeacherTask.query.order_by(TeacherTask.created_at.desc()).all()

    # Task chart data preparation
    task_data = {}
    task_details = []
    task_colors = []
    task_border_colors = []
    
    color_map = {
        'high': 'rgba(220, 53, 69, 0.5)',
        'medium': 'rgba(255, 193, 7, 0.5)',
        'low': 'rgba(23, 162, 184, 0.5)'
    }
    border_color_map = {
        'high': 'rgb(220, 53, 69)',
        'medium': 'rgb(255, 193, 7)',
        'low': 'rgb(23, 162, 184)'
    }

    # Group tasks by date
    for task in tasks:
        date_str = task.created_at.strftime('%Y-%m-%d')
        if date_str not in task_data:
            task_data[date_str] = {
                'count': 0,
                'details': []
            }
        task_data[date_str]['count'] += 1
        task_data[date_str]['details'].append({
            'priority': task.priority,
            'due_date': task.due_date.strftime('%Y-%m-%d %H:%M'),
            'title': task.title
        })

    # Sort dates and prepare final data
    task_dates = sorted(task_data.keys())
    task_counts = []
    task_details = []
    task_colors = []
    task_border_colors = []

    for date in task_dates:
        task_counts.append(task_data[date]['count'])
        task_details.append(task_data[date]['details'])
        
        # Get predominant priority if there are tasks
        if task_data[date]['details']:
            priorities = [d['priority'] for d in task_data[date]['details']]
            predominant = max(set(priorities), key=priorities.count)
        else:
            predominant = 'medium'
            
        task_colors.append(color_map[predominant])
        task_border_colors.append(border_color_map[predominant])

    # Format dates for display
    display_dates = [datetime.strptime(date, '%Y-%m-%d').strftime('%b %d') for date in task_dates]

    return render_template('admin/dashboard.html',
                         reports=reports,
                         unread_messages=unread_messages,
                         total_messages=total_messages,
                         teachers=teachers,
                         students=students,
                         teachers_present=0,
                         students_present=0,
                         tasks=tasks,
                         # Chart data
                         task_dates=display_dates,
                         task_counts=task_counts,
                         task_colors=task_colors,
                         task_border_colors=task_border_colors,
                         task_details=task_details)
@admin.route('/admin/reports')
@login_required
@admin_required
def view_reports():
    reports = DailyReport.query.order_by(DailyReport.date.desc()).all()
    return render_template('admin/reports.html', reports=reports)

@admin.route('/admin/teacher/<int:teacher_id>/profile')
@login_required
@admin_required
def teacher_profile(teacher_id):
    # Get teacher info
    teacher = User.query.filter_by(id=teacher_id, role='teacher').first_or_404()
    
    # Calculate attendance rate
    thirty_days_ago = datetime.now() - timedelta(days=30)
    attendance_records = Attendance.query.filter(
        Attendance.user_id == teacher_id,
        Attendance.date >= thirty_days_ago
    ).all()
    
    present_count = len([a for a in attendance_records if a.status == 'present'])
    attendance_rate = (present_count / 30) * 100 if attendance_records else 0
    
    # Get task statistics
    tasks = TeacherTask.query.filter_by(assigned_to=teacher_id).all()
    completed_tasks = len([t for t in tasks if t.status == 'completed'])
    total_tasks = len(tasks)
    
    # Get reports statistics
    this_month = datetime.now().replace(day=1)
    reports = DailyReport.query.filter(
        DailyReport.teacher_id == teacher_id,
        DailyReport.date >= this_month
    ).all()
    reports_submitted = len(reports)
    
    # Get recent activities (combine attendance, tasks, reports)
    recent_activities = []
    
    # Add attendance activities
    for record in attendance_records[:5]:
        recent_activities.append({
            'title': 'Attendance',
            'description': f'Marked as {record.status}',
            'timestamp': record.created_at,
            'type_color': 'success' if record.status == 'present' else 'warning'
        })
    
    # Add task activities
    for task in tasks[:5]:
        recent_activities.append({
            'title': 'Task',
            'description': f"{task.title} - {task.status}",
            'timestamp': task.completed_at or task.created_at,
            'type_color': 'info'
        })
    
    # Add report activities
    for report in reports[:5]:
        recent_activities.append({
            'title': 'Daily Report',
            'description': f"Submitted daily report with rating {report.cleanliness_rating}",
            'timestamp': report.date,
            'type_color': 'primary'
        })
    
    # Sort activities by timestamp
    recent_activities.sort(key=lambda x: x['timestamp'], reverse=True)
    recent_activities = recent_activities[:10]  # Keep only 10 most recent
    
    # Get current tasks
    current_tasks = TeacherTask.query.filter_by(
        assigned_to=teacher_id,
        status='pending'
    ).order_by(TeacherTask.due_date.asc()).limit(5).all()
    
    # Process tasks for display
    processed_tasks = []
    for task in current_tasks:
        total_time = (task.due_date - task.created_at).total_seconds()
        time_left = (task.due_date - datetime.now()).total_seconds()
        progress = min(100, max(0, ((total_time - time_left) / total_time) * 100))
        
        processed_tasks.append({
            'title': task.title,
            'due_date': task.due_date,
            'progress': round(progress, 1),
            'status_color': 'danger' if progress > 75 else 'warning' if progress > 50 else 'info'
        })
    
    # Get homework data
    recent_homework = Homework.query.filter_by(teacher_id=teacher_id)\
        .order_by(Homework.created_at.desc()).limit(5).all()
    
    # Process homework for display
    processed_homework = []
    for hw in recent_homework:
        submissions = HomeworkSubmission.query.filter_by(homework_id=hw.id).count()
        total_students = User.query.filter_by(role='student').count()
        
        processed_homework.append({
            'title': hw.title,
            'subject': hw.subject.value,
            'due_date': hw.due_date,
            'status': 'Active' if hw.due_date > datetime.now() else 'Expired',
            'status_color': 'success' if hw.due_date > datetime.now() else 'danger',
            'submission_count': submissions,
            'total_students': total_students
        })
    
    # Prepare chart data for attendance
    attendance_labels = []
    attendance_data = []
    
    for i in range(30, 0, -1):
        date = datetime.now() - timedelta(days=i)
        attendance_labels.append(date.strftime('%Y-%m-%d'))
        
        record = Attendance.query.filter_by(
            user_id=teacher_id,
            date=date.date()
        ).first()
        
        # Calculate attendance percentage for that day
        if record and record.status == 'present':
            attendance_data.append(100)
        elif record and record.status == 'late':
            attendance_data.append(50)
        else:
            attendance_data.append(0)
    
    # Prepare chart data for reports quality
    report_labels = []
    report_data = []
    
    last_10_reports = DailyReport.query.filter_by(teacher_id=teacher_id)\
        .order_by(DailyReport.date.desc()).limit(10).all()
    
    for report in reversed(last_10_reports):
        report_labels.append(report.date.strftime('%Y-%m-%d'))
        report_data.append(report.cleanliness_rating or 0)
    
    return render_template(
        'admin/teacher_profile.html',
        teacher=teacher,
        attendance_rate=attendance_rate,
        completed_tasks=completed_tasks,
        total_tasks=total_tasks,
        reports_submitted=reports_submitted,
        recent_activities=recent_activities,
        current_tasks=processed_tasks,
        recent_homework=processed_homework,
        attendance_labels=attendance_labels,
        attendance_data=attendance_data,
        report_labels=report_labels,
        report_data=report_data
    )


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


from datetime import datetime, timedelta
from app.models.attendance import Attendance
from app.models.user import User

@admin.route('/admin/attendance')
@login_required
@admin_required
def view_attendance():
    # Get filter parameters
    date = request.args.get('date', datetime.now().date())
    if isinstance(date, str):
        date = datetime.strptime(date, '%Y-%m-%d').date()
    role = request.args.get('role', 'all')
    
    # Get attendance records
    attendance_records = Attendance.get_attendance_by_date(date, role)
    
    # Get all users for comparison
    users_query = User.query.filter_by(is_active=True)
    if role != 'all':
        users_query = users_query.filter_by(role=role)
    users = users_query.all()
    
    # Calculate statistics
    total_users = len(users)
    present_users = len([a for a in attendance_records if a.status == 'present'])
    absent_users = len([a for a in attendance_records if a.status == 'absent'])
    late_users = len([a for a in attendance_records if a.status == 'late'])
    
    return render_template('admin/attendance.html',
                         date=date,
                         role=role,
                         attendance_records=attendance_records,
                         users=users,
                         stats={
                             'total': total_users,
                             'present': present_users,
                             'absent': absent_users,
                             'late': late_users
                         })

@admin.route('/admin/attendance/user/<int:user_id>')
@login_required
@admin_required
def user_attendance(user_id):
    user = User.query.get_or_404(user_id)
    
    # Get date range
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=30)  # Last 30 days by default
    
    attendance_records = Attendance.get_user_attendance(user_id, start_date, end_date)
    
    # Calculate statistics
    total_days = (end_date - start_date).days + 1
    present_days = len([a for a in attendance_records if a.status == 'present'])
    absent_days = len([a for a in attendance_records if a.status == 'absent'])
    late_days = len([a for a in attendance_records if a.status == 'late'])
    
    return render_template('admin/user_attendance.html',
                         user=user,
                         attendance_records=attendance_records,
                         start_date=start_date,
                         end_date=end_date,
                         stats={
                             'total_days': total_days,
                             'present_days': present_days,
                             'absent_days': absent_days,
                             'late_days': late_days
                         })

@admin.route('/admin/attendance/mark', methods=['POST'])
@login_required
@admin_required
def mark_attendance():
    user_id = request.form.get('user_id')
    date = request.form.get('date')
    status = request.form.get('status')
    remarks = request.form.get('remarks')
    
    if not all([user_id, date, status]):
        flash('Missing required fields', 'danger')
        return redirect(url_for('admin.view_attendance'))
    
    date = datetime.strptime(date, '%Y-%m-%d').date()
    
    # Check if attendance already exists
    attendance = Attendance.query.filter_by(user_id=user_id, date=date).first()
    if attendance:
        attendance.status = status
        attendance.remarks = remarks
        attendance.recorded_by = current_user.id
    else:
        attendance = Attendance(
            user_id=user_id,
            date=date,
            status=status,
            remarks=remarks,
            recorded_by=current_user.id
        )
        db.session.add(attendance)
    
    db.session.commit()
    flash('Attendance marked successfully', 'success')
    return redirect(url_for('admin.view_attendance'))


# In admin.py
@admin.route('/all_attendance')
@login_required
@admin_required
def all_attendance():
    # Add your attendance viewing logic here
    attendances = Attendance.query.order_by(Attendance.date.desc()).all()
    return render_template('admin/all_attendance.html', attendances=attendances)



@admin.route('/tasks', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_tasks():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        assigned_to = request.form.get('assigned_to')
        due_date = request.form.get('due_date')
        priority = request.form.get('priority', 'medium')

        file = request.files.get('task_file')
        print(file)
        file_path = None
        if file:
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{timestamp}_{filename}"
            file_path = os.path.join('uploads', filename)
            full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(full_path)


        try:
            due_date = datetime.strptime(due_date, '%Y-%m-%dT%H:%M')
            task = TeacherTask(
                title=title,
                description=description,
                assigned_to=assigned_to,
                assigned_by=current_user.id,
                due_date=due_date,
                priority=priority,
                task_file=file_path
            )
            db.session.add(task)
            db.session.commit()
            flash('Task assigned successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Error assigning task. Please try again.', 'danger')
            print(f"Error: {str(e)}")

        return redirect(url_for('admin.manage_tasks'))

    teachers = User.query.filter_by(role='teacher').all()
    tasks = TeacherTask.query.order_by(TeacherTask.created_at.desc()).all()
    return render_template('admin/tasks.html', teachers=teachers, tasks=tasks)
