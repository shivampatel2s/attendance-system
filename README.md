# Student Attendance Management System

A beginner-friendly desktop application for registering students, recording daily
attendance and reviewing attendance reports. The project is written in Python and
uses Tkinter for its interface and SQLite for persistent local storage.

## Objectives

- Keep student records and attendance in one simple desktop application.
- Make it easy to take attendance for a selected date.
- Calculate individual and overall attendance percentages.
- Provide readable CSV exports for college records.
- Demonstrate Python functions, GUI programming, SQL, validation and testing.

## Features

- Separate administrator and student sign-in with salted PBKDF2 password hashes.
- Student portal shows only the signed-in student's attendance summary/history.
- Dashboard cards for student count, today's attendance and overall attendance.
- Add, search, update and delete students.
- Set or reset each student's sign-in password in the student form.
- Mark selected students Present/Absent, mark the whole class at once, and correct
  daily attendance; one record per student and date.
- Overall, daily, monthly and individual student reports.
- List students with attendance below 75%.
- Export student and attendance reports as Excel-friendly CSV files.
- SQLite data is stored locally and remains available after closing the app.

## Technologies and requirements

- Python 3.9 or newer (Python 3.10+ recommended).
- Tkinter, `sqlite3`, `datetime`, CSV and other Python standard-library modules.
- No third-party packages, paid services or internet connection are required.
- On some Linux systems, Tkinter may need to be installed using the operating
  system package manager.

## Project files

- `main.py` — starts the application and connects the pages.
- `database.py` — creates the database and contains database/report operations.
- `login.py`, `dashboard.py`, `students.py`, `attendance.py`, `reports.py` —
  separate interface screens.
- `student_dashboard.py` — read-only portal for the signed-in student.
- `export.py` — CSV export functions.
- `database/attendance.db` — created automatically the first time the app runs.
- `tests/test_database.py` — automated tests for the core workflows.

## Installation and running

1. Install Python 3 and ensure the Python executable is available in your PATH.
2. Open the `Student_Attendance_System` folder in Visual Studio Code.
3. In VS Code, open **Terminal → New Terminal**.
4. (Optional) Create and activate a virtual environment:

   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   ```

5. Run the application:

   ```powershell
   python main.py
   ```

   On macOS/Linux, use `source .venv/bin/activate` to activate the optional
   virtual environment. No `pip install` step is necessary.

## Demo login

- **Username:** `admin`
- **Password:** `admin123`

The application creates this demo administrator on the first run. Its password is
stored as a salted PBKDF2 hash, not as plain text. Change the demo password before
using this application for real records.

The administrator creates student accounts from **Students → Add student** and
sets their login password there. A student signs in by selecting **Student** and
entering their roll number and password. To reset a student's password, open
**Students → Edit selected** as an administrator and enter a new password. The
student login only shows that student's attendance; only an administrator can
change attendance.

## Database explanation

SQLite creates `database/attendance.db` automatically when the application starts.
It contains:

- `Admin`: unique username and password hash.
- `Students`: unique roll number, name, course, semester and phone number.
- `Students.password_hash`: nullable salted hash for the student's portal login.
  The application adds this column automatically to databases created by an older
  version; older student records need an administrator to set a password.
- `Attendance`: student, ISO date (`YYYY-MM-DD`) and Present/Absent status.

Foreign keys connect attendance to student records. Deleting a student also
removes their associated attendance. A unique constraint on student and date
prevents duplicate entries; saving an existing date intentionally updates those
entries after the user confirms a correction.

## Testing

Run the standard-library tests from the project folder:

```powershell
python -m unittest discover -s tests -v
```

The test suite checks login validation, password hashing, student add/edit/delete,
duplicate roll numbers, attendance correction and uniqueness, percentage/monthly
reports, and both CSV exports. Tests use a temporary database and do not modify
your application records.

## Screenshots

Screenshots can be added here after running the application, for example:

- `assets/login.png`
- `assets/dashboard.png`
- `assets/attendance.png`

## Future improvements

- Add a password-change screen and additional administrator accounts.
- Add semester/course filters and printable PDF reports.
- Add a dedicated attendance history search page and pagination for large classes.
- Add backup and restore options for the local SQLite database.
