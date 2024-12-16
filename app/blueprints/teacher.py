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

from app.models.report import DailyReport  # Import the DailyReport model
from datetime import datetime

@teacher.route('/teacher/daily-report', methods=['GET', 'POST'])
@login_required
@teacher_required
def daily_report():
    if request.method == 'POST':
        try:
            print("Form submitted:", request.form)  # Debug print
            print("Files:", request.files)  # Debug print
            
            # Get form data
            report_date = datetime.strptime(request.form.get('report_date'), '%Y-%m-%d')
            cleanliness = request.form.get('cleanliness')
            report_content = request.form.get('report_content')
            
            print(f"Parsed data: date={report_date}, cleanliness={cleanliness}, content={report_content}")  # Debug print

            # Handle file upload
            file_path = None
            if 'attachments' in request.files:
                file = request.files['attachments']
                if file and file.filename:
                    filename = secure_filename(file.filename)
                    file_path = os.path.join('uploads', filename)
                    full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                    print(f"Saving file to: {full_path}")  # Debug print
                    file.save(full_path)

            # Create new daily report
            new_report = DailyReport(
                teacher_id=current_user.id,
                date=report_date,
                content=report_content,
                file_path=file_path,
                status='pending'
            )

            print("Created new report object")  # Debug print

            # Add and commit to database
            db.session.add(new_report)
            db.session.commit()
            print("Successfully committed to database")  # Debug print

            flash('Daily report submitted successfully!', 'success')
            return redirect(url_for('teacher.daily_report'))

        except Exception as e:
            db.session.rollback()
            print(f"Error occurred: {str(e)}")  # Debug print
            flash(f'Error submitting report: {str(e)}', 'danger')
            return redirect(url_for('teacher.daily_report'))

    # For GET request
    today_date = datetime.now().strftime('%Y-%m-%d')
    previous_reports = DailyReport.query.filter_by(
        teacher_id=current_user.id
    ).order_by(DailyReport.date.desc()).all()

    daily_tasks = [
        {'id': 1, 'description': 'Take attendance'},
        {'id': 2, 'description': 'Complete lesson plan'},
        {'id': 3, 'description': 'Grade assignments'},
    ]
    
    total_tasks = len(daily_tasks)

    return render_template('teacher/daily_report.html',
                         today_date=today_date,
                         previous_reports=previous_reports,
                         daily_tasks=daily_tasks,
                         total_tasks=total_tasks)

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
