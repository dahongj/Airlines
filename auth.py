from flask import Blueprint, render_template, request, session, url_for, redirect
import pymysql.cursors

auth = Blueprint('auth',__name__)

#Configure MySQL
conn = pymysql.connect(host='localhost',
                        user='root',
                        password='',
                        db='airplane',
                        charset='utf8mb4',
                        cursorclass=pymysql.cursors.DictCursor)

@auth.route('/login')
def login():
    cursor = conn.cursor()
    cursor.close()
    return render_template('login.html')

@auth.route('/loginAuth', methods=['GET', 'POST'])
def loginAuth():
    email = request.form['email']
    password = request.form['password']
    cursor = conn.cursor()
    query = 'SELECT email, first_name, last_name FROM customer WHERE email = %s and password = %s'
    cursor.execute(query, (email, password))
    data = cursor.fetchone()
    query = 'SELECT * FROM flight'
    cursor.execute(query)
    flights = cursor.fetchall()
    cursor.close()
    if(data):
        session['user'] = {'email': data['email'], 'first_name': data['first_name'], 'last_name': data['last_name']}
        return render_template('home.html', name=session['user']['first_name'] + ' ' + session['user']['last_name'], flights=flights)
    else:
        error = 'Invalid login or username'
        return render_template('login.html', error=error)

@auth.route('/logout')
def logout():
    return "<p>Logout<p>"

@auth.route('/register')
def sign_up():
    return render_template('register.html')
