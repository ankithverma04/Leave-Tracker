from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory, jsonify
import sqlite3
from fine_calculation import main, merge
from werkzeug.utils import secure_filename
from functools import wraps
import os
from datetime import datetime


app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'static/uploads/'
app.config['UPLOAD_FOLDER1'] = './csv/attendance'
app.config['PROCESSED_FOLDER'] = './csv/fines'
app.config['PROCESSED_FINES'] = './csv/fines/merged'
app.config['ALLOWED_EXTENSIONS'] = {'jpg', 'jpeg', 'png'}

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
PROCESSED_FOLDER = os.path.join(BASE_DIR, 'csv/fines')
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER1 = os.path.join(BASE_DIR, 'csv/attendance')
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
PROCESSED_FINES = os.path.join(BASE_DIR, 'csv/fines/merged')
DATABASE = 'database1.db'

os.makedirs(app.config['UPLOAD_FOLDER1'], exist_ok=True)
os.makedirs(app.config['PROCESSED_FOLDER'], exist_ok=True)

# Helper function to connect to the SQLite database
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# Initialize database tables if they don't exist
def init_db():
    with get_db() as conn:
        conn.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            usn TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
            );
        ''')

        conn.execute('''
        CREATE TABLE IF NOT EXISTS leaves (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            from_date TEXT NOT NULL,
            to_date TEXT NOT NULL,
            reason TEXT CHECK(reason IN ('Medical', 'Events', 'Others')) NOT NULL,
            file TEXT,
            status TEXT NOT NULL,
            description TEXT,
            FOREIGN KEY(student_id) REFERENCES students(id)
            );
        ''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER,
                date TEXT NOT NULL,
                status TEXT NOT NULL,
                FOREIGN KEY(student_id) REFERENCES students(id)
            )
        ''')

init_db()

def login_required(role=None):
    """Decorator to ensure the user is logged in and has the correct role."""
    def wrapper(f):
        @wraps(f)
        def wrapped_function(*args, **kwargs):
            if 'user_type' not in session:
                flash('You need to log in first!', 'warning')
                return redirect(url_for('login_view'))

            if role and session.get('user_type') != role:
                flash('You are not authorized to view this page!', 'danger')
                return redirect(url_for('login_view'))

            return f(*args, **kwargs)
        return wrapped_function
    return wrapper

@app.route('/')
def index():
    return render_template('smart-leave.html')

@app.route('/login', methods=['GET', 'POST'])
def login_view():
    if request.method == 'POST':
        role = request.form.get('role')
        print(role) 
        if role == 'student':
            usn = request.form.get('usn')
            password = request.form.get('studentpass')
            print(usn,password)
            with get_db() as conn:
                student = conn.execute(
                    'SELECT * FROM students WHERE usn = ?',
                    (usn,)
                ).fetchone()
                if student and student['password'] == password:
                    session['user_type'] = 'student'
                    session['user_id'] = student['id']
                    return redirect(url_for('dashboard', user_type='student'))
                else:
                    flash('Invalid student credentials!', 'danger')

        elif role == 'admin':
            username = request.form.get('username')
            password = request.form.get('password')
            print(username,password)
        
            if username == 'admin' and password == 'admin123':  
                session['user_type'] = 'admin'
                session['username'] = username
                return redirect(url_for('dashboard', user_type='admin'))
            else:
                flash('Invalid admin credentials!', 'error')
        else:
            flash('Invalid role selected!', 'error')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def student_signup():
    if request.method == 'POST':
        name = request.form.get('name')
        usn = request.form.get('usn')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # Validate passwords
        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return redirect(url_for('student_signup'))

        # Insert student into the database
        try:
            with get_db() as conn:
                existing_student = conn.execute(
                    'SELECT * FROM students WHERE usn = ?',
                    (usn,)
                ).fetchone()
                
                if existing_student:
                    flash('Account Already Exists With This USN. ', 'danger')
                    return redirect(url_for('student_signup'))

                conn.execute(
                    'INSERT INTO students (name, usn, password) VALUES (?, ?, ?)',
                    (name, usn, password)
                )
                conn.commit()
            
            flash('Sign-up successful! You can now log in.', 'success')
            return redirect(url_for('login_view'))
        except Exception as e:
            flash(f'An error occurred during sign-up: {str(e)}', 'danger')
            return redirect(url_for('student_signup'))

    return render_template('signup.html')

@app.route('/dashboard/<user_type>')
@login_required()      
def dashboard(user_type):
    if user_type not in ['admin', 'student']:
        return "Invalid user type", 404
    if user_type == 'admin' and session['user_type'] != 'admin':
        flash("Only Admins have access to this. Login as admin ", 'warning')
        return redirect(url_for('login_view'))
    return render_template('dashboard.html', user_type=user_type)

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully!', 'success')
    return redirect(url_for('login_view'))

@app.route('/dashboard/student/apply_leave', methods=['GET', 'POST'])
def apply_leave():
    # add session validation from login1.html
    if 'user_type' not in session or session['user_type'] != 'student':
        flash('Please log in as a student to apply for leave.', 'warning')
        return redirect(url_for('login_view'))

    if request.method == 'POST':
        student_id = session.get('user_id')
        from_date = request.form['from_date']
        to_date = request.form['to_date']
        reason = request.form['reason']
        file = request.files.get('file')
        description = request.form['description']
        filename = None

        # Convert the date strings to datetime objects for validation
        from_date_obj = datetime.strptime(from_date, '%Y-%m-%d').date()
        to_date_obj = datetime.strptime(to_date, '%Y-%m-%d').date()

        # Validate the dates
                
        if to_date_obj < from_date_obj:
            flash('To date cannot be before from date.', 'error')
            return redirect(url_for('apply_leave'))

        # Validate reason
        if reason not in ['Medical', 'Events', 'Others']:
            flash('Invalid reason selected.', 'error')
            return redirect(url_for('apply_leave'))

        # File handling logic
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(upload_path)

        # Insert leave application into database
        with get_db() as conn:
            conn.execute('''
                INSERT INTO leaves (student_id, from_date, to_date, reason, file, status, description)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (student_id, from_date, to_date, reason, filename, 'Pending', description))
            conn.commit()

        flash('Leave applied successfully!', 'success')
        return redirect(url_for('view_leaves'))
    return render_template('apply_leave.html')

@app.route('/dashboard/admin/manage_leaves', methods=['GET', 'POST'])
def manage_leaves():
    if 'user_type' not in session or session['user_type'] != 'admin':
        flash('Please log in as an admin to manage leaves.', 'warning')
        return redirect(url_for('login_view'))

    with get_db() as conn:
        # Fetch all leave applications
        leave_records = conn.execute('''
            SELECT leaves.id, students.name, students.usn, leaves.from_date, leaves.to_date, 
               leaves.reason, leaves.file, leaves.description, leaves.status
            FROM leaves 
            JOIN students ON leaves.student_id = students.id
            ORDER BY 
            CASE 
                WHEN leaves.status = 'Pending' THEN 1
                WHEN leaves.status = 'Approved' THEN 2
                WHEN leaves.status = 'Rejected' THEN 3
                ELSE 4
            END,
            leaves.from_date;
        ''').fetchall()

    return render_template('manage_leaves.html', leave_records=leave_records)

@app.route('/dashboard/admin/update_leave_status', methods=['POST'])
def update_leave_status():
    if 'user_type' not in session or session['user_type'] != 'admin':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('login_view'))

    leave_id = request.form['leave_id']
    action = request.form['action']  # 'approve' or 'reject'

    new_status = 'Approved' if action == 'approve' else 'Rejected'

    with get_db() as conn:
        conn.execute('''
            UPDATE leaves SET status = ? WHERE id = ?
        ''', (new_status, leave_id))
        conn.commit()

    flash(f'Leave {new_status} successfully!', 'success')
    return redirect(url_for('manage_leaves'))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/dashboard/student/view_leaves', methods=['GET'])
def view_leaves():
    if 'user_type' not in session or session['user_type'] != 'student':
        flash('Please log in as a student to view your leave records.', 'warning')
        return redirect(url_for('login_view'))

    student_id = session.get('user_id')
    with get_db() as conn:
        leave_records = conn.execute('''
            SELECT from_date, to_date, reason, file, description, status
            FROM leaves
            WHERE student_id = ?
            ORDER BY CASE 
                WHEN leaves.status = 'Pending' THEN 1
                WHEN leaves.status = 'Approved' THEN 2
                WHEN leaves.status = 'Rejected' THEN 3
                ELSE 4
            END , from_date DESC;
        ''', (student_id,)).fetchall()

    return render_template('view_leaves.html', leave_records=leave_records)

@app.route('/dashboard/change_password', methods=['GET', 'POST'])
def change_password():
    if 'user_type' not in session:
        flash('Please log in to change your password.', 'warning')
        return redirect(url_for('login_view'))

    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        if new_password != confirm_password:
            flash('New password and confirm password do not match!', 'danger')
            return redirect(url_for('change_password'))

        user_id = session['user_id']
        user_type = session['user_type']

        with get_db() as conn:
            if user_type == 'student':
                user = conn.execute('SELECT * FROM students WHERE id = ?', (user_id,)).fetchone()
                
            if user and user['password'] == current_password:
                conn.execute('UPDATE {} SET password = ? WHERE id = ?'.format(user_type + 's'),
                             (new_password, user_id))
                conn.commit()
                flash('Password updated successfully!', 'success')
                return redirect(url_for('dashboard', user_type=user_type))
            else:
                flash('Current password is incorrect!', 'danger')

    return render_template('change_password.html')


@app.route('/upload_attendance', methods=['GET', 'POST'])
def upload_attendance():
    if request.method == 'POST':
        # Collect uploaded files and subjects
        uploaded_files = []
        for key in request.files:
            if key.startswith("file"):  # Identify file inputs
                file = request.files[key]
                subject_key = key.replace("file", "subject")  # Corresponding subject input
                subject_name = request.form.get(subject_key, "Unknown").strip()

                if file and file.filename and subject_name:
                    # try:
                        # Save the uploaded file with the subject name
                        sanitized_subject = subject_name.replace(" ", "_")  # Sanitize subject name
                        filename = f"{sanitized_subject}.csv"
                        upload_path = os.path.join(UPLOAD_FOLDER1, filename)
                        file.save(upload_path)

                        # Process the file
                        fines_df = main(upload_path)

                        # Save processed file
                        processed_filename = f"Fines-{sanitized_subject}.csv"
                        processed_path = os.path.join(PROCESSED_FOLDER, processed_filename)
                        fines_df.to_csv(processed_path, index=False)

                        # Append result to preview
                        uploaded_files.append({
                            "file": processed_path,
                            "subject": subject_name,
                        })
                    # except Exception as e:
                else:
                        flash("Error processing file for {subject_name}: ", "error")
                        return redirect(request.url)

        if uploaded_files:
            fines = merge(uploaded_files)
            filename = f"Fines-total"
            path = os.path.join(PROCESSED_FINES, f"{filename}")
            fines.to_csv(f"{path}.csv", index = False)
            preview = {
                    "columns": fines.columns.tolist(),
                    "data": fines.head(10).values.tolist(),  # Show only first 10 rows
                }
            
            return render_template(
                'attendance_cal.html',
                preview = preview,
                download_url=url_for('download_processed_file', filename=f"{filename}.csv")
            )
        else:
            flash('No valid files were uploaded.', 'error')
            return redirect(request.url)

    return render_template('attendance_cal.html')

@app.route('/download/<filename>')
def download_processed_file(filename):
    return send_from_directory(PROCESSED_FINES, filename, as_attachment=True)

@app.route('/delete_all_leaves', methods=['POST'])
def delete_all_leaves():
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Delete all rows from the table `leave`
        cursor.execute("DELETE FROM leaves")
        conn.commit()

        return jsonify({'message': 'All rows in the "leave" table have been deleted successfully.'}), 200

    except sqlite3.Error as e:
        return jsonify({'error': f"An error occurred: {e}"}), 500

    finally:
        conn.close()

if __name__ == '__main__':
    app.run(debug=True)
