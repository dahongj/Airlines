from flask import Blueprint, render_template, request, session, url_for, redirect
import pymysql.cursors
from hashlib import md5

auth = Blueprint('auth',__name__)

#Configure MySQL
conn = pymysql.connect(host='localhost',
                        user='root',
                        password='',
                        db='airticket',
                        charset='utf8mb4',
                        cursorclass=pymysql.cursors.DictCursor)

@auth.route('/')
def home():
    #cursor created from the conn above
    cursor = conn.cursor()
    query = 'SELECT * FROM Flight WHERE departure_date > CURRENT_DATE OR (departure_date = CURRENT_DATE AND departure_time >= CURRENT_TIME);'
    cursor.execute(query)
    flights = cursor.fetchall()
    cursor.close()
    return render_template('home.html', flights=flights)

@auth.route('/search', methods=['GET', 'POST'])
def search():
    departure_search_area = request.form['departure search area']
    departure = request.form['departure query']
    arrival_search_area = request.form['arrival search area']
    arrival = request.form['arrival query']
    cursor = conn.cursor()

    # I wanna select from the flights that are filtered by departure matching and then take the arrival flights from that selection
    # changing the end of the query based on if the user wants to search by city or airport code
    if departure_search_area == 'departure_city':
        departure_query_end = " in (SELECT name FROM airport where city = %s)"
    else:
        departure_query_end = " = %s"
    # storing a query as a string to put in the final query
    departure_query = 'SELECT * FROM Flight WHERE departure_airport_code'+ departure_query_end
    
    if arrival == '':
        cursor.execute(departure_query, departure+"%")
        flights = cursor.fetchall()
        cursor.close()
    else:
        if arrival_search_area == 'arrival_city':
            arrival_query_end = " in (SELECT name FROM airport where city =  %s)"
        else:
            arrival_query_end = " = %s"
        query = 'SELECT * FROM (%s) WHERE arrival_airport_code%s' % (departure_query, arrival_query_end)
        cursor.execute(query, (departure+"%", arrival+"%"))
        flights = cursor.fetchall()
        cursor.close()
    return render_template('home.html', flights=flights)

@auth.route('/login')
def login():
    return render_template('login.html')

@auth.route('/loginAuth', methods=['GET', 'POST'])
def loginAuth():
    email = request.form['email']
    password = request.form['password']

    
    cursor = conn.cursor()
    query = 'SELECT * FROM flight'
    cursor.execute(query)
    flights = cursor.fetchall()

    #legacy code since our test cases aren't encrypted
    query = 'SELECT email, first_name, last_name FROM customer WHERE email = %s and password = %s'
    cursor.execute(query, (email, password))
    user = cursor.fetchone()
    
    cursor.close()
    if(user):
        session['user'] = {'email': user['email'], 'first_name': user['first_name'], 'last_name': user['last_name']}
        return render_template('home.html', name=session['user']['first_name'] + ' ' + session['user']['last_name'], flights=flights)

    cursor = conn.cursor()
    query = 'SELECT email, first_name, last_name FROM customer WHERE email = %s and password = %s'
    cursor.execute(query, (email, md5(password.encode()).hexdigest()))
    user = cursor.fetchone()

    if(user):
        session['user'] = {'email': user['email'], 'first_name': user['first_name'], 'last_name': user['last_name']}
        return render_template('customer.html', name=session['user']['first_name'] + ' ' + session['user']['last_name'], flights=flights)
    else:
        error = 'Invalid login or username'
        return render_template('login.html', error=error)

@auth.route('/logout')
def logout():
    return "<p>Logout<p>"

@auth.route('/register')
def sign_up():
    return render_template('register.html')

@auth.route('/registerAuth', methods=['GET', 'POST'])
def registerAuth():
    
    password = request.form['password']
    confirm_password = request.form['confirm password']

    if(password != confirm_password):
        error = "Passwords don't match"
        return render_template('register.html', error=error)
    password = md5(password.encode()).hexdigest()

    email = request.form['email']
    first_name = request.form['first name']
    last_name = request.form['last name']
    date_of_birth = request.form['date of birth']
    address = request.form['address']
    building_number = address.split()[0]
    apartment_number = request.form['apartment number']
    if apartment_number == '':
        apartment_number = "NULL"
    street = ' '.join(address.split()[1:])
    city = request.form['city']
    state = request.form['state']
    zip_code = request.form['zip code']
    passport_number = request.form['passport number']
    passport_expiration = request.form['passport expiration date']
    phone_number = request.form['phone number']
    cursor = conn.cursor()
    query = 'SELECT * FROM customer WHERE email = %s'
    cursor.execute(query, (email))
    data = cursor.fetchone()
    error = None
    if(data):
        error = "This user already exists"
        return render_template('register.html', error=error)
    else:
        ins = 'INSERT INTO customer VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'
        cursor.execute(ins, (email, last_name, first_name, date_of_birth, password, building_number, street, apartment_number, city, state, zip_code, passport_number, passport_expiration, phone_number))
        conn.commit()
        cursor.close()
        return render_template('login.html')
    


@auth.route('custflight', methods=['GET', 'POST'])
def myflight():
    return render_template('custflight.html')

