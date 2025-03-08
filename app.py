from flask import Flask, render_template, request, redirect, url_for, session
import requests

app = Flask(__name__)

app.secret_key = "your_secret_key"  # Change this to a strong secret key

from datetime import timedelta
app.permanent_session_lifetime = timedelta(hours=1)


# Airtable Credentials
AIRTABLE_PAT = "pat7eAyh1LhYzoP9r.c3a3f9161996a8acfaf22355a405c53a88d801fd55fd9fe60140a54bfa28f221"
BASE_ID = "appElnsry6ToOcuPQ"
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
    print("Session Data:", session)  # Add this in select_test, start_test, and submit_test
    # Fetch values from session
    name = session.get("name")  # Ensure name is fetched
    roll_no = session.get("roll_no")
    student_class = session.get("class")

   # Store in Airtable
#    data = {"records": [{"fields": {"NAME": name, "ROLL_NO": roll_no, "CLASS": student_class}}]}
 #   requests.post(f"https://api.airtable.com/v0/{BASE_ID}/RESULT", headers=HEADERS, json=data)

    student_class = session.get("class")
    if not student_class:
        return redirect(url_for("login"))

    # Fetch available tests from Airtable
    response = requests.get(f"https://api.airtable.com/v0/{BASE_ID}/{TEST_TABLE}", headers=HEADERS).json()
    test_list = []
    for record in response.get("records", []):
        fields = record.get("fields", {})
        if student_class in fields:
            test_list.append(fields[student_class])

    return render_template("select_test.html", tests=test_list)

@app.route("/start_test/<test_name>")
def start_test(test_name):

     # Fetch values from session
    name = session.get("name")  # Ensure name is fetched
    roll_no = session.get("roll_no")
    student_class = session.get("class")
    est_name = session.get("test_name")


    session["test_name"] = test_name

    # Fetch questions from Airtable
    response = requests.get(f"https://api.airtable.com/v0/{BASE_ID}/{test_name}", headers=HEADERS).json()
    
    questions = []
    for record in response.get("records", []):
        fields = record.get("fields", {})
        questions.append({
            "question": fields.get("Question", ""),
            "options": [fields.get("Option1", ""), fields.get("Option2", ""), fields.get("Option3", ""), fields.get("Option4", "")],
            "correct": fields.get("Correct Answer", "")
        })

    session["questions"] = questions
    return render_template("test_page.html", questions=questions)

    print("Session Data:", session)  # Add this in select_test, start_test, and submit_test



@app.route("/submit_test", methods=["POST"])
def submit_test():
    # Fetch values from session
    name = session.get("name")  # Ensure name is fetched
    roll_no = session.get("roll_no")
    student_class = session.get("class")
    test_name = session.get("test_name")



    chosen_answers = request.form.get("answers")
    chosen_answers = eval(chosen_answers) if chosen_answers else []

    questions = session.get("questions", [])
    score = sum(1 for i in range(len(questions)) if chosen_answers[i] == questions[i]["correct"])
    total_questions = len(questions)
    percentage = (score / total_questions) * 100 if total_questions else 0

    print("Session Data:", session)  # Add this in select_test, start_test, and submit_test


    # Store Result in Airtable
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
    print("Data being sent to Airtable:", data)


    requests.post(f"https://api.airtable.com/v0/{BASE_ID}/RESULT", headers=HEADERS, json=data)

   # print("Airtable Response:", response.status_code, response.text)


    return render_template("result.html", name=session["name"], score=score, total=total_questions, percentage=percentage, questions=questions, chosen_answers=chosen_answers)


    print("Airtable Response:", response.json())


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)  # Fixed port 5000