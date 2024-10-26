import os, random
import threading
from functions import toObject, saveShares, create
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_wtf import FlaskForm
from wtforms import IntegerField, SubmitField, BooleanField, StringField, PasswordField, ValidationError
from wtforms.validators import DataRequired, Email, EqualTo
from flask_sqlalchemy import SQLAlchemy as SQL
from flask_migrate import Migrate
import email_validator
from flask_login import LoginManager, UserMixin, login_user, current_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash

# If you plan to fork this code do make sure to create environment vars / secrets  in repl.

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ['secret_key']

basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(basedir, "data.sqlite")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQL(app)
Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
  return User.query.get(user_id)

class User(db.Model, UserMixin):
  __tablename__ = "User"

  id = db.Column(db.Integer, primary_key = True)
  email = db.Column(db.String, unique = True)
  username = db.Column(db.String, unique = True)
  password_hash = db.Column(db.String)
  money = db.Column(db.Float)
  public = db.Column(db.Boolean)

  shares = db.relationship("Portfolio", backref = "User", lazy = True)

  def __init__(this, email, username, password_hash, money):
    this.email = email
    this.username = username
    this.password_hash = password_hash
    this.money = money
    this.public = True

  def __repr__(this):
    return f"Name : {this.username}"

  def checkPassword(this, password):
    return check_password_hash(this.password_hash, password)

  def Buy(this, share):
    pass
  
  def Sell(this, share):
    pass

class Portfolio(db.Model):
  __tablename__ = "Portfolio"

  owner = db.relation("User")
  id = db.Column(db.Integer, primary_key = True)
  user_id = db.Column(db.Integer, db.ForeignKey("User.id"), nullable = False)
  name = db.Column(db.String, unique = True)
  total = db.Column(db.Float)
  quantity = db.Column(db.Integer)

  def __init__(this, user_id, name, total, quantity):
    this.user_id = user_id
    this.name = name
    this.total = total
    this.quantity = quantity
  
  def __repr__(this):
    return f"{this.owner.username} has {str(this.quantity)} shares of {this.name}"



class RegisterForm(FlaskForm):
  email = StringField("Email : ", validators = [DataRequired(), Email()])
  username = StringField("Username : ", validators = [DataRequired()])
  password = PasswordField("Password : ", validators = [DataRequired(), EqualTo("confirm", message = "Passwords Must Match!!!")])
  confirm = PasswordField("Confirm Password : ", validators = [DataRequired()])
  submit = SubmitField("Register")

  def checkEmail(this, field):
    if User.query.filter_by(email = field.data).first():
      raise ValidationError("Your Email Has Been Registered Already")

  def checkUsername(this, field):
    if User.query.filter_by(username = field.data).first():
      raise ValidationError("Your Username Has Been Registered Already")

class LoginForm(FlaskForm):
  email = StringField("Email : ", validators = [DataRequired(), Email()])
  password = PasswordField("Password : ", validators = [DataRequired()])
  submit = SubmitField("Login")

class BuyForm(FlaskForm):
  quantity = IntegerField("Quantity", validators = [DataRequired()])
  submit = SubmitField("Buy")

class SellForm(FlaskForm):
  quantity = IntegerField("Quantity", validators = [DataRequired()])
  submit = SubmitField("Sell")

class CheckedForm(FlaskForm):
  public = BooleanField("Do you want to appear on the Leaderboard", default = "checked")
  submit = SubmitField("Save")

class NotForm(FlaskForm):
  public = BooleanField("Do you want to appear on the Leaderboard")
  submit = SubmitField("Save")

def update(market):
  shares = toObject("shares.txt")
  market = market * random.randint(98, 102) / 100
  if market >= 0.70 or market <= 1.30:
    market = (random.randint(90, 110) / 100)
  for key in shares:
    share = shares[key]
    share["price"] = share["price"] * market
    share["price"] = share["price"] * share["rate"]
    share["rate"] = share["rate"] * random.randint(98, 102) / 100
    share["price"] = share["price"] * (1 + ((share["bought"] - share["sold"]) / 13000))
    share["bought"] = 0
    share["sold"] = 0
    if share["rate"] >= 1.5 or share["rate"] <= 0.5:
      share["rate"] = (random.randint(95, 105) / 100)
    if share["price"] <= 5 or share["price"] >= 25000:
      share["price"] = random.randint(250, 500)
    share["price"] = share["price"]
  saveShares("shares.txt", shares)  
  t = threading.Timer(30, update, [market])
  t.start()

@app.route("/")
def home():
  return render_template("home.html", os = os)

@app.route("/shares")
@login_required
def shareList():
  shares = toObject("shares.txt")
  return render_template("shares.html", shares = shares, os = os)

@app.route("/account/<name>", methods = ["GET", "POST"])
def account(name):
  user = User.query.filter_by(username = name).first()
  if current_user.is_authenticated:
    if not user.public:
      if current_user.username != name:
        if current_user.username != os.environ["admin_name"]:
          return redirect(url_for("home"))
  form = ""
  if user.public:
    form = CheckedForm()
  else:
    form = NotForm()
  if form.validate_on_submit():
    if form.public.data or form.public.data == "checked":
      user.public = True
    else:
      user.public = False
    db.session.commit()
    return redirect(url_for("account", name = name))
  return render_template("account.html", user = user, form = form, os = os)

@app.route("/admin")
@login_required
def admin():
  if current_user.username != os.environ["admin_name"]:
    # redirect to 500 error instead of home
    return redirect(url_for("home"))
  return render_template("admin.html", os = os)

@app.route("/share/buy/<name>", methods = ["GET", "POST"])
@login_required
def buy(name):
  shares = toObject("shares.txt")
  form = BuyForm()
  if form.validate_on_submit():
    # Add the Shares to the current users portfolio
    if form.quantity.data < 1:
      flash("Please type a number greater than or equal to 1")
    elif form.quantity.data * shares[name]["price"] > current_user.money:
      flash(f"You do not have enough money to buy {form.quantity.data} shares.")
    elif form.quantity.data > shares[name]["quantity"]:
      flash("These many shares are not available currently.")
    else:
      if Portfolio.query.filter_by(user_id = current_user.id, name = name).first():
        portfolio = Portfolio.query.filter_by(user_id = current_user.id, name = name).first()
        portfolio.quantity = portfolio.quantity + form.quantity.data
        portfolio.total = portfolio.total + (form.quantity.data * shares[name]["price"])
        db.session.commit()
      else:
        portfolio = Portfolio(current_user.id, name, form.quantity.data * shares[name]["price"], form.quantity.data)
        db.session.add(portfolio)
        db.session.commit()
      user = User.query.filter_by(id = current_user.id).first()
      user.money = user.money - (form.quantity.data * shares[name]["price"])
      db.session.commit()
      shares[name]["quantity"] = shares[name]["quantity"] - form.quantity.data
      shares[name]["bought"] = shares[name]["bought"] + form.quantity.data
      saveShares("shares.txt", shares)
      if shares[name]["quantity"] <= 100 or shares[name]["quantity"] >= 13000:
        shares[name]["quantity"] = random.randint(8000, 12000)
        saveShares("shares.txt", shares)
      return redirect(url_for("shareList"))
  return render_template("buy.html", name = name, shares = shares, form = form, os = os)

@app.route("/portfolio", methods = ["GET", "POST"])
@login_required
def portfolio():
  return render_template("portfolio.html", os = os)

@app.route("/share/sell/<name>", methods = ["GET", "POST"])
def sell(name):
  shares = toObject("shares.txt")
  share = Portfolio.query.filter_by(user_id = current_user.id, name = name).first()
  form = SellForm()
  if form.validate_on_submit():
    if form.quantity.data < 1:
      flash("Please Enter a number larger than 1")
    elif form.quantity.data > share.quantity:
      flash("You do not have these many shares.")
    else:
      shares[name]["quantity"] = shares[name]["quantity"] + form.quantity.data
      shares[name]["sold"] = shares[name]["sold"] + form.quantity.data
      saveShares("shares.txt", shares)
      user = User.query.filter_by(id = current_user.id).first()
      user.money = user.money + (form.quantity.data * shares[name]["price"])
      share.quantity = share.quantity - form.quantity.data
      share.total = share.total - (form.quantity.data * shares[name]["price"])
      if share.quantity <= 0:
        db.session.delete(share)
      db.session.commit()
      return redirect(url_for("portfolio"))
    return render_template("sell.html", name = name, shares = shares, share = share, form = form, os = os)
  return render_template("sell.html", name = name, shares = shares, share = share, form = form, os = os)

@app.route("/login", methods = ["GET", "POST"])
def login():
  form = LoginForm()
  if form.validate_on_submit():
    user = User.query.filter_by(email = form.email.data).first()
    if user is not None:
      if user.checkPassword(form.password.data):
        login_user(user)
        next = request.args.get("next")
        if next == None or not next[0]== "/":
          next = url_for("home")
        return redirect(next)
  return render_template("login.html", form = form, os = os)

@app.route("/register", methods = ["GET", "POST"])
def register():
  form  = RegisterForm()
  if form.validate_on_submit():
    form.checkEmail(form.email)
    form.checkUsername(form.username)
    user = User(email = form.email.data, username = form.username.data, password_hash = generate_password_hash(form.password.data), money = 50000)
    db.session.add(user)
    db.session.commit()
    return redirect(url_for("login"))
  return render_template("register.html", form = form, os = os)

@app.route("/logout")
@login_required
def logout():
  logout_user()
  return redirect(url_for("home"))

@app.route("/reset/user/<name>")
@login_required
def resetUser(name):
  if current_user.username != os.environ["admin_name"]:
    return redirect(url_for("home"))
  if name == os.environ["admin_name"]:
    return redirect(url_for("admin"))
  user = User.query.filter_by(username = name).first()
  db.session.delete(user)
  for portfolio in Portfolio.query.filter_by(user_id = user.id).all():
    db.session.delete(portfolio)
  db.session.commit()
  return redirect(url_for("admin"))

@app.route("/reset/user/all")
@login_required
def resetUserAll():
  if current_user.username != os.environ["admin_name"]:
    return redirect("home")
  for user in User.query.all():
    if user.username == os.environ["admin_name"]:
      continue
    db.session.delete(user)
  db.session.commit()
  for portfolio in Portfolio.query.all():
    if portfolio.user_id == User.query.filter_by(username = os.environ["admin_name"]).first().id:
      continue
    db.session.delete(portfolio)
  db.session.commit()
  return redirect(url_for("admin"))

@app.route("/leaderboard")
def leaderboard():
  users = ""
  if current_user.is_authenticated:
    if current_user.username == os.environ["admin_name"]:
      users = User.query.order_by(User.money.desc()).all()
    else:
      users = User.query.filter_by(public = True).order_by(User.money.desc()).all()
  else:
    users = User.query.filter_by(public = True).order_by(User.money.desc()).all()
  leng = len(users)
  return render_template("leaderboard.html", users = users, leng = leng, os = os)

@app.route("/reset/share")
@login_required
def resetShare():
  if current_user.username != os.environ["admin_name"]:
    return redirect("home")
  file = open("shares.txt", "w")
  file.close()
  create("shares.txt")
  return redirect(url_for("admin"))

@app.errorhandler(404)
def error404(e):
  return render_template("404.html", os = os)

@app.errorhandler(500)
def error500(e):
  return render_template("500.html", os = os)

if __name__ == "__main__":
  update((random.randint(90, 110) / 100))
  if User.query.filter_by(username = os.environ["admin_name"]).all() == []:
    adminuser = User(os.environ["admin_mail"], os.environ["admin_name"], generate_password_hash(os.environ["admin_pass"]), 50000)
    db.session.add(adminuser)
    adminuser.public = False
    db.session.commit()
  app.run(host = "0.0.0.0")