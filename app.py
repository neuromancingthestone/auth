from flask import Flask, render_template, redirect, session, flash
from flask_debugtoolbar import DebugToolbarExtension
from models import connect_db, db, User, Feedback
from forms import UserForm, LoginForm, FeedbackForm
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql:///auth_exercise"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True
app.config["SECRET_KEY"] = "abc123"
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

app.app_context().push()
connect_db(app)

toolbar = DebugToolbarExtension(app)

#############################################
# Base Route
#############################################

@app.route('/')
def home_page():
    if "user_id" not in session:
        return redirect('/login')
    else:
        user = User.query.get(session['user_id'])        
        return redirect(f'/users/{user.username}')         
    return render_template('/login')

#############################################
# USER ROUTES
#############################################

@app.route('/register', methods=['GET','POST'])
def register_user():
    """Get info to register a user, redirect if invalid"""
    form = UserForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        email = form.email.data
        first_name = form.first_name.data
        last_name = form.last_name.data
        new_user = User.register(username, password, email, first_name, last_name)

        db.session.add(new_user)
        try:
            db.session.commit()
        except IntegrityError:
            form.username.errors.append('Username taken.')
            return render_template(f'/users/{username}', form=form)

        session['user_id'] = new_user.id

        flash('Welcome! Successfully created account!', "success")
        return redirect(f'/users/{username}')

    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login_user():
    """Attempt to log a user in, and redirect if invalid"""
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        user = User.authenticate(username, password)
        if user:
            flash(f"Welcome back, {user.username}!", "primary")
            session['user_id'] = user.id
            return redirect(f'/users/{user.username}')
        else:
            form.username.errors = ['Invalid username/password.']

    return render_template('login.html', form=form)

@app.route("/users/<username>")
def user_page(username):
    """Show the user info and feedback posts"""
    if "user_id" not in session:
        flash("Please login first!", "danger")
        return redirect('/')     

    user = User.query.get(session['user_id'])

    if username != user.username:
        flash("Cannot access another user's page!", "danger")
        return redirect(f'/users/{user.username}')

    feedback = Feedback.query.filter(Feedback.username == username)
    return render_template("user.html", user=user, feedback=feedback)    

@app.route('/users/<username>/delete')
def delete_user(username):
    """Delete user"""
    if "user_id" not in session:
        flash("Please login first!", "danger")
        return redirect('/') 

    user = User.query.get(session['user_id'])

    if username != user.username:
        flash("Cannot access another user's page!", "danger")
        return redirect(f'/users/{user.username}')    

    db.session.delete(user)
    db.session.commit()
    session.pop('user_id')
    flash(f"User {username} Deleted!")

    return redirect(f"/")

@app.route('/logout')
def logout_user():
    session.pop('user_id')
    flash("Goodbye!", "info")
    return redirect('/')

######################################
# FEEDBACK ROUTES
######################################

@app.route('/users/<username>/feedback/add', methods=['GET', 'POST'])
def add_feedback(username):
    """Get the username and add feedback"""
    if "user_id" not in session:
        flash("Please login first!", "danger")
        return redirect('/')
    
    form = FeedbackForm()
    user = User.query.get(session['user_id'])

    if username != user.username:
        flash("Cannot access another user's page!", "danger")
        return redirect(f'/users/{user.username}/feedback/add')    

    if form.validate_on_submit():
        title = form.title.data
        content = form.content.data

        new_feedback = Feedback(title=title, content=content, username=username)
        db.session.add(new_feedback)
        db.session.commit()
        flash('Feedback Added!', 'success')
        return redirect(f'/users/{username}')

    return render_template("/feedback.html", form=form )

@app.route('/feedback/<int:id>/update', methods=['GET', 'POST'])
def update_feedback(id):
    """Update the feedback for the specific id passed in"""
    if "user_id" not in session:
        flash("Please login first!", "danger")
        return redirect('/')
    
    feedback = Feedback.query.get(id)
    form = FeedbackForm(obj=feedback)
    user = User.query.get(session['user_id'])    

    if feedback.user.username != user.username:
        flash("Cannot access another user's page!", "danger")
        return redirect(f'/users/{user.username}')

    if form.validate_on_submit():
        feedback.title = form.title.data
        feedback.content = form.content.data

        db.session.commit()
        flash('Feedback Added!', 'success')
        return redirect(f'/users/{user.username}')
    else:
        return render_template("edit_feedback.html", form=form )

@app.route('/feedback/<int:id>/delete', methods=["POST"])
def delete_feedback(id):
    """Delete feedback"""    
    if 'user_id' not in session:
        flash("Please login first!", "danger")
        return redirect('/login')
    
    user = User.query.get(session['user_id'])  
    feedback = Feedback.query.get_or_404(id)  

    if feedback.user.username == user.username:
        db.session.delete(feedback)
        db.session.commit()
        flash("Feedback deleted!", "info")
        return redirect(f'/users/{user.username}')
    flash("You don't have permission to do that!", "danger")
    return redirect(f'/users/{user.username}') 

