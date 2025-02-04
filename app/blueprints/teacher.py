from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from app.models.user import User
from app.models.homework import Homework
from app.models.TeacherTask import TeacherTask
from app import db
from datetime import datetime
from werkzeug.utils import secure_filename
import os
from functools import wraps
from app.models.homework import SubjectEnum
import json

from app.models.report import DailyReport  # Import the DailyReport model
from datetime import datetime

teacher = Blueprint('teacher', __name__)

def teacher_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'teacher':
            flash('You need to be a teacher to access this page.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function



# routes/teacher.py
from flask import render_template, jsonify, request
from datetime import datetime

@teacher.route('/teacher/dashboard')
@login_required
@teacher_required
def dashboard():

    weekly_attendance = {
        'present': [95, 92, 88, 93, 90],  # Replace with actual data
        'absent': [5, 8, 12, 7, 10]       # Replace with actual data
    }    
    today_attendance = Attendance.get_today_attendance(current_user.id)
    today_date = datetime.now()
    attendance_history = Attendance.query.filter_by(
        user_id=current_user.id
    ).order_by(Attendance.date.desc()).limit(10).all()
    return render_template('teacher/dashboard.html',
                         attendance_history=attendance_history,
                         today_attendance=today_attendance,
                         today_date=today_date,
                         weekly_attendance=weekly_attendance)

@teacher.route('/teacher/check-in', methods=['POST'])
@login_required
@teacher_required
def check_in():
    location = request.form.get('location')
    attendance = Attendance.mark_check_in(current_user.id, location)
    return jsonify({
        'status': 'success',
        'check_in_time': attendance.check_in_time.strftime('%I:%M %p')
    })

@teacher.route('/teacher/check-out', methods=['POST'])
@login_required
@teacher_required
def check_out():
    location = request.form.get('location')
    attendance = Attendance.mark_check_out(current_user.id, location)
    return jsonify({
        'status': 'success',
        'check_out_time': attendance.check_out_time.strftime('%I:%M %p')
    })




from app.models.attendance import Attendance  # Add this import
from app import db
from datetime import datetime, date
from werkzeug.utils import secure_filename
import os
from functools import wraps

# ... (keep existing decorators and other routes)

@teacher.route('/teacher/attendance', methods=['GET', 'POST'])
@login_required
@teacher_required
def attendance():
    if request.method == 'POST':
        attendance_date = datetime.strptime(request.form.get('date'), '%Y-%m-%d').date()
        status = request.form.get('status')
        remarks = request.form.get('remarks')

        if 'mark_self_attendance' in request.form:
            # Handle self attendance
            existing_attendance = Attendance.query.filter_by(
                user_id=current_user.id,
                date=attendance_date
            ).first()

            if existing_attendance:
                flash('You have already marked your attendance for this date!', 'warning')
            else:
                attendance = Attendance(
                    user_id=current_user.id,
                    date=attendance_date,
                    status=status,
                    check_in_time=datetime.now(),
                    remarks=remarks,
                    recorded_by=current_user.id
                )
                db.session.add(attendance)
                flash('Your attendance has been marked successfully!', 'success')

        else:
            # Handle student attendance
            student_ids = request.form.getlist('students')
            status_dict = {student_id: request.form.get(f'status_{student_id}') 
                         for student_id in student_ids}

            for student_id in student_ids:
                if student_id:
                    existing_attendance = Attendance.query.filter_by(
                        user_id=student_id,
                        date=attendance_date
                    ).first()

                    if existing_attendance:
                        existing_attendance.status = status_dict[student_id]
                        existing_attendance.remarks = remarks
                    else:
                        attendance = Attendance(
                            user_id=student_id,
                            date=attendance_date,
                            status=status_dict[student_id],
                            check_in_time=datetime.now(),
                            remarks=remarks,
                            recorded_by=current_user.id
                        )
                        db.session.add(attendance)

            flash('Student attendance marked successfully!', 'success')

        db.session.commit()
        return redirect(url_for('teacher.attendance'))
    
    students = User.query.filter_by(role='student').all()
    today = date.today()
    
    # Get existing attendance records for today
    existing_attendance = Attendance.query.filter_by(date=today).all()
    attendance_dict = {att.user_id: att.status for att in existing_attendance}
    
    return render_template('teacher/attendance.html', 
                         students=students,
                         attendance_dict=attendance_dict,
                         today=today)

@teacher.app_template_filter('parse_json')
def parse_json_filter(s):
    try:
        return json.loads(s) if s else []
    except:
        return []


@teacher.route('/teacher/homework', methods=['GET', 'POST'])
@login_required
@teacher_required
def homework():
    if request.method == 'POST':
        try:
            title = request.form.get('title')
            description = request.form.get('description')
            due_date = request.form.get('due_date')
            subject = request.form.get('subject')

                        # Validate subject is in enum
            if subject not in [s.value for s in SubjectEnum]:
                flash('Invalid subject selected', 'danger')
                return redirect(url_for('teacher.homework'))

            # Validate required fields
            if not all([title, description, due_date]):
                flash('Please fill in all required fields', 'danger')
                return redirect(url_for('teacher.homework'))

            # Convert due_date string to datetime (now handling datetime-local format)
            try:
                due_date = datetime.strptime(due_date, '%Y-%m-%dT%H:%M')  # Changed format to match datetime-local
            except ValueError:
                flash('Invalid date format', 'danger')
                return redirect(url_for('teacher.homework'))

            file_paths = []
            files = request.files.getlist('files')  # Get list of files
            for file in files:
                if file and file.filename:
                    filename = secure_filename(file.filename)
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f"{timestamp}_{filename}"
                    file_path = os.path.join('uploads', filename)
                    full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                    file.save(full_path)
                    file_paths.append(file_path)
            
            # Convert list to JSON string
            file_path_json = json.dumps(file_paths) if file_paths else None

            new_homework = Homework(
                title=title,
                description=description,
                due_date=due_date,
                teacher_id=current_user.id,
                file_path=file_path_json,  # Store JSON string
                subject=subject
            )

            db.session.add(new_homework)
            db.session.commit()
            
            flash('Homework assigned successfully!', 'success')
            return redirect(url_for('teacher.homework'))
      
        except Exception as e:
            db.session.rollback()
            flash('Error assigning homework. Please try again.', 'danger')
            print(f"Error occurred: {str(e)}")  # Keep for debugging
            return redirect(url_for('teacher.homework'))
    
    assignments = Homework.query.filter_by(teacher_id=current_user.id).all()
    
    processed_assignments = []
    for hw in assignments:
        # Process dates and status in Python

        file_list = json.loads(hw.file_path) if hw.file_path else []
        
        is_pending = hw.due_date > datetime.utcnow()
        status = 'pending' if is_pending else 'overdue'
        due_date_str = hw.due_date.strftime('%b %d, %Y %H:%M')
        created_str = hw.created_at.strftime('%b %d')
        subject = str(hw.subject)
        processed_assignments.append({
            'id': hw.id,
            'title': hw.title,
            'subject': subject.split(".")[1].capitalize(),
            'description': hw.description,
            'status': status,
            'due_date': due_date_str,
            'created_at': created_str,
            'file_count': len(file_list),
            'files': file_list
        })
    
    return render_template('teacher/homework.html',
                         assignments=processed_assignments,
                         subjects=SubjectEnum)


@teacher.route('/teacher/daily-report', methods=['GET', 'POST'])
@login_required
@teacher_required
def daily_report():
    if request.method == 'POST':
        try:
            report_date = datetime.strptime(request.form.get('report_date'), '%Y-%m-%d')
            report_content = request.form.get('report_content')
            
            # Initialize new report
            new_report = DailyReport(
                teacher_id=current_user.id,
                date=report_date,
                content=report_content,
                status='pending'
            )
            
            # Process cleanliness components
            components = ['floor', 'bench', 'whiteboard', 'door', 'walls', 'dustbin']
            total_rating = 0
            valid_ratings_count = 0
            
            for component in components:
                # Get rating with safe conversion to integer
                rating = request.form.get(f'{component}_rating', '0')
                try:
                    rating_value = int(rating)
                    if rating_value > 0:  # Only count valid ratings
                        setattr(new_report, f'{component}_rating', rating_value)
                        total_rating += rating_value
                        valid_ratings_count += 1
                except (ValueError, TypeError):
                    setattr(new_report, f'{component}_rating', 0)
                
                # Get remarks
                remarks = request.form.get(f'{component}_remarks')
                if remarks:
                    setattr(new_report, f'{component}_remarks', remarks)
                
                # Process photo
                photo = request.files.get(f'{component}_photo')
                if photo and photo.filename:
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f"{timestamp}_{component}_{secure_filename(photo.filename)}"
                    photo_path = os.path.join('uploads', filename)
                    full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                    photo.save(full_path)
                    setattr(new_report, f'{component}_photo', photo_path)

            # Calculate average cleanliness rating safely
            if valid_ratings_count > 0:
                new_report.cleanliness_rating = round(total_rating / valid_ratings_count, 2)
            else:
                new_report.cleanliness_rating = 0
            
            # Process additional attachments
            attachment_paths = []
            files = request.files.getlist('attachments')
            for file in files:
                if file and file.filename:
                    filename = secure_filename(file.filename)
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f"{timestamp}_attachment_{filename}"
                    file_path = os.path.join('uploads', filename)
                    full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                    file.save(full_path)
                    attachment_paths.append(file_path)
            
            # Store attachments as string
            if attachment_paths:
                new_report.file_path = ','.join(attachment_paths)
            
            # Save to database
            db.session.add(new_report)
            db.session.commit()
            
            flash('Daily report submitted successfully!', 'success')
            return redirect(url_for('teacher.daily_report'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error submitting report: {str(e)}', 'danger')
            print(f"Error details: {str(e)}")  # For debugging
            return redirect(url_for('teacher.daily_report'))

    # For GET request
    today_date = datetime.now().strftime('%Y-%m-%d')
    previous_reports = DailyReport.query.filter_by(
        teacher_id=current_user.id
    ).order_by(DailyReport.date.desc()).all()

    return render_template('teacher/daily_report.html',
                         today_date=today_date,
                         previous_reports=previous_reports)

def allowed_file(filename):
    """Check if file extension is allowed"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@teacher.route('/teacher/report/<int:report_id>/details')
@login_required
@teacher_required
def get_report_details(report_id):
    """API endpoint to get report details for modal view"""
    report = DailyReport.query.get_or_404(report_id)
    
    # Ensure teacher can only view their own reports
    if report.teacher_id != current_user.id:
        pass
    
    components = ['floor', 'bench', 'whiteboard', 'door', 'walls', 'dustbin']
    cleanliness_details = {}
    
    for component in components:
        rating = getattr(report, f'{component}_rating', None)
        photo = getattr(report, f'{component}_photo', None)
        remarks = getattr(report, f'{component}_remarks', None)
        
        if rating or photo or remarks:
            cleanliness_details[component] = {
                'rating': rating,
                'photo': url_for('static', filename=photo) if photo else None,
                'remarks': remarks
            }
    
    return jsonify({
        'date': report.date.strftime('%Y-%m-%d %H:%M'),
        'content': report.content,
        'cleanliness': cleanliness_details,
        'files': report.attachments.split(',') if report.attachments else [],
        'status': report.status
    })


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

@teacher.route('/teacher/tasks')
@login_required
@teacher_required
def view_tasks():
    print("#"*30)
    tasks = TeacherTask.query.filter_by(assigned_to=current_user.id)\
        .order_by(TeacherTask.due_date.asc()).all()
    return render_template('teacher/tasks.html', tasks=tasks, now=datetime.utcnow() )

@teacher.route('/teacher/tasks/<int:task_id>/complete', methods=['POST'])
@login_required
@teacher_required
def complete_task(task_id):
    print("*"*30)
    task = TeacherTask.query.get_or_404(task_id)
    print("*"*30)

    
    # Check if the task belongs to the current teacher
    if task.assigned_to != current_user.id:
        flash('You are not authorized to complete this task.', 'danger')
        return redirect(url_for('teacher.view_tasks'))

    completion_notes = request.form.get('completion_notes')
    completion_image = request.files.get('completion_image')
    print("*"*30)


    if completion_image:
        # Save the image
        filename = secure_filename(completion_image.filename)
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        file_path = os.path.join('uploads', filename)
        full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        
        try:
            completion_image.save(full_path)
            task.completion_image = file_path
        except Exception as e:
            print(f"Error saving image: {str(e)}")
            flash('Error uploading image. Task was not marked as complete.', 'danger')
            return redirect(url_for('teacher.view_tasks'))

    # Update task status and details
    task.status = 'completed'
    task.completion_notes = completion_notes
    task.completed_at = datetime.utcnow()
    print("*"*30)


    try:
        db.session.commit()
        flash('Task marked as completed successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        print(f"Error completing task: {str(e)}")
        flash('Error marking task as complete. Please try again.', 'danger')

    print("*"*30)

    return redirect(url_for('teacher.view_tasks'))
