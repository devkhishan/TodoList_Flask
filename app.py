from flask import Flask, render_template, request, url_for, redirect
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Database Configuration (SQLite)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///todo.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


# --- DATABASE MODELS ---
#
class List(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    # Relationship: 'tasks' allows us to call my_list.tasks to see all items
    tasks = db.relationship(
        "Task", backref="todo_list", cascade="all, delete-orphan", lazy=True
    )


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    checked = db.Column(db.Boolean, default=False)
    list_id = db.Column(db.Integer, db.ForeignKey("list.id"), nullable=False)


# Initialize Database with defaults
with app.app_context():
    db.create_all()
    if not List.query.first():
        db.session.add_all(
            [List(name="Default"), List(name="Education"), List(name="Shopping")]  # type: ignore
        )
        db.session.commit()

# --- ROUTES ---


@app.route("/")
def index():
    # Automatically go to the 'Default' list on home load
    return redirect(url_for("view_list", list_name="Default"))


@app.route("/list/<list_name>", methods=["GET", "POST"])
def view_list(list_name):
    # Retrieve the specific List object or return 404 if it doesn't exist
    current_list = List.query.filter_by(name=list_name).first_or_404()

    if request.method == "POST":
        content = request.form.get("todo")
        if content:
            new_task = Task(content=content, list_id=current_list.id)  # type: ignore
            db.session.add(new_task)
            db.session.commit()
        # Redirect back to the same list to prevent form resubmission (PRG Pattern)
        return redirect(url_for("view_list", list_name=list_name))

    # Get all lists for the navigation menu
    all_lists = List.query.all()
    return render_template(
        "index.html",
        all_lists=all_lists,
        current_list=current_list,
        tasks=current_list.tasks,
    )


@app.route("/checked/<int:task_id>", methods=["POST"])
def checked(task_id):
    task = Task.query.get_or_404(task_id)
    task.checked = not task.checked
    db.session.commit()
    return redirect(url_for("view_list", list_name=task.todo_list.name))


@app.route("/delete/<int:task_id>", methods=["POST"])
def delete(task_id):
    task = Task.query.get_or_404(task_id)
    list_name = task.todo_list.name
    db.session.delete(task)
    db.session.commit()
    return redirect(url_for("view_list", list_name=list_name))


@app.route("/add_list", methods=["POST"])
def add_list():
    name = request.form.get("list_name")
    if name and not List.query.filter_by(name=name).first():
        new_list = List(name=name)  # type: ignore
        db.session.add(new_list)
        db.session.commit()
        return redirect(url_for("view_list", list_name=name))
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
