from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, send_file
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from extensions import db
from models import User, Request
from diffusers import StableDiffusionPipeline
import torch
import os
from os import makedirs
from os.path import isdir, join

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'images'
app.secret_key = "your_secret_key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# Load the Stable Diffusion model
model_id = "stabilityai/stable-diffusion-2-1"
pipe = StableDiffusionPipeline.from_pretrained(model_id, torch_dtype=torch.float16)
pipe = pipe.to("cuda" if torch.cuda.is_available() else "cpu")
try:
    model_id = "stabilityai/stable-diffusion-2-1"
    if torch.cuda.is_available():
        pipe = StableDiffusionPipeline.from_pretrained(model_id, torch_dtype=torch.float16)
        pipe = pipe.to("cuda")
    else:
        pipe = StableDiffusionPipeline.from_pretrained(model_id, torch_dtype=torch.float32)
        pipe = pipe.to("cpu")
    print("Model loaded successfully!")
except Exception as e:
    print(f"Error loading model: {e}")
# Database setup
db.init_app(app)
with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # Check if the username already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash("Username already exists. Please choose a different username.")
            return redirect(url_for("register"))

        # Create a new user
        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()

        flash("Registration successful! Please log in.")
        return redirect(url_for("login"))

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            login_user(user)
            return redirect(url_for("index"))
        flash("Invalid username or password.")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))

@app.route("/generate", methods=["POST"])
@login_required
def generate():
    prompt = request.form["prompt"]
    if not prompt:
        flash("Please enter a prompt.")
        return redirect(url_for("index"))

    # Ensure the directory exists
    if not isdir("images"):
        makedirs("images")

    # Generate image
    image = pipe(prompt).images[0]
    image_path = join("images", f"{current_user.id}_{len(current_user.requests)}.png")
    image.save(image_path)

    # Save request to database
    request_entry = Request(user_id=current_user.id, prompt=prompt, image_path=image_path)
    db.session.add(request_entry)
    db.session.commit()

    return redirect(url_for("view_image", filename=os.path.basename(image_path)))

@app.route("/history")
# @login_It seems my response was cut off. Let me complete the code for the `/history` route and provide the remaining parts of the website.

# ---

# ### Step 2: Backend Code (`app.py`) - Continued
# ```python
@app.route("/history")
@login_required
def history():
    requests = Request.query.filter_by(user_id=current_user.id).all()
    return render_template("history.html", requests=requests)

@app.route('/static/generated/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route("/view_image/<filename>")
def view_image(filename):
    return send_from_directory("images", filename)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
    