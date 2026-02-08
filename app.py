from flask import Flask, render_template, request, url_for, redirect, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///todo.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


class List(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    tasks = db.relationship("Task", backref="todo_list", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "tasks": [t.to_dict() for t in self.tasks],
        }


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    checked = db.Column(db.Boolean, default=False)
    list_id = db.Column(db.Integer, db.ForeignKey("list.id"), nullable=False)

    def to_dict(self):
        return {"id": self.id, "content": self.content, "checked": self.checked}


with app.app_context():
    db.create_all()
    if not List.query.first():
        db.session.add(List(name="Personal"))
        db.session.commit()


def wants_json():
    return "application/json" in request.headers.get("Accept", "")


def smart_redirect(list_name, data=None, status_code=200):
    if wants_json():
        return jsonify(data if data else {"status": "success"}), status_code
    return redirect(url_for("view_list", list_name=list_name))


@app.route("/")
def index():
    return redirect(url_for("view_list", list_name="Personal"))


@app.route("/list/<list_name>", methods=["GET", "POST"])
def view_list(list_name):
    current_list = List.query.filter_by(name=list_name).first_or_404()

    if request.method == "POST":
        # Handle Form or JSON input
        data = request.get_json() if request.is_json else request.form
        content = data.get("todo")

        if content:
            new_task = Task(content=content, list_id=current_list.id)
            db.session.add(new_task)
            db.session.commit()
            return smart_redirect(list_name, new_task.to_dict(), 201)

    # GET logic
    if wants_json():
        return jsonify(current_list.to_dict())

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
    return smart_redirect(task.todo_list.name, task.to_dict())


@app.route("/delete/<int:task_id>", methods=["POST"])
def delete(task_id):
    task = Task.query.get_or_404(task_id)
    list_name = task.todo_list.name
    db.session.delete(task)
    db.session.commit()
    return smart_redirect(list_name, {"message": "deleted", "id": task_id})


@app.route("/add_list", methods=["POST"])
def add_list():
    data = request.get_json() if request.is_json else request.form
    name = data.get("list_name")

    if name and not List.query.filter_by(name=name).first():
        new_list = List(name=name)
        db.session.add(new_list)
        db.session.commit()
        return smart_redirect(name, new_list.to_dict(), 201)

    if wants_json():
        return jsonify({"error": "Invalid name or list exists"}), 400
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
