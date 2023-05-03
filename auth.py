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
    if 'user' in session:
        return render_template('home.html', session=session, flights=flights)
    return render_template('home.html', flights=flights)

#Search function
@auth.route('/search', methods=['GET', 'POST'])
def search():
    departure_search_area = request.form['departure search area']
    if departure_search_area not in ['name', 'city']:
        departure_search_area = 'name'
    departure = request.form['departure query']
    arrival_search_area = request.form['arrival search area']
    if arrival_search_area not in ['name', 'city']:
        arrival_search_area = 'name'
    arrival = request.form['arrival query']
    cursor = conn.cursor()

    # I wanna select from the flights that are filtered by departure matching and then take the arrival flights from that selection
    query = "SELECT * FROM flight JOIN airport departure_airport ON flight.departure_airport_code=departure_airport.name JOIN airport arrival_airport ON flight.arrival_airport_code=arrival_airport.name WHERE departure_airport.{departure_search} LIKE %s and arrival_airport.{arrival_search} LIKE %s".format(departure_search=departure_search_area, arrival_search=arrival_search_area)
    cursor.execute(query, (departure+"%", arrival+"%"))
    flights = cursor.fetchall()
    cursor.close()
    if 'user' in session:
        return render_template('home.html', name=session['user']['first_name'] + ' ' + session['user']['last_name'], flights=flights)
    return render_template('home.html', session=session, flights=flights)

#Load up customer login form page
@auth.route('/custlogin')
def custlogin():
    return render_template('custlogin.html')

#Go to customer dashboard, the home page for a customer
@auth.route('custhome',methods=['GET', 'POST'])
def custhome():
    return render_template('custdashboard.html', session=session)

#Customer login authentication
@auth.route('/custloginAuth', methods=['GET', 'POST'])
def custloginAuth():
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
        return render_template('custdashboard.html', name=session['user']['first_name'] + ' ' + session['user']['last_name'], flights=flights)
    else:
        error = 'Invalid login or username'
        return render_template('custlogin.html', error=error)

@auth.route('/custmyflight')
def custmyflight():
    return render_template('custmyflight.html')

#Load the customer registration form
@auth.route('/custregister')
def custsign_up():
    return render_template('custregister.html')

#Customer registration data insertion
@auth.route('/custregisterAuth', methods=['GET', 'POST'])
def custregisterAuth():

    password = request.form['password']
    confirm_password = request.form['confirm password']

    if(password != confirm_password):
        error = "Passwords don't match"
        return render_template('custregister.html', error=error)
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
        return render_template('custregister.html', error=error)
    else:
        ins = 'INSERT INTO customer VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'
        cursor.execute(ins, (email, last_name, first_name, date_of_birth, password, building_number, street, apartment_number, city, state, zip_code, passport_number, passport_expiration, phone_number))
        conn.commit()
        cursor.close()
        return render_template('custlogin.html')

@auth.route('/custmyflight', methods=['GET', 'POST'])
def myflight():
    cursor = conn.cursor()
    query = 'SELECT * FROM customer NATURAL JOIN purchased NATURAL JOIN ticket NATURAL JOIN flight WHERE customer.email = %s'
    cursor.execute(query, (session['user']['email']))
    flights = cursor.fetchall()
    return render_template('custmyflight.html', flights = flights)

@auth.route('/purchase/{{flight_number}}', methods=['GET', 'POST'])
def buyflights():
    flight_number = request.form['flight_number']
    cursor = conn.cursor()
    query = 'SELECT * FROM flight WHERE flight_number = %s'
    cursor.execute(query, (flight_number))
    flight = cursor.fetchone()

    return render_template('buyflights.html', flight=flight)

@auth.route('/custhistory', methods=['GET', 'POST'])
def custhistory():
    return render_template('/custhistory.html')
############################ STAFF ##############################
#Login template
@auth.route('/stafflogin', methods=['GET', 'POST'])
def stafflogin():
    return render_template('stafflogin.html')

#Login authorization
@auth.route('/staffloginAuth', methods=['GET', 'POST'])
def staffloginAuth():
    username = request.form['username']
    password = request.form['password']

    cursor = conn.cursor()
    query = 'SELECT username, first_name, last_name, airline_name, email, phone_number, date_of_birth FROM airline_staff WHERE username = %s and PASSWORD = %s'
    cursor.execute(query, (username, md5(password.encode()).hexdigest()))
    user = cursor.fetchone()

    if(user):
        session['user'] = {'username': user['username'], 'first_name': user['first_name'], 'last_name': user['last_name'],
                            'airline_name': user['airline_name'], 'email': user['email'], 'phone_number' : user['phone_number'],
                            'date_of_birth': user['date_of_birth']}
        return render_template('staffdashboard.html', name=session['user']['first_name'] + ' ' + session['user']['last_name'])
    else:
        error = 'Invalid login or username'
        return render_template('stafflogin.html', error=error)

#Register template
@auth.route('/staffregister', methods=['GET', 'POST'])
def staffsign_up():
    cursor = conn.cursor()
    query = 'SELECT name FROM airline'
    cursor.execute(query)
    airlines = cursor.fetchall()
    return render_template('staffregister.html', airlines=airlines)

#Register authorization
@auth.route('/staffregisterAuth', methods=['GET', 'POST'])
def staffregisterAuth():

    password = request.form['password']
    confirm_password = request.form['confirm password']

    if(password != confirm_password):
        error = "Passwords don't match"
        return render_template('staffregister.html', error=error)
    password = md5(password.encode()).hexdigest()

    email = request.form['email']
    first_name = request.form['first name']
    last_name = request.form['last name']
    date_of_birth = request.form['date of birth']
    phone_number = request.form['phone number']
    airline = request.form['airline employer']
    username = request.form['username']

    cursor = conn.cursor()
    query = 'SELECT * FROM airline_staff WHERE username = %s'
    cursor.execute(query, (username))
    data = cursor.fetchone()
    error = None
    if(data):
        error = "This user already exists"
        return render_template('staffregister.html', error=error)
    else:
        ins = 'INSERT INTO airline_staff VALUES(%s, %s, %s, %s, %s, %s, %s, %s)'
        cursor.execute(ins, (username, airline, password, last_name, first_name, email, phone_number, date_of_birth))
        conn.commit()
        cursor.close()
        return render_template('stafflogin.html')

#Homepage template
@auth.route('/staffhome',methods=['GET', 'POST'])
def staffhome():
    return render_template('staffdashboard.html', name=session['user']['first_name'] + ' ' + session['user']['last_name'])

@auth.route('/logout')
def logout():
    if 'user' in session:
        session.pop('user')
    return redirect('/')

#Flight template
@auth.route('staffflight', methods=['GET', 'POST'])
def staffflight():
    cursor = conn.cursor()
    query = 'SELECT * FROM Flight WHERE (departure_date > CURRENT_DATE OR (departure_date = CURRENT_DATE AND departure_time >= CURRENT_TIME) AND departure_date <= CURRENT_DATE + 30) AND airline_name = %s'
    cursor.execute(query, session['user']['airline_name'])
    flights = cursor.fetchall()

    cursor.close()
    return render_template('staffflight.html', flights = flights)

#Flight search
@auth.route('/staffsearch', methods=['GET', 'POST'])
def staffsearch():
    departure_search_area = request.form['departure search area']
    if departure_search_area not in ['name', 'city']:
        departure_search_area = 'name'
    departure = request.form['departure query']
    arrival_search_area = request.form['arrival search area']
    if arrival_search_area not in ['name', 'city']:
        arrival_search_area = 'name'
    arrival = request.form['arrival query']
    cursor = conn.cursor()

    # I wanna select from the flights that are filtered by departure matching and then take the arrival flights from that selection
    query = "SELECT * FROM flight JOIN airport departure_airport ON flight.departure_airport_code=departure_airport.name JOIN airport arrival_airport ON flight.arrival_airport_code=arrival_airport.name WHERE airline_name = %s AND departure_airport.{departure_search} LIKE %s and arrival_airport.{arrival_search} LIKE %s".format(departure_search=departure_search_area, arrival_search=arrival_search_area)
    cursor.execute(query, (session['user']['airline_name'],departure+"%", arrival+"%"))
    flights = cursor.fetchall()
    cursor.close()
    if 'user' in session:
        return render_template('staffflight.html', name=session['user']['first_name'] + ' ' + session['user']['last_name'], flights=flights)
    return render_template('staffflight.html', flights=flights)

#INFRASTRUCTURE
#template
@auth.route('/staffinfra', methods=['GET', 'POST'])
def staffinfra():
    return render_template('staffinfra.html')

@auth.route('/staffairportlist', methods=['GET', 'POST'])
def staffairportlist():
    cursor = conn.cursor()
    query = 'SELECT * FROM airport WHERE 1'
    cursor.execute(query)
    airports = cursor.fetchall()
    return render_template('staffairportlist.html', airports = airports, session=session['user'])

#Airport template
@auth.route('/staffairport', methods=['GET','POST'])
def staffairport():
    return render_template('staffairport.html')

#Airport authorization
@auth.route('/staffairportAuth', methods=['GET','POST'])
def staffairportAuth():
    code = request.form['code']
    name = request.form['name']
    city = request.form['city']
    country = request.form['country']
    type = request.form['type']

    cursor = conn.cursor()
    query = 'SELECT * FROM airport WHERE code = %s'
    cursor.execute(query, (code))
    data = cursor.fetchone()
    error = None
    if(data):
        error = "This airport already exists"
        return render_template('staffairport.html', error=error, session=session['user'])
    else:
        ins = 'INSERT INTO airport VALUES(%s, %s, %s, %s, %s)'
        cursor.execute(ins, (code,name, city, country, type))
        conn.commit()
        cursor.close()
        return redirect('/staffairportlist')

@auth.route('/staffairplanelist', methods=['GET', 'POST'])
def staffairplanelist():
    cursor = conn.cursor()
    query = 'SELECT * FROM airplane WHERE airline_name = %s'
    cursor.execute(query, session['user']['airline_name'])
    airplanes = cursor.fetchall()
    return render_template('staffairplanelist.html', airplanes = airplanes, session=session['user'])

@auth.route('/staffairplane', methods=['GET','POST'])
def staffairplane():
    return render_template('staffairplane.html')

@auth.route('/staffairplaneAuth', methods=['GET','POST'])
def staffairplaneAuth():
    identification_number = request.form['identification_number']
    seat_count = request.form['seat_count']
    manufacturer = request.form['manufacturer']
    manufacture_date = request.form['manufacture_date']

    cursor = conn.cursor()
    query = 'SELECT * FROM airplane WHERE airline_name = %s AND identification_number = %s'
    cursor.execute(query, (session['user']['airline_name'],identification_number))
    data = cursor.fetchone()
    error = None
    if(data):
        error = "This airplane already exists"
        return render_template('staffairplane.html', error=error, session=session['user'])
    else:
        ins = 'INSERT INTO airplane VALUES(%s, %s, %s, %s, %s)'
        cursor.execute(ins, (session['user']['airline_name'],identification_number, seat_count, manufacturer, manufacture_date))
        conn.commit()
        cursor.close()
        return redirect('/staffairplanelist')

@auth.route('/staff_add_flight', methods=['GET', 'POST'])
def staff_add_flight():
    cursor = conn.cursor()
    query = 'SELECT * FROM airport'
    cursor.execute(query)
    airports = cursor.fetchall()
    query = 'SELECT * FROM airplane'
    cursor.execute(query)
    airplanes = cursor.fetchall()
    return render_template('create flight.html', airports = airports, airplanes = airplanes, session=session['user'])

# Create a new flight
@auth.route('/flight_added', methods=['GET', 'POST'])
def staffflightAuth():
    departure_airport_code = request.form['departure_airport_code']
    arrival_airport_code = request.form['arrival_airport_code']
    if departure_airport_code == arrival_airport_code:
        error = "Departure and arrival airport cannot be the same"
        return render_template('create flight.html', error=error, session=session['user'])
    flight_num = request.form['flight_number']
    departure_date = request.form['departure_date']
    departure_time = request.form['departure_time']
    arrival_date = request.form['arrival_date']
    arrival_time = request.form['arrival_time']
    base_price = request.form['base_price']
    airplane_id = request.form['airplane_id']
    cursor = conn.cursor()
    query = 'SELECT * FROM flight WHERE flight_number = %s AND departure_date = %s AND departure_time = %s'
    cursor.execute(query, (flight_num, departure_date, departure_time))
    data = cursor.fetchone()
    if data:
        error = "This flight already exists"
        return render_template('create flight.html', error=error, session=session['user'])
    query = 'INSERT INTO flight VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'
    cursor.execute(query, (flight_num, departure_time, departure_date, departure_airport_code, arrival_date, arrival_time, arrival_airport_code, base_price, "On Time", session['user']['airline_name'], airplane_id.split("[*]")[0], airplane_id.split("[*]")[-1]))
    query = 'SELECT seat_count FROM airplane WHERE airline_name = %s AND identification_number = %s'
    cursor.execute(query, (airplane_id.split("[*]")[0], airplane_id.split("[*]")[-1]))
    seat_count = cursor.fetchone()
    for i in range(1, seat_count['seat_count']+1):
        query = 'INSERT INTO ticket VALUES(%s, %s, %s, %s, %s)'
        cursor.execute(query, (i, flight_num, departure_time, departure_date, base_price))
    conn.commit()
    cursor.close()
    return redirect('/staffflight')