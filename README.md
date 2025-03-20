# Leave-Tracker

## 📌 Overview
**Leave Tracker** is a web-based attendance management system designed to help institutions track student attendance, manage leave requests, and calculate fines for students with attendance below the required threshold. The system provides role-based access for administrators and students, ensuring a seamless experience for both.

## 🚀 Features
### 🔹 Role-Based Authentication
- Separate login for **Admins** and **Students**.

### 🔹 Admin Dashboard
- View and approve/reject **leave requests** submitted by students.
- Manage attendance records.
- Monitor fine calculations.

### 🔹 Student Dashboard
- Submit leave requests.
- View leave request history and their statuses.

### 🔹 Attendance & Fine Management
- Upload attendance data.
- Automatically calculate attendance percentage.
- Impose a fine of ₹100 for every 5% shortfall below 85%.
- Fine concession for approved leave days if attendance is below 85%.

## 🛠 Tech Stack
- **Frontend:** HTML, CSS, JavaScript
- **Backend:** Flask (Python)
- **Database:** SQLite

## 📂 Project Structure
```
Leave-Tracker/
│── templates/           # Flask templates for rendering pages
│── static/              # Static files (CSS, JS, Images)
│── README.md            # Project documentation
│── app.py               # backend logic, routes
│── fine_calculation.py  # utility code
│── database1.db         # SQLite database 
│── requirements.txt   # Dependencies
```

## 🚀 Installation & Setup
### 🔹 Prerequisites
Ensure you have the following installed:
- Python 3.x
- Flask
- SQLite

### 🔹 Steps to Run the Project
1. **Clone the Repository**
   ```bash
   git clone https://github.com/ankithverma04/Leave-Tracker.git
   cd Leave-Tracker
   ```
2. **Create a Virtual Environment** (Optional but recommended)
   ```bash
   python -m venv venv
   source venv/bin/activate  # For Linux/macOS
   venv\Scripts\activate     # For Windows
   ```
3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```
4. **Initialize the Database**
   ```bash
   flask db init
   flask db migrate -m "Initial migration."
   flask db upgrade
   ```
5. **Start the Flask Server**
   ```bash
   flask run
   ```
6. **Access the Application**
   Open your browser and go to: [http://127.0.0.1:5000/](http://127.0.0.1:5000/)

## 🤝 Contribution Guidelines
- Fork the repository.
- Create a new branch (`feature-branch` or `bugfix-branch`).
- Commit changes and push to GitHub.
- Open a pull request.


## 📧 Contact
For any queries or contributions, reach out to **Ankith Verma**:
- **GitHub:** [ankithverma04](https://github.com/ankithverma04)
- **Email:** [ankithverma.04@gmail.com]

---
**🚀 Happy Coding!** 🎯

