from flask import Flask, render_template, request, redirect, url_for, session, flash
import pandas as pd
import pickle
import sqlite3
from functools import wraps
import json

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Load model + encoders
model = pickle.load(open('model/accident_model.pkl', 'rb'))
encoders = pickle.load(open('model/encoders.pkl', 'rb'))
feature_order = pickle.load(open('model/feature_order.pkl', 'rb'))
target_encoder = pickle.load(open('model/target_encoder.pkl', 'rb'))

# Rule-based override
def determine_severity(row):
    if (row['speed_limit'] >= 80 
        and row['light_conditions'] != 'Daylight'
        and row['weather_conditions'] in ['Raining with high winds','Snowing with high winds']):
        return 'Fatal'
    elif ((50 <= row['speed_limit'] < 80 and row['weather_conditions'] in [
            'Raining no high winds','Raining with high winds','Snowing no high winds','Snowing with high winds'])
          or (row['speed_limit'] >= 70 and row['road_type'] in ['Single carriageway','Roundabout'])
          or (row['speed_limit'] >= 60 and row['road_surface_conditions'] in ['Snow','Frost / Ice'])):
        return 'Serious'
    else:
        return 'Slight'

# DB setup
def init_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT)''')
    conn.commit()
    conn.close()
init_db()

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'username' not in session:
            flash('Please register or login first!', 'warning')
            return redirect(url_for('register'))
        return f(*args, **kwargs)
    return decorated

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()

        # Check if user already exists
        cursor.execute('SELECT * FROM users WHERE username=?', (username,))
        existing_user = cursor.fetchone()
        if existing_user:
            conn.close()
            flash('⚠️ User already registered. Please log in.', 'warning')
            return redirect(url_for('login'))

        # Insert new user
        cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
        conn.commit()
        conn.close()

        # Auto-login new user
        session['username'] = username
        flash('✅ Registration successful! You are now logged in.', 'success')
        return redirect(url_for('predict'))

    return render_template('register.html')


@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username=? AND password=?', (username, password))
        user = cursor.fetchone()
        conn.close()
        if user:
            session['username'] = username
            flash('Login successful!', 'success')
            return redirect(url_for('predict'))
        else:
            flash('Invalid credentials!', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

import json

@app.route('/predict', methods=['GET', 'POST'])
@login_required
def predict():
    if request.method == 'POST':
        input_data = []
        raw_data = {}  # to store original values for rules

        for feature in feature_order:
            value = request.form.get(feature)
            if feature in ['number_of_vehicles', 'speed_limit']:
                raw_data[feature] = int(value)
            else:
                raw_data[feature] = value

            if feature in encoders:
                value = encoders[feature].transform([value])[0]
            else:
                value = int(value)
            input_data.append(value)

        input_df = pd.DataFrame([input_data], columns=feature_order)
        prediction = model.predict(input_df)[0]
        severity_ml = target_encoder.inverse_transform([prediction])[0]

        severity_rule = determine_severity(raw_data)
        severity_priority = ['Slight', 'Serious', 'Fatal']
        severity = severity_rule if severity_priority.index(severity_rule) > severity_priority.index(severity_ml) else severity_ml

        # --- Save to DB ---
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO history (username, inputs, prediction) VALUES (?, ?, ?)',
                       (session['username'], json.dumps(raw_data), severity))
        conn.commit()
        conn.close()

        return render_template('result.html', prediction=severity)
    
    dropdown_options = {col: encoders[col].classes_.tolist() for col in feature_order if col in encoders}
    return render_template('predict.html', dropdown_options=dropdown_options, features=feature_order)


@app.route('/history')
@login_required
def history():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT inputs, prediction FROM history WHERE username=? ORDER BY id DESC LIMIT 5', (session['username'],))
    rows = cursor.fetchall()
    conn.close()

    history_data = []
    for row in rows:
        history_data.append({
            'inputs': json.loads(row[0]),
            'prediction': row[1]
        })

    return render_template('history.html', history=history_data)

@app.route('/clear_history')
@login_required
def clear_history():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM history WHERE username=?', (session['username'],))
    conn.commit()
    conn.close()
    flash('Prediction history cleared.', 'info')
    return redirect(url_for('history'))

if __name__ == '__main__':
    app.run(debug=True)
