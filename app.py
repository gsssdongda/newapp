from flask import Flask, render_template, request, redirect, url_for, session
import requests
from datetime import timedelta
import os

app = Flask(__name__)

app.secret_key = os.getenv("FLASK_SECRET_KEY", "your_secret_key")  # Store in Render environment
app.permanent_session_lifetime = timedelta(hours=1)

# Airtable Credentials (Use Environment Variables for Security)
AIRTABLE_PAT = os.getenv("AIRTABLE_PAT")
BASE_ID = os.getenv("BASE_ID")
RESULT_TABLE = "RESULT"
TEST_TABLE = "TEST"

HEADERS = {
    "Authorization": f"Bearer {AIRTABLE_PAT}",
    "Content-Type": "application/json"
}

@app.route("/", methods=["GET", "POST"])
def login():
    session.permanent = True

    if request.method == "POST":
        name = request.form["name"]
        roll_no = request.form["roll_no"]
        student_class = request.form["class"]
        password = request.form["password"]

        if password != "gsssdongda":
            return "Invalid Password. Please try again."

        session["name"] = name
        session["roll_no"] = roll_no
        session["class"] = student_class

        return redirect(url_for("select_test"))

    return render_template("login.html")

@app.route("/select_test")
def select_test():
    if "class" not in session:
        return redirect(url_for("login"))

    student_class = session["class"]

    # Fetch available tests from Airtable
    response = requests.get(f"https://api.airtable.com/v0/{BASE_ID}/{TEST_TABLE}", headers=HEADERS).json()
    test_list = [record["fields"][student_class] for record in response.get("records", []) if student_class in record.get("fields", {})]

    return render_template("select_test.html", tests=test_list)

@app.route("/start_test/<test_name>")
def start_test(test_name):
    if "name" not in session:
        return redirect(url_for("login"))

    session["test_name"] = test_name

    # Fetch questions from Airtable
    response = requests.get(f"https://api.airtable.com/v0/{BASE_ID}/{test_name}", headers=HEADERS).json()
    
    questions = [{
        "question": record["fields"].get("Question", ""),
        "options": [record["fields"].get(f"Option{i}", "") for i in range(1, 5)],
        "correct": record["fields"].get("Correct Answer", "")
    } for record in response.get("records", [])]

    session["questions"] = questions
    return render_template("test_page.html", questions=questions)

@app.route("/submit_test", methods=["POST"])
def submit_test():
    if "name" not in session:
        return redirect(url_for("login"))

    chosen_answers = eval(request.form.get("answers", "[]"))
    questions = session.get("questions", [])
    
    score = sum(1 for i in range(len(questions)) if chosen_answers[i] == questions[i]["correct"])
    total_questions = len(questions)
    percentage = (score / total_questions) * 100 if total_questions else 0

    # Store result in Airtable
    data = {
        "records": [{
            "fields": {
                "NAME": session["name"],
                "ROLL_NO": session["roll_no"],
                "CLASS": session["class"],
                "TEST_NAME": session["test_name"],
                "MARKS_OBTAINED": score,
                "TOTAL_MARKS": total_questions,
                "PERCENTAGE": percentage
            }
        }]
    }
    requests.post(f"https://api.airtable.com/v0/{BASE_ID}/RESULT", headers=HEADERS, json=data)

    return render_template("result.html", name=session["name"], score=score, total=total_questions, percentage=percentage, questions=questions, chosen_answers=chosen_answers)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))  # Use Render's assigned port
