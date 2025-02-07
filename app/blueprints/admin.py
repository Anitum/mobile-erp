from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, jsonify
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
from pytz import timezone

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
    tasks = TeacherTask.query.order_by(TeacherTask.created_at.desc()).all()
    total_teachers = User.query.filter_by(role='teacher').count()
    total_students = User.query.filter_by(role='student').count()
    weekly_stats = Attendance.get_weekly_attendance_stats()
    teachers_present = Attendance.query.join(
        User, 
        User.id == Attendance.user_id
    ).filter(
        Attendance.date == today,
        Attendance.status == 'present',
        User.role == 'teacher'
    ).count()

    students_present = Attendance.query.join(
        User,
        User.id == Attendance.user_id
    ).filter(
        Attendance.date == today,
        Attendance.status == 'present',
        User.role == 'student'
    ).count()

    unread_reports = DailyReport.query.filter_by(status='pending').count()
    unread_reports_list = DailyReport.query.filter_by(status='pending')\
        .order_by(DailyReport.date.desc())\
        .limit(5)\
        .all()

    # Get today's teacher attendance for the table
    teacher_attendance = db.session.query(
        Attendance,
        db.func.concat(User.first_name, ' ', User.last_name).label('teacher_name'),
        User.id.label('teacher_id')
    ).join(
        User,
        User.id == Attendance.user_id
    ).filter(
        Attendance.date == today,
        User.role == 'teacher'
    ).all()

    chart_data = {
        'labels': [stat['date_label'] for stat in weekly_stats],
        'datasets': [
            {
                'present': [stat['present'] for stat in weekly_stats],
                'absent': [stat['absent'] for stat in weekly_stats],
                'late': [stat['late'] for stat in weekly_stats],
            }
        ],
        'details': [
            {
                'date': stat['date'].isoformat(),
                'day': stat['day_name'],
                'present_count': stat['present_count'],
                'absent_count': stat['absent_count'],
                'late_count': stat['late_count'],
                'total': stat['total']
            } for stat in weekly_stats
        ]
    }
    

    # Process teacher attendance for display
    teacher_attendance_list = []
    for record in teacher_attendance:
        teacher_attendance_list.append({
            'teacher_id': record.teacher_id,
            'teacher_name': record.teacher_name,
            'check_in_time': record.Attendance.check_in_time,
            'is_late': record.Attendance.status == 'late'
        })

    weekly_labels = []
    weekly_present_data = []
    weekly_absent_data = []

    for i in range(7):
        date = today - timedelta(days=i)
        weekly_labels.append(date.strftime('%a'))
        
        total = User.query.count()
        present = Attendance.query.filter(
            Attendance.date == date,
            Attendance.status == 'present'
        ).count()
        
        present_percentage = (present / total * 100) if total > 0 else 0
        absent_percentage = 100 - present_percentage
        
        weekly_present_data.append(present_percentage)
        weekly_absent_data.append(absent_percentage)
    
    weekly_labels.reverse()
    weekly_present_data.reverse()
    weekly_absent_data.reverse()
    
    # Task chart data preparation
    task_data = {}
    
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
                         teacher_attendance=teacher_attendance_list,  # Make sure this is passed
                         total_teachers=total_teachers,
                         total_students=total_students,
                         teachers_present=teachers_present,
                         students_present=students_present,
                         unread_reports=unread_reports,
                         unread_reports_list=unread_reports_list,
                         weekly_labels=weekly_labels,
                         weekly_present_data=weekly_present_data,
                         weekly_absent_data=weekly_absent_data,
                         reports=reports,
                         unread_messages=unread_messages,
                         total_messages=total_messages,
                         tasks=tasks,
                         task_dates=display_dates,
                         task_counts=task_counts,
                         task_colors=task_colors,
                         task_border_colors=task_border_colors,
                         task_details=task_details,
                         chart_data=chart_data
                         )

@admin.route('/admin/reports')
@login_required
@admin_required
def view_reports():
    # Get filter parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    status = request.args.get('status')
    
    # Base query
    reports_query = DailyReport.query
    
    # Apply filters if provided
    if start_date:
        reports_query = reports_query.filter(DailyReport.date >= datetime.strptime(start_date, '%Y-%m-%d'))
    if end_date:
        reports_query = reports_query.filter(DailyReport.date <= datetime.strptime(end_date, '%Y-%m-%d'))
    if status:
        reports_query = reports_query.filter(DailyReport.status == status)
    
    # Get reports with teacher information
    reports = reports_query.join(
        User, User.id == DailyReport.teacher_id
    ).add_columns(
        User.first_name,
        User.last_name
    ).order_by(DailyReport.date.desc()).all()
    
    # Process reports for display
    processed_reports = []
    for report, first_name, last_name in reports:
        # Calculate average cleanliness rating
        cleanliness_components = [
            'floor', 'bench', 'whiteboard', 'door', 'walls', 'dustbin'
        ]
        
        ratings = []
        component_details = {}
        
        for component in cleanliness_components:
            rating = getattr(report, f'{component}_rating', None)
            photo = getattr(report, f'{component}_photo', None)
            remarks = getattr(report, f'{component}_remarks', None)
            
            if rating:
                ratings.append(rating)
            
            component_details[component] = {
                'rating': rating,
                'photo': photo,
                'remarks': remarks
            }
        
        avg_rating = sum(ratings) / len(ratings) if ratings else 0
        
        # Format report data
        processed_report = {
            'id': report.id,
            'teacher_name': f"{first_name} {last_name}",
            'date': report.date,
            'content': report.content,
            'status': report.status,
            'cleanliness_rating': report.cleanliness_rating,
            'average_component_rating': round(avg_rating, 2),
            'component_details': component_details,
            'file_path': report.file_path,
            'components': cleanliness_components  # Pass list of components for iteration in template
        }
        
        processed_reports.append(processed_report)
    
    # Calculate overall statistics
    total_reports = len(processed_reports)
    avg_cleanliness = sum(r['cleanliness_rating'] or 0 for r in processed_reports) / total_reports if total_reports > 0 else 0
    pending_reports = sum(1 for r in processed_reports if r['status'] == 'pending')
    
    stats = {
        'total_reports': total_reports,
        'average_cleanliness': round(avg_cleanliness, 2),
        'pending_reports': pending_reports
    }
    
    return render_template(
        'admin/reports.html',
        reports=processed_reports,
        stats=stats,
        current_filters={
            'start_date': start_date,
            'end_date': end_date,
            'status': status
        }
    )

@admin.route('/admin/reports/<int:report_id>/toggle-status', methods=['POST'])
@login_required
@admin_required
def toggle_report_status(report_id):
    report = DailyReport.query.get_or_404(report_id)
    report.status = 'reviewed' if report.status == 'pending' else 'pending'
    db.session.commit()
    return jsonify({
        'success': True,
        'new_status': report.status
    })

@admin.route('/admin/reports/statistics')
@login_required
@admin_required
def get_report_statistics():
    """API endpoint for report statistics"""
    # Get date range
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    query = DailyReport.query
    
    if start_date:
        query = query.filter(DailyReport.date >= datetime.strptime(start_date, '%Y-%m-%d'))
    if end_date:
        query = query.filter(DailyReport.date <= datetime.strptime(end_date, '%Y-%m-%d'))
    
    reports = query.all()
    
    # Calculate statistics for each component
    components = ['floor', 'bench', 'whiteboard', 'door', 'walls', 'dustbin']
    component_stats = {}
    
    for component in components:
        ratings = [getattr(report, f'{component}_rating', 0) for report in reports if getattr(report, f'{component}_rating', 0)]
        
        component_stats[component] = {
            'average': round(sum(ratings) / len(ratings), 2) if ratings else 0,
            'total_ratings': len(ratings),
            'distribution': {
                '5': ratings.count(5),
                '4': ratings.count(4),
                '3': ratings.count(3),
                '2': ratings.count(2),
                '1': ratings.count(1)
            }
        }
    
    return jsonify({
        'success': True,
        'stats': component_stats
    })

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
        report_data=report_data,
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

        file_path = None
        if file:
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{timestamp}_{filename}"
            # Store only the filename, not the full path
            file_path = filename
            # Use full path only for saving
            full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(full_path)

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

@admin.route('/admin/tasks/<int:task_id>/details')
@login_required
@admin_required
def get_task_details(task_id):
    task = TeacherTask.query.get_or_404(task_id)
    completion_image_url = None
    if task.completion_image:
        completion_image_url = url_for('static', filename=task.completion_image)

    return jsonify({
        'id': task.id,
        'title': task.title,
        'description': task.description,
        'assigned_to': f"{task.assignee.first_name} {task.assignee.last_name}",
        'assigned_by': f"{task.assigner.first_name} {task.assigner.last_name}",
        'due_date': task.due_date.strftime('%Y-%m-%d %H:%M'),
        'created_at': task.created_at.strftime('%Y-%m-%d %H:%M'),
        'status': task.status,
        'priority': task.priority,
        'completion_notes': task.completion_notes,
        'completion_image': completion_image_url,
        'completed_at': task.completed_at.strftime('%Y-%m-%d %H:%M') if task.completed_at else None,
        'task_file': task.task_file
    })

@admin.route('/admin/tasks/<int:task_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_task(task_id):
    task = TeacherTask.query.get_or_404(task_id)
    try:
        db.session.delete(task)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Task deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@admin.route('/admin/-file/<filename>')
@login_required
@admin_required
def view_task_file(filename):
    try:
        return send_from_directory(
            current_app.config['UPLOAD_FOLDER'],
            filename,
            as_attachment=False
        )
    except FileNotFoundError:
        flash('File not found', 'error')
        return redirect(url_for('admin.manage_tasks'))

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
@admin.route('/api/weekly-attendance')
@login_required
@admin_required
def get_weekly_attendance():
    try:
        weekly_stats = Attendance.get_weekly_attendance_stats()
        return jsonify({
            'success': True,
            'data': weekly_stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

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
