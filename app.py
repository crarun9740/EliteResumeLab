from flask import Flask, render_template, request, abort, render_template_string, make_response, session, redirect
from functools import wraps
from flask_mysqldb import MySQL
from MySQLdb import cursors
import os
from secket_key import secret_key, MISTRAL_API_KEY, MISTRAL_AI_MODEL
from mistralai import Mistral
import json
import bs4 as bs

app = Flask(__name__)
app.secret_key = secret_key


def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if session.get("user", None) is None:
            return redirect("/login")
        print(session.get("user"))
        return func(*args, **kwargs)

    return wrapper


app.config['MYSQL_HOST'] = '127.0.0.1'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'arun'
app.config['MYSQL_DB'] = 'EliteResumeLab'
app.config['MYSQL_PORT'] = 3306

mysql = MySQL(app)
PDF_DIR = 'resume_templates'
os.makedirs(PDF_DIR, exist_ok=True)

TEMPLATE_MAPPING = {
    1: "template1.html",
    2: "template2.html",
    3: "template3.html",
    4: "template4.html",
    5: "template5.html",
    6: "template6.html",
}

mistral = Mistral(api_key=MISTRAL_API_KEY)


def get_improvements(resume_data: dict) -> dict:
    print("Getting AI response with data", resume_data)
    prompt = ""
    with open("sysPrompt.txt", "r") as f:
        prompt = f.read()
    chat_res = mistral.chat.complete(
        model=MISTRAL_AI_MODEL,
        messages=[{
            "role": "system",
            "content": prompt
        }, {
            "role": "user",
            "content": json.dumps(resume_data)
        }
        ],

    )
    print(chat_res.choices[0].message.content)
    file = bs.BeautifulSoup(chat_res.choices[0].message.content, "lxml")
    summary = file.find('summary').text
    return summary


@app.route('/mysql')
def index():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users")
    results = cur.fetchall()
    return str(results)


@app.route('/signup', methods=["GET", "POST"])
def signup():
    if request.method == "GET":

        return render_template("signin.html")
    elif request.method == "POST":

        data = {
            "firstname": request.form.get("firstname", ""),
            "lastname": request.form.get("lastname", ""),
            "email": request.form.get("email", ""),
            "password": request.form.get("password", ""),
            "confirm_password": request.form.get("confirm_password", ""),
        }
        if data["password"] != data["confirm_password"]:
            return render_template("signin.html", message="Passwords do not match.")

        cur = mysql.connection.cursor()
        try:
            cur.execute("""
                INSERT INTO users (firstname, lastname, email, password)
                VALUES (%s, %s, %s, %s)
            """, (data.get("firstname"), data.get("lastname"), data.get("email"), data.get("password")))
            mysql.connection.commit()

            return redirect("/login")
        except Exception as e:
            print(e)
            return render_template("signin.html", message="An Error Occured")
        finally:
            cur.close()


@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    elif request.method == "POST":
        email = request.form.get("email", "")
        password = request.form.get("password", "")

        cur = mysql.connection.cursor()
        cur.execute(
            "SELECT * FROM users WHERE email=%s AND password=%s;", (email, password))
        user = cur.fetchall()

        print(user)

        if len(user) == 0:
            return render_template("login.html", message="Invalid Username/Password")

        session["user"] = user[0]
        session["email"] = email
        return render_template("firstpage.html")


@app.route("/logout")
@login_required
def logout():
    session.pop("user")
    return redirect("/")


@app.route('/', methods=["GET"])
@login_required
def firstpage():
    return render_template("firstpage.html")


@app.route('/secondpage', methods=["GET"])
@login_required
def secondpage():
    return render_template("secondpage.html")


@app.route('/thirdpage', methods=['GET'])
@login_required
def thirdpage():
    return render_template("thirdpage.html")


@app.route('/form/<int:id>', methods=["GET", "POST"])
@login_required
def template_handler(id):
    if request.method == "GET":
        email = session.get('email')
        data = None

        if email:
            try:
                cursor = mysql.connection.cursor(cursors.DictCursor)
                cursor.execute(
                    "SELECT * FROM resumes WHERE email = %s", (email,))
                data = cursor.fetchone()
                cursor.close()
                print(data)
            except Exception as e:
                print(f"Error retrieving user data: {e}")

        return render_template('form.html', id=id, data=data if data else {})

    elif request.method == "POST":
        data = {
            "firstname": request.form.get("name", ""),
            "lastname": request.form.get("lastname", ""),
            "city": request.form.get("city", ""),
            "country": request.form.get("country", ""),
            "pincode": request.form.get("pincode", ""),
            "phone": request.form.get("phone", ""),
            "collegename": request.form.get("collegename", ""),
            "degree": request.form.get("degree", ""),
            "department": request.form.get("department", ""),
            "graduation_date": request.form.get("graduation_date"),
            "experience": request.form.get("experience", ""),
            "skills": request.form.getlist("skills[]"),
            "project1_name": request.form.get("project_name", ""),
            "project1_desc": request.form.get("project_desc", ""),
            "summary": request.form.get("summary", ""),
            "linkedin": request.form.get("linkedin", ""),
            "github": request.form.get("github", ""),
            "certification": request.form.getlist("certification[]"),
            "email": request.form.get("email", ""),
            "activities": request.form.getlist("activities[]"),
            "achievements": request.form.get("achievements", ""),
            "languages": request.form.getlist("languages[]"),
            "current_role": request.form.get("current-role", "")
        }
        print(data)

        data['summary'] = get_improvements(data)

        cursor = mysql.connection.cursor()
        cursor.execute(
            "SELECT * FROM resumes WHERE email = %s", (data["email"],))
        existing_data = cursor.fetchone()

        if existing_data:
            update_query = """
                UPDATE resumes
                SET firstname = %s, lastname = %s, city = %s, country = %s, pincode = %s, phone = %s,
                    collegename = %s, degree = %s, department = %s, graduation_date = %s,
                    experience = %s, skills = %s, project1_name = %s, project1_desc = %s,
                    summary = %s, linkedin = %s, github = %s, certification = %s,
                    activities = %s, achievements = %s, languages = %s, current_role = %s
                WHERE email = %s
                """
            values = (
                data["firstname"], data["lastname"], data["city"], data["country"], data["pincode"], data["phone"],
                data["collegename"], data["degree"], data["department"], data["graduation_date"],
                data["experience"], ",".join(
                    data["skills"]), data["project1_name"], data["project1_desc"],
                data["summary"], data["linkedin"], data["github"], ",".join(
                    data["certification"]),
                ','.join(data["activities"]), data["achievements"], ", ".join(
                    data["languages"]), data["current_role"], data["email"]
            )
            cursor.execute(update_query, values)
        else:
            insert_query = """
                INSERT INTO resumes (
                    firstname, lastname, city, country, pincode, phone,
                    collegename, degree, department, graduation_date,
                    experience, skills, project1_name, project1_desc,
                    summary, linkedin, github, certification, email,
                    activities, achievements, languages, current_role
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
            values = (
                data["firstname"], data["lastname"], data["city"], data["country"], data["pincode"], data["phone"],
                data["collegename"], data["degree"], data["department"], data["graduation_date"],
                data["experience"], data["skills"], data["project1_name"], data["project1_desc"],
                data["summary"], data["linkedin"], data["github"], data["certification"], data["email"],
                data["activities"], data["achievements"], data["languages"], data["current_role"]
            )
            cursor.execute(insert_query, values)

        mysql.connection.commit()
        cursor.close()

        session['data'] = data

        template_name = TEMPLATE_MAPPING.get(id)
        if template_name:
            return render_template(template_name, data=data, id=id)
        else:
            abort(404)
            # except Exception as e:
            mysql.connection.rollback()
            print(f"Error occurred: {e}")
            abort(500)
    else:
        abort(405)


@app.route('/form/<int:id>/download_resume', methods=['GET', 'POST'])
@login_required
def download_resume(id):
    template_name = TEMPLATE_MAPPING.get(id)
    if template_name:
        data = session.get('data')
        rendered_template = render_template(template_name, data=data)

    response = make_response(rendered_template)

    response.headers['Content-Disposition'] = 'attachment;filename=template.html'
    response.headers['Content-Type'] = 'text/html'

    return response


if __name__ == "__main__":
    app.run(debug=True)
