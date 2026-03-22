import json
import os
import re
import bcrypt
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

USERS_FILE = "App-Data/users.json"
COURSES_FILE = "App-Data/courses.json"
STUDENT_COURSES_FILE = "App-Data/student_courses.json"


@app.route("/")
def index():
    return send_file("cpcc_login.html")


def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r") as f:
        return json.load(f)


def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)


def load_courses():
    if not os.path.exists(COURSES_FILE):
        return {}
    with open(COURSES_FILE, "r") as f:
        return json.load(f)


def save_courses(courses):
    with open(COURSES_FILE, "w") as f:
        json.dump(courses, f, indent=2)


def load_student_courses():
    if not os.path.exists(STUDENT_COURSES_FILE):
        return {}
    with open(STUDENT_COURSES_FILE, "r") as f:
        return json.load(f)


def save_student_courses(student_courses):
    with open(STUDENT_COURSES_FILE, "w") as f:
        json.dump(student_courses, f, indent=2)


def get_user_emails():
    """Extract all email IDs across all users from users.values()"""
    users = load_users()
    
    # Handle dict format - email is a field in users.values()
    if isinstance(users, dict):
        email_ids = [user.get("email") for user in users.values() if user.get("email")]
        return sorted(email_ids) if email_ids else []
    
    # Handle list format - email is a field in each user object
    elif isinstance(users, list):
        email_ids = [user.get("email") for user in users if user.get("email")]
        return sorted(email_ids) if email_ids else []
    
    return []


def  get_user_by_email(email):
    """Get user data by email"""
    users = load_users()
    if isinstance(users, dict):
        return users.get(email)
    elif isinstance(users, list):
        return next((user for user in users if user.get("email") == email), None)
    return None


def get_course_ids():
    """Extract all course IDs from courses data"""
    courses = load_courses()
    if isinstance(courses, dict):
        return list(courses.keys())
    elif isinstance(courses, list):
        return [course.get("id") for course in courses if course.get("id")]
    return []


def get_course_by_id(course_id):
    """Get course data by course ID"""
    courses = load_courses()
    if isinstance(courses, dict):
        return courses.get(course_id)
    elif isinstance(courses, list):
        return next((course for course in courses if course.get("id") == course_id), None)
    return None


@app.route("/api/health")
def health():
    return jsonify({"success": True, "message": "Server is running!"})

@app.route("/api/emails", methods=["GET"])
def get_all_emails():
    """Get list of all email IDs across users"""
    user_emails = get_user_emails()
    return jsonify({
        "success": True,
        "data": user_emails,
        "total": len(user_emails)
    })


@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json()

    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    confirm = data.get("confirm", "")

    if not name or len(name.strip()) < 2:
        return jsonify({"success": False, "message": "Name is too short"})

    if not email:
        return jsonify({"success": False, "message": "Email is required"})

    # make sure its a real email format
    pattern = r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
    if not re.match(pattern, email):
        return jsonify({"success": False, "message": "Invalid email"})

    # only let cpcc students register
    if not email.endswith("@cpcc.edu") and not email.endswith("@email.cpcc.edu"):
        return jsonify({"success": False, "message": "You need a cpcc email to register"})

    if len(password) < 6:
        return jsonify({"success": False, "message": "Password must be at least 6 characters"})

    if password != confirm:
        return jsonify({"success": False, "message": "Passwords dont match"})

    users = load_users()

    # Check if email already exists
    if any(user.get("email") == email for user in users.values()):
        return jsonify({"success": False, "message": "Email already registered", "hint": "login"})

    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    # Generate user key following USR-N pattern
    user_ids = [int(key.split("-")[1]) for key in users.keys() if key.startswith("USR-")]
    next_id = max(user_ids) + 1 if user_ids else 1
    user_key = f"USR-{next_id}"

    users[user_key] = {
        "name": name,
        "email": email,
        "password": hashed
    }
    save_users(users)

    return jsonify({"success": True, "message": f"Account created! Welcome, {name}.", "name": name, "email": email})


@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email:
        return jsonify({"success": False, "message": "Email is required"})

    if not email.endswith("@cpcc.edu") and not email.endswith("@email.cpcc.edu"):
        return jsonify({"success": False, "message": "Use your cpcc email"})

    if not password:
        return jsonify({"success": False, "message": "Password is required"})

    # Get user by email using helper function
    user = get_user_by_email(email)
    
    if not user:
        return jsonify({"success": False, "message": "No account found, register first", "hint": "register"})


    if not bcrypt.checkpw(password.encode(), user["password"].encode()):
        return jsonify({"success": False, "message": "Wrong password"})

    return jsonify({"success": True, "message": f"Welcome back, {user['name']}!", "name": user["name"], "email": user["email"]})


@app.route("/api/courses", methods=["GET"])
def get_courses():
    courses = load_courses()
    return jsonify({"success": True, "data": courses})


@app.route("/api/courses/<course_id>", methods=["GET"])
def get_course(course_id):
    course_id = course_id.upper()
    
    # Check if course exists by creating course ID list from courses
    course_ids = get_course_ids()
    if course_id not in course_ids:
        return jsonify({"success": False, "message": "Course not found"})
    
    course = get_course_by_id(course_id)
    return jsonify({"success": True, "data": course})


@app.route("/api/courses", methods=["POST"])
def add_course():
    data = request.get_json()
    
    code = data.get("code", "").strip().upper()
    name = data.get("name", "").strip()
    department = data.get("department", "").strip().upper()
    
    if not code:
        return jsonify({"success": False, "message": "Course code is required"})
    
    if not name or len(name) < 3:
        return jsonify({"success": False, "message": "Course name must be at least 3 characters"})
    
    if not department:
        return jsonify({"success": False, "message": "Department is required"})
    
    courses = load_courses()
    
    # Generate course ID (e.g., CS-1, CS-2, etc.)
    course_ids = [int(id.split("-")[1]) for id in courses.keys() if "-" in id]
    next_id = max(course_ids) + 1 if course_ids else 1
    course_key = f"{department[:3]}-{next_id}"
    
    courses[course_key] = {
        "code": code,
        "name": name,
        "department": department
    }
    save_courses(courses)
    
    return jsonify({"success": True, "message": f"Course '{name}' added successfully!", "course_id": course_key, "course": courses[course_key]})


@app.route("/api/register-course", methods=["POST"])
def register_course():
    data = request.get_json()
    
    email = data.get("email", "").strip().lower()
    course_id = data.get("course_id", "").strip().upper()
    
    if not email:
        return jsonify({"success": False, "message": "Email is required"})
    
    if not email.endswith("@cpcc.edu") and not email.endswith("@email.cpcc.edu"):
        return jsonify({"success": False, "message": "Use your cpcc email"})
    
    if not course_id:
        return jsonify({"success": False, "message": "Course ID is required"})
    
    # Check if student exists by creating email list from users
    user_emails = get_user_emails()
    if email not in user_emails:
        return jsonify({"success": False, "message": "Student not found, register first"})
    
    # Check if course exists by creating course ID list from courses
    course_ids = get_course_ids()
    if course_id not in course_ids:
        return jsonify({"success": False, "message": "Course not found"})
    
    course = get_course_by_id(course_id)
    student_courses = load_student_courses()
    
    # Initialize course if not exists
    if course_id not in student_courses:
        student_courses[course_id] = []
    
    # Check if already registered
    if email in student_courses[course_id]:
        return jsonify({"success": False, "message": f"Already registered for {course['name']}"})
    
    # Register student to course
    student_courses[course_id].append(email)
    save_student_courses(student_courses)
    
    return jsonify({
        "success": True, 
        "message": f"Successfully registered for {course['name']}!", 
        "course_id": course_id,
        "email": email
    })

@app.route("/api/courses/<course_id>/students", methods=["GET"])
def get_course_students(course_id):
    course_id = course_id.upper()
    
    # Check if course exists by creating course ID list from courses
    course_ids = get_course_ids()
    if course_id not in course_ids:
        return jsonify({"success": False, "message": "Course not found"})
    
    course = get_course_by_id(course_id)
    student_courses = load_student_courses()
    
    # Get all students enrolled in this course
    enrolled_students = student_courses.get(course_id, [])
    
    # Load full student data for all students in this course
    all_course_students = []
    for student_id in enrolled_students:
        student_data = get_user_by_email(student_id)
        if student_data:
            all_course_students.append({
                "email": student_data.get("email"),
                "name": student_data.get("name")
            })
    
    return jsonify({
        "success": True,
        "data": all_course_students,
        "course": course,
        "total": len(all_course_students)
    })



if __name__ == "__main__":
    print("Server running at http://127.0.0.1:5000")
    app.run(debug=True, port=5000)