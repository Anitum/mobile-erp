# School Management System

A comprehensive web-based school management system built with Flask, designed to facilitate communication and management between teachers, students, and administrators.

## Features

### User Management
- Multi-role authentication system (Teachers, Students, Administrators)
- Secure login and registration
- Role-based access control

### Teacher Features
1. **Dashboard**
   - Overview of assigned classes
   - Quick access to key features

2. **Homework Management**
   - Create and assign homework
   - Upload attachments
   - Set due dates
   - Specify subjects from standardized list
   - Track submissions

3. **Attendance System**
   - Mark daily attendance
   - Record student attendance
   - Add remarks and notes
   - View attendance history

4. **Daily Reports**
   - Submit daily activity reports
   - Upload supporting documents
   - Track cleanliness and other metrics
   - View previous reports

5. **Messaging System**
   - Communicate with students
   - File sharing capabilities
   - Message history

## Prerequisites

- Python 3+
- pip (Python package manager)
- Virtual environment (recommended)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/viralka/school-erp
   cd school-erp
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   Create a `.env` file in the root directory with necessary configurations.

5. Initialize the database:
   ```bash
   flask db upgrade
   ```

## Running the Application

1. Start the development server:
   ```bash
   python run.py
   ```

2. Access the application at `http://localhost:5000`

## Technical Stack

### Backend
- **Framework**: Flask
- **Database**: SQLAlchemy ORM
- **Authentication**: Flask-Login

### Frontend
- **Template Engine**: Jinja2
- **CSS Framework**: Bootstrap
- **Icons**: Font Awesome


## Contributing

1. Fork the repository
2. Create a new branch for your feature
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## About Anitum

Anitum is a startup revolutionizing educational technology with innovative solutions like:

### Walk-In Attendance System

- Seamless walk-in face detection - no manual scanning required
- Ultra-fast attendance marking (1/3 second processing)
- Multi-face scanning capability
- Easy integration with existing systems
- Real-time attendance tracking

For more information about Anitum's products and services, please contact us or visit our website.

## License

This software is proprietary and confidential. Copyright © 2023 Anitum. All rights reserved.

This software and its documentation are protected by copyright law and international treaties. Unauthorized reproduction