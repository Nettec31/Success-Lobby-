import re
import bcrypt
import json
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from models import db, User, StudentCourse


app = Flask(__name__)
CORS(app)

#DB config
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///successlobby.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

#create successlobby.db
with app.app_context():
    db.create_all()

#html route
@app.route("/")
def index():
    return render_template("cpcc_login.html")

@app.route("/quiz")
def quiz():
    return render_template("quiz.html")

@app.route("/lobby")
def lobby():
    return render_template("lobby.html")

@app.route("/room")
def room():
    return render_template("room.html")

@app.route("/profile")
def profile():
    return render_template("profile.html")

#api routes
@app.route("/api/health")
def health():
    return jsonify({"success": True, "message": "Server is running!"})

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

    if User.query.filter_by(email=email).first():
        return jsonify({"success": False, "message": "Email already registered", "hint": "login"})

    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    #save to DB
    new_user = User(name=name, email=email, password=hashed)
    db.session.add(new_user)
    db.session.commit()

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

    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify({"success": False, "message": "No account found, register first", "hint": "register"})

    if not bcrypt.checkpw(password.encode(), user.password.encode()):
        return jsonify({"success": False, "message": "Wrong password"})

    return jsonify({"success": True, "message": f"Welcome back, {user.name}!", "name": user.name, "email": user.email})

# Get profile info
@app.route("/api/profile", methods=["GET"])
def get_profile():
    email = request.args.get("email")
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"success": False, "message": "User not found"})

    courses = StudentCourse.query.filter_by(email=email).all()
    course_list = [{"code": c.course_code, "name": c.course_name} for c in courses]

    return jsonify({
        "success": True,
        "name": user.name,
        "email": user.email,
        "major": user.major or "",
        "availability": user.availability or "",
        "campus": user.campus or "",
        "courses": course_list,
        "bio": user.bio or ""
    })


# Save profile info
@app.route("/api/profile", methods=["POST"])
def save_profile():
    data = request.get_json()
    email = data.get("email")
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"success": False, "message": "User not found"})

    user.major = data.get("major", "")
    user.availability = data.get("availability", "")
    user.campus = data.get("campus", "")
    user.bio = data.get("bio", "")
    db.session.commit()

    return jsonify({"success": True, "message": "Profile saved!"})


# Add a course
@app.route("/api/courses/add", methods=["POST"])
def add_student_course():
    data = request.get_json()
    email = data.get("email")
    course_code = data.get("course_code", "").strip().upper()
    course_name = data.get("course_name", "").strip()

    if not email or not course_code or not course_name:
        return jsonify({"success": False, "message": "All fields required"})

    already = StudentCourse.query.filter_by(email=email, course_code=course_code).first()
    if already:
        return jsonify({"success": False, "message": "Already added"})

    new_course = StudentCourse(email=email, course_code=course_code, course_name=course_name)
    db.session.add(new_course)
    db.session.commit()

    return jsonify({"success": True, "message": f"{course_code} added!"})


# Remove a course
@app.route("/api/courses/remove", methods=["POST"])
def remove_student_course():
    data = request.get_json()
    email = data.get("email")
    course_code = data.get("course_code", "").strip().upper()

    course = StudentCourse.query.filter_by(email=email, course_code=course_code).first()
    if not course:
        return jsonify({"success": False, "message": "Course not found"})

    db.session.delete(course)
    db.session.commit()

    return jsonify({"success": True, "message": f"{course_code} removed!"})

# Look up a course by code
@app.route("/api/courses/lookup", methods=["GET"])
def lookup_course():
    code = request.args.get("code", "").strip().upper()

    with open("courses.json", "r") as f:
        courses = json.load(f)

    if code not in courses:
        return jsonify({"success": False, "message": "Course not found"})

    return jsonify({"success": True, "code": code, "name": courses[code]})

@app.route("/api/lobby", methods=["GET"])
def get_lobby():
    email = request.args.get("email")
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"success": False, "message": "User not found"})

    # Get this student's enrolled courses
    my_courses = StudentCourse.query.filter_by(email=email).all()

    result = []
    for course in my_courses:
        # Find other students in the same course
        others = StudentCourse.query.filter_by(course_code=course.course_code).all()

        matches = []
        for other in others:
            if other.email == email:
                continue  # skip yourself

            other_user = User.query.filter_by(email=other.email).first()
            if not other_user:
                continue

            # Check how well they match
            match_score = 0
            if other_user.availability == user.availability:
                match_score += 1
            if other_user.campus == user.campus:
                match_score += 1

            matches.append({
                "name": other_user.name,
                "availability": other_user.availability or "—",
                "campus": other_user.campus or "—",
                "match_score": match_score
            })

        # Sort best match first
        matches.sort(key=lambda x: x["match_score"], reverse=True)

        result.append({
            "code": course.course_code,
            "name": course.course_name,
            "matches": matches
        })

    return jsonify({"success": True, "courses": result})

if __name__ == "__main__":
    print("Server running at http://127.0.0.1:5000")
    app.run(debug=True, port=5000)
