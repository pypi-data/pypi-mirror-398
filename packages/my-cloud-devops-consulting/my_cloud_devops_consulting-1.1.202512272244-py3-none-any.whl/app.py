from flask import Flask, render_template, request, redirect, url_for, session, flash,jsonify
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from urllib.parse import quote_plus
from bson.objectid import ObjectId
import os
from flask_login import LoginManager,login_user,UserMixin,login_required,logout_user,current_user
from settings import SECRET_KEY,MONGO_URI, EMAIL_USER, MONGO_PASSWORD, MONGO_USERNAME, COGNITO_CLIENT_ID, COGNITO_CLIENT_SECRET
from utils import send_email, get_videos
from werkzeug.middleware.proxy_fix import ProxyFix



app = Flask(__name__)
app.secret_key = SECRET_KEY  # Secure your secret key with an environment variable 
### app.secret_key = SECRET_KEY isn’t an import at all—it’s just an assignment
login_manager = LoginManager()

login_manager.init_app(app)

decoded_mongo_url = f"mongodb+srv://{quote_plus(MONGO_USERNAME)}:{quote_plus(MONGO_PASSWORD)}@cluster.7plpy.mongodb.net/my-database?retryWrites=true&w=majority"
client = MongoClient(decoded_mongo_url)


db = client['my-database']  # Specify your database as shown in the MongoDB Atlas interface
users_collection = db['inventory_collection']  # Collection for storing user data



class User(UserMixin):
    def __init__(self, user_id, username):
        self.id = str(user_id)
        self.username = username

    @staticmethod
    def get(user_id):
        user = users_collection.find_one({"_id": ObjectId(user_id)})
        if user:
            return User(user["_id"], user["username"])
        return None
@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

@app.route('/')
def home():
    video_url = None
    if 'username' in session:
        video_url = None  # Removed S3 video URL
    return render_template('index.html', video_url=video_url)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = users_collection.find_one({'username': username})
        print(user)
        if user and check_password_hash(user['password'], password):
            user_obj =User(user["_id"], user["username"])
            login_user(user_obj)
            # return redirect(url_for('home'))
            return jsonify({"message":"Login successful", "status": 200})
        else:
            # return redirect(url_for('login'))
            return jsonify({"message":"Invalid username or password", "status": 400})
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Check if the user already exists
        existing_user = users_collection.find_one({'username': username})
        if existing_user:
            flash('Username already exists. Please choose a different username.', 'error')
            return redirect(url_for('register'))
        
        # Hash the password for security
        hashed_password = generate_password_hash(password)
        user_data = {'username': username, 'password': hashed_password}
        users_collection.insert_one(user_data)
        flash('Successfully registered! Please log in.🥰', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/services')
def services():
    return render_template('services.html')

@app.route('/contact-form', methods=['GET', 'POST'])
def contact_form():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        category = request.form['category']
        appointment = request.form.get('appointment')
        message = request.form['message']
        
        # Store the contact data in the database
        contact_data = {
            'name': name,
            'email': email,
            'phone': phone,
            'category': category,
            'appointment': appointment,
            'message': message
        }
        print("Contact Data: ", contact_data)
        db.contacts.insert_one(contact_data)
        
        send_email('New Contact Form Submission', EMAIL_USER, f'Name: {name}\nEmail: {email}\nPhone: {phone}\nCategory: {category}\nAppointment: {appointment}\nMessage: {message}')
        send_email('Thanks for contacting', email, "We will get back to you as soon as possible!\nBest Regards,\nBetrand")
        
        

        # Remove the email or SMS notification logic here
        # Simply flash a success message
        flash('Your message has been submitted successfully!', 'success')

        return redirect(url_for('contact_form'))
    return render_template('contact-form.html')

# Update the /videos route to support both login types if does not work use this old one 
@app.route('/videos')
# @login_required
def private_videos():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    videos = get_videos()
    return render_template('private-videos.html', videos=videos)



@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully!", "info")
    return redirect(url_for("login"))

# My added route
@app.route('/about', methods=['GET', 'POST'])
def about():
    message = None
    if request.method == 'POST':
        mood = request.form['mood']
        if mood == "Excited":
            message = " Happy you are Excited We don’t just build infrastructure — we empower innovation. 💡💕"
        elif mood == "Curious":
            message = "Hmmmm curiousity is sometime good Explore what makes our infrastructure so powerful! 🔍"
        else:
            message = "We’re building something meaningful every day. 🌱"

    return render_template('about.html', message=message)


@app.route('/assessment', methods=['GET', 'POST'])
def assessment():
    result = None
    if request.method == 'POST':
        name = request.form['client_name']
        score = int(request.form['score'])
        if score >= 70:
            result = f"{name} is Cloud Ready ✅"
        else:
            result = f"{name} needs more preparation ❌"
    return render_template('assessment.html', result=result)

# 👇 Add this before the final block
@app.route('/subscribe', methods=['POST'])
def subscribe():
    email = request.form.get('email')
    if email:
        db.subscribers.insert_one({'email': email})
        print(f"New subscriber: {email}")
        flash('Thank you for subscribing!')
    else:
        flash('Please enter a valid email address.')
    return redirect(url_for('home'))
# 👇 Add this before the final block


from flask import Response

@app.route('/google77f25e63bec6dd80.html')
def google_verification():
    with open('google77f25e63bec6dd80.html') as f:
        return Response(f.read(), mimetype='text/html')

@app.route('/sitemap.xml')
def sitemap():
    return app.send_static_file('sitemap.xml')

@app.route('/robots.txt')
def robots():
    return app.send_static_file('robots.txt')




# adding logic for passwords reset

from itsdangerous import URLSafeTimedSerializer

serializer = URLSafeTimedSerializer(SECRET_KEY)

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        user = users_collection.find_one({'username': email})
        if user:
            token = serializer.dumps(str(user['_id']), salt='password-reset')
            reset_url = url_for('reset_password', token=token, _external=True)
            send_email("Password Reset Request", email, f"Click here to reset your password: {reset_url}")
            flash("Password reset link sent to your email.", "info")
        else:
            flash("User not found.", "error")
    return render_template('forgot-password.html')


# adding logic for passwords reset

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        user_id = serializer.loads(token, salt='password-reset', max_age=3600)  # 1 hour
    except:
        flash("The reset link is invalid or has expired.", "danger")
        return redirect(url_for('login'))

    if request.method == 'POST':
        new_password = request.form['password']
        hashed = generate_password_hash(new_password)
        users_collection.update_one({'_id': ObjectId(user_id)}, {'$set': {'password': hashed}})
        flash("Password updated. Please log in.", "success")
        return redirect(url_for('login'))

    return render_template('reset-password.html')



# Cookies
@app.route('/cookie-policy')
def cookie_policy():
    return render_template('cookie-policy.html')



if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=50)




