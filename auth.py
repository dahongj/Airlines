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
    query = 'SELECT * FROM Flight WHERE departure_date >= CURRENT_DATE OR (departure_date = CURRENT_DATE AND departure_time >= CURRENT_TIME);'
    cursor.execute(query)
    flights = cursor.fetchall()
    cursor.close()
    if 'user' in session:
        return render_template('home.html', session=session['user'], flights=flights)
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
        return render_template('home.html', session=session['user'], flights=flights)
    return render_template('home.html', session=session['user'], flights=flights)

#Load up customer login form page
@auth.route('/custlogin')
def custlogin():
    return render_template('custlogin.html')

#Go to customer dashboard, the home page for a customer
@auth.route('custhome',methods=['GET', 'POST'])
def custhome():
    return render_template('custdashboard.html', session=session['user'])

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
    query = 'SELECT email, first_name, last_name, date_of_birth FROM customer WHERE email = %s and password = %s'
    cursor.execute(query, (email, password))
    user = cursor.fetchone()

    cursor.close()
    if(user):
        session['user'] = {'email': user['email'], 'first_name': user['first_name'], 'last_name': user['last_name'], 'date_of_birth' : user['date_of_birth']}
        return render_template('home.html', session=session['user'], flights=flights)

    cursor = conn.cursor()
    query = 'SELECT email, first_name, last_name, date_of_birth  FROM customer WHERE email = %s and password = %s'
    cursor.execute(query, (email, md5(password.encode()).hexdigest()))
    user = cursor.fetchone()

    if(user):
        session['user'] = {'email': user['email'], 'first_name': user['first_name'], 'last_name': user['last_name'], 'date_of_birth' : user['date_of_birth']}
        return render_template('home.html', session=session['user'], flights=flights)
    else:
        error = 'Invalid login or username'
        return render_template('custlogin.html', error=error)

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
def custmyflight():
    cursor = conn.cursor()
    query = 'SELECT * FROM customer NATURAL JOIN purchased NATURAL JOIN ticket NATURAL JOIN flight WHERE customer.email = %s AND ((departure_date = CURRENT_DATE + 1 AND departure_time >= CURRENT_TIME) OR departure_date >= CURRENT_DATE + 2)'
    cursor.execute(query, (session['user']['email']))
    flights = cursor.fetchall()
    if 'user' in session:
        return render_template('custmyflight.html', session=session['user'],flights = flights)

@auth.route('/cancelflight', methods=['GET', 'POST'])
def cancelflight():
    cursor = conn.cursor()
    ticket_id = request.form['ticket_id']

    query = 'DELETE from purchased where ticket_id = %s'
    cursor.execute(query, ticket_id)
    conn.commit()
    cursor.close()

    if 'user' in session:
        return redirect('\custmyflight')

@auth.route('/buyflights', methods=['GET', 'POST'])
def buyflights():
    cursor = conn.cursor()
    query = 'SELECT * FROM Flight WHERE departure_date > CURRENT_DATE OR (departure_date = CURRENT_DATE AND departure_time >= CURRENT_TIME);'
    cursor.execute(query)
    flights = cursor.fetchall()
    cursor.close()
    if 'user' in session:
        return render_template('buyflights.html', session=session['user'], flights=flights)

@auth.route('/purchaseflight', methods=['GET', 'POST'])
def purchaseflight():
    flight_number = request.form['flight_number']
    departure_date = request.form['departure_date']
    departure_time = request.form['departure_time']

    cursor = conn.cursor()
    query = 'SELECT * from ticket WHERE flight_number = %s  AND departure_date = %s AND departure_time = %s AND NOT EXISTS(SELECT ticket_id from purchased WHERE purchased.ticket_id = ticket.ticket_id)'
    cursor.execute(query,(flight_number,departure_date,departure_time))
    tickets = cursor.fetchall()
    cursor.close()
    return render_template('tickets.html',session=session['user'],flight_number=flight_number,departure_date=departure_date,departure_time=departure_time, tickets = tickets)

@auth.route('/purchaseticket', methods=['GET', 'POST'])
def purchaseticket():
    email = session['user']['email']
    last_name = session['user']['last_name']
    first_name = session['user']['first_name']
    dob = session['user']['last_name']
    flight_number = request.form['flight_number']
    departure_date = request.form['departure_date']
    departure_time = request.form['departure_time']
    card_type = request.form['card_type']
    card_number = request.form['card_number']
    expiration_date = request.form['exp_date']
    name_on_card = request.form['noc']
    amount = int(request.form['amount'])

    cursor = conn.cursor()
    query = 'SELECT * from ticket WHERE flight_number = %s  AND departure_date = %s AND departure_time = %s AND NOT EXISTS(SELECT ticket_id from purchased WHERE purchased.ticket_id = ticket.ticket_id)'
    cursor.execute(query,(flight_number,departure_date,departure_time))
    tickets = cursor.fetchall()

    for ticket in tickets:
        if amount > 0:
            query = 'INSERT INTO purchased(email,ticket_id,rider_last_name,rider_first_name,rider_dob,card_type,card_number,expiration_date,name_on_card,purchase_time,purchase_date) VALUES(%s, %s, %s, %s, %s, %s, %s,%s, %s, CURRENT_TIME, CURRENT_DATE)'
            ticket_id = ticket['ticket_id']
            cursor.execute(query,(email,ticket_id,last_name,first_name,dob,card_type,card_number,expiration_date,name_on_card))
            amount -= 1 
        else:
            break
    conn.commit()
    cursor.close()
    return redirect('/custmyflight')

@auth.route('/custhistory', methods=['GET', 'POST'])
def custhistory():
    if 'user' in session:
        cursor = conn.cursor()
        query = 'SELECT * from purchased NATURAL JOIN ticket WHERE email = %s AND departure_date < CURRENT_DATE OR (departure_date = CURRENT_DATE AND departure_time < CURRENT_TIME)'
        cursor.execute(query,(session['user']['email']))
        flights = cursor.fetchall()
        cursor.close()
        return render_template('/custhistory.html',session=session['user'],flights=flights)
    
@auth.route('/rate', methods=['GET', 'POST'])
def rate():
    flight_number = request.form['flight_number']
    departure_date = request.form['departure_date']
    departure_time = request.form['departure_time']

    cursor = conn.cursor()
    query = 'SELECT * from reviews WHERE email = %s AND flight_number = %s AND departure_date = %s AND departure_time = %s'
    cursor.execute(query, (session['user']['email'],flight_number,departure_date,departure_time))
    reviews = cursor.fetchall()

    for review in reviews:
        rating = review['rating']
        comment = review['comment']

    if len(reviews) != 0:
        return  render_template('/rate.html',session=session['user'], flight_number=flight_number,departure_date=departure_date,departure_time=departure_time,rating=rating,comment=comment)
    else:
        return  render_template('/rate.html',session=session['user'], flight_number=flight_number,departure_date=departure_date,departure_time=departure_time)
    
@auth.route('/create_rating', methods=['GET', 'POST'])
def create_rating():
    flight_number = request.form['flight_number']
    departure_date = request.form['departure_date']
    departure_time = request.form['departure_time']
    rating = request.form['rating']
    comment = request.form['comment']

    cursor = conn.cursor()
    query = 'SELECT * from reviews WHERE email = %s AND flight_number = %s AND departure_date = %s AND  departure_time = %s'
    cursor.execute(query, (session['user']['email'],flight_number,departure_date,departure_time))
    reviews = cursor.fetchall()

    if(len(reviews) != 0):
        query = 'DELETE from reviews WHERE email = %s AND flight_number = %s AND departure_date = %s AND  departure_time = %s'
        cursor.execute(query, (session['user']['email'],flight_number,departure_date,departure_time))
        conn.commit()

    query = 'INSERT INTO reviews(email,flight_number,departure_date,departure_time,rating,comment) VALUES(%s,%s,%s,%s,%s,%s)'
    cursor.execute(query, (session['user']['email'],flight_number,departure_date,departure_time,rating,comment))
    conn.commit()
    cursor.close()
    return  redirect('/custhistory')
    
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
        return render_template('staffdashboard.html', session = session['user'],name=session['user']['first_name'] + ' ' + session['user']['last_name'])
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
    return render_template('staffdashboard.html', session = session['user'])

@auth.route('/logout')
def logout():
    if 'user' in session:
        session.pop('user')
    return redirect('/')

#Flight template
@auth.route('/staffflight', methods=['GET', 'POST'])
def staffflight():
    cursor = conn.cursor()
    query = 'SELECT * FROM Flight WHERE (departure_date > CURRENT_DATE OR (departure_date = CURRENT_DATE AND departure_time >= CURRENT_TIME) AND departure_date <= CURRENT_DATE + 30) AND airline_name = %s'
    cursor.execute(query, session['user']['airline_name'])
    flights = cursor.fetchall()

    cursor.close()
    return render_template('staffflight.html', flights = flights, session=session['user'])

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
        return render_template('staffflight.html', session=session['user'], flights=flights)
    return render_template('staffflight.html', flights=flights)

#INFRASTRUCTURE
#template
@auth.route('/staffinfra', methods=['GET', 'POST'])
def staffinfra():
    return render_template('staffinfra.html',session=session['user'])

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
    return render_template('staffairport.html', session=session['user'])

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
    return render_template('staffairplane.html',session=session['user'])

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
    query = 'SELECT * FROM airplane WHERE airline_name = %s'
    cursor.execute(query, session['user']['airline_name'])
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
    query = 'SELECT * FROM flight WHERE airline_name = %s AND flight_number = %s AND departure_date = %s AND departure_time = %s'
    cursor.execute(query, (session['user']['airline_name'], flight_num, departure_date, departure_time))
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
        if((seat_count['seat_count']-i)/seat_count['seat_count'] > .2):
            query = 'INSERT INTO ticket(flight_number,departure_time,departure_date,price) VALUES(%s, %s, %s, %s)'
            cursor.execute(query, (flight_num, departure_time, departure_date, base_price))
        else:
            new_price = str(1.25*int(base_price))
            query = 'INSERT INTO ticket(flight_number,departure_time,departure_date,price) VALUES(%s, %s, %s, %s)'
            cursor.execute(query, (flight_num, departure_time, departure_date, new_price))
    conn.commit()
    cursor.close()
    return redirect('/staffflight')

@auth.route('/flight_changed', methods=['GET', 'POST'])
def staffflightchangeAuth():
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
    status = request.form['flight_status']
    airplane_id = request.form['airplane_id']
    cursor = conn.cursor()
    query = 'UPDATE flight SET departure_airport_code = %s, arrival_airport_code = %s, arrival_date = %s, arrival_time = %s, flight_status = %s WHERE airline_name = %s AND flight_number = %s AND departure_date = %s AND departure_time = %s'
    cursor.execute(query, (departure_airport_code, arrival_airport_code, arrival_date, arrival_time, status, session['user']['airline_name'], flight_num, departure_date, departure_time))
    return redirect('/staffflight')

@auth.route('/staffrevenue', methods=['GET', 'POST'])
def staffrevenue():

    monthly_rev = 0
    monthly_ticket = 0
    yearly_rev = 0
    yearly_ticket = 0
    range_rev = 0
    range_ticket = 0

    cursor = conn.cursor()
    query = 'SELECT sum(price) AS revenue, COUNT(*) AS sales FROM ticket JOIN purchased ON ticket.ticket_id=purchased.ticket_id JOIN flight ON ticket.flight_number=flight.flight_number WHERE airline_name = %s AND purchased.purchase_date >= DATE_SUB(NOW(), INTERVAL 1 YEAR)'
    cursor.execute(query, session['user']['airline_name'])
    yrevenue = cursor.fetchone()
    yearly_rev = yrevenue['revenue']
    yearly_ticket = yrevenue['sales']

    query = 'SELECT sum(price) AS revenue, COUNT(*) AS sales FROM ticket JOIN purchased ON ticket.ticket_id=purchased.ticket_id JOIN flight ON ticket.flight_number=flight.flight_number WHERE airline_name = %s AND purchased.purchase_date >= DATE_SUB(NOW(), INTERVAL 1 MONTH)'
    cursor.execute(query, session['user']['airline_name'])
    mrevenue = cursor.fetchone()
    monthly_rev = mrevenue['revenue']
    monthly_ticket = mrevenue['sales']

    query = 'SELECT Customer.email, COUNT(DISTINCT Flight.flight_number) AS num_flights FROM Customer JOIN Purchased ON Customer.email = Purchased.email JOIN Ticket ON Purchased.ticket_id = Ticket.ticket_id JOIN Flight ON Ticket.flight_number = Flight.flight_number AND Ticket.departure_date = Flight.departure_date AND Ticket.departure_time = Flight.departure_time GROUP BY Customer.email ORDER BY num_flights'
    cursor.execute(query)
    customers = cursor.fetchall()

    return render_template('/staffrevenue.html', yearly_rev = yearly_rev, yearly_ticket = yearly_ticket, monthly_rev = monthly_rev, monthly_ticket = monthly_ticket, range_rev = range_rev, range_ticket= range_ticket, session=session['user'], customers=customers)

@auth.route('/staffrange', methods=['GET', 'POST'])
def staffrange():

    start = request.form['start']
    end = request.form['end']
    monthly_rev = 0
    monthly_ticket = 0
    yearly_rev = 0
    yearly_ticket = 0
    range_rev = 0
    range_ticket = 0

    cursor = conn.cursor()
    'SELECT sum(price) AS revenue, COUNT(*) AS sales FROM ticket JOIN purchased ON ticket.ticket_id=purchased.ticket_id JOIN flight ON ticket.flight_number=flight.flight_number WHERE airline_name = %s AND purchased.purchase_date >= DATE_SUB(NOW(), INTERVAL 1 YEAR)'
    cursor.execute(query, session['user']['airline_name'])
    yrevenue = cursor.fetchone()
    yearly_rev = yrevenue['revenue']
    yearly_ticket = yrevenue['sales']

    query = 'SELECT sum(price) AS revenue, COUNT(*) AS sales FROM ticket JOIN purchased ON ticket.ticket_id=purchased.ticket_id JOIN flight ON ticket.flight_number=flight.flight_number WHERE airline_name = %s AND purchased.purchase_date >= DATE_SUB(NOW(), INTERVAL 1 MONTH)'
    cursor.execute(query, session['user']['airline_name'])
    mrevenue = cursor.fetchone()
    monthly_rev = mrevenue['revenue']
    monthly_ticket = mrevenue['sales']

    query = 'SELECT sum(price) AS revenue, COUNT(*) AS sales FROM ticket JOIN purchased ON ticket.ticket_id=purchased.ticket_id JOIN flight ON ticket.flight_number=flight.flight_number WHERE airline_name = %s AND purchase_date BETWEEN {start} AND {end}'
    cursor.execute(query, (session['user']['airline_name'],start,end))
    rrevenue = cursor.fetchone()
    range_rev = rrevenue['revenue']
    range_ticket = rrevenue['sales']

    query = 'SELECT Customer.email, COUNT(DISTINCT Flight.flight_number) AS num_flights FROM Customer JOIN Purchased ON Customer.email = Purchased.email JOIN Ticket ON Purchased.ticket_id = Ticket.ticket_id JOIN Flight ON Ticket.flight_number = Flight.flight_number AND Ticket.departure_date = Flight.departure_date AND Ticket.departure_time = Flight.departure_time GROUP BY Customer.email ORDER BY num_flights'
    cursor.execute(query)
    customers = cursor.fetchall()

    return render_template('/staffrevenue.html', yearly_rev = yearly_rev, yearly_ticket = yearly_ticket, monthly_rev = monthly_rev, monthly_ticket = monthly_ticket, range_rev = range_rev, range_ticket= range_ticket,session=session['user'], customers=customers)

@auth.route('/staff_manage_flight', methods=['GET', 'POST'])
def manage_flight():    
    flight_number = request.form['flight_number']
    airline_name = request.form['airline_name']
    departure_date = request.form['departure_date']
    departure_time = request.form['departure_time']
    cursor = conn.cursor()
    query = 'SELECT * FROM flight WHERE flight_number = %s AND departure_date = %s AND departure_time = %s AND airline_name = %s'
    cursor.execute(query, (flight_number, departure_date, departure_time, airline_name))
    flight = cursor.fetchone()
    query = 'SELECT * FROM airport'
    cursor.execute(query)
    airports = cursor.fetchall()
    query = 'SELECT * FROM airplane WHERE airline_name = %s'
    cursor.execute(query, (session['user']['airline_name']))
    airplanes = cursor.fetchall()
    cursor.close()
    return render_template('modify flight.html', flight = flight, session=session['user'], airplanes = airplanes, airports = airports)

@auth.route('/view_review', methods=['GET', 'POST'])
def view_review():
    flight_number = request.form['flight_number']
    departure_date = request.form['departure_date']
    departure_time = request.form['departure_time']

    cursor = conn.cursor()
    query = 'SELECT * FROM reviews WHERE flight_number = %s AND departure_date = %s AND  departure_time = %s '
    cursor.execute(query,(flight_number,departure_date,departure_time))
    reviews = cursor.fetchall()

    query = 'SELECT AVG(rating) as avg_rating FROM reviews WHERE flight_number = %s AND departure_date = %s AND  departure_time = %s '
    cursor.execute(query,(flight_number,departure_date,departure_time))
    avg = cursor.fetchone()
    cursor.close()
    return render_template('view_review.html',session=session['user'], reviews= reviews, avg = int(avg['avg_rating']))

@auth.route('/view_customers', methods=['GET', 'POST'])
def view_customers():
    flight_number = request.form['flight_number']
    departure_date = request.form['departure_date']
    departure_time = request.form['departure_time']

    cursor = conn.cursor()
    query = 'SELECT DISTINCT customer.email, customer.first_name, customer.last_name FROM purchased INNER JOIN ticket INNER JOIN customer ON purchased.email=customer.email WHERE flight_number = %s AND departure_date = %s AND  departure_time = %s '
    cursor.execute(query,(flight_number,departure_date,departure_time))
    customers = cursor.fetchall()


    return render_template('view_customers.html',session=session['user'], customers= customers)


@auth.route('/custfinance', methods=['GET', 'POST'])
def custrevenue():

    monthly_rev = 0
    monthly_ticket = 0
    yearly_rev = 0
    yearly_ticket = 0
    range_rev = 0
    range_ticket = 0

    cursor = conn.cursor()
    query = 'SELECT sum(price) AS revenue, COUNT(*) AS sales FROM ticket JOIN purchased ON ticket.ticket_id=purchased.ticket_id JOIN flight ON ticket.flight_number=flight.flight_number WHERE email=%s AND purchased.purchase_date >= DATE_SUB(NOW(), INTERVAL 1 YEAR)'
    cursor.execute(query, session['user']['email'])
    yrevenue = cursor.fetchone()
    yearly_rev = yrevenue['revenue']
    yearly_ticket = yrevenue['sales']

    query = 'SELECT sum(price) AS revenue, COUNT(*) AS sales FROM ticket JOIN purchased ON ticket.ticket_id=purchased.ticket_id JOIN flight ON ticket.flight_number=flight.flight_number WHERE email = %s AND purchased.purchase_date >= DATE_SUB(NOW(), INTERVAL 1 MONTH)'
    cursor.execute(query, session['user']['email'])
    mrevenue = cursor.fetchone()
    monthly_rev = mrevenue['revenue']
    monthly_ticket = mrevenue['sales']

    return render_template('/custfinance.html', yearly_rev = yearly_rev, yearly_ticket = yearly_ticket, monthly_rev = monthly_rev, monthly_ticket = monthly_ticket, range_rev = range_rev, range_ticket= range_ticket, session=session['user'])

@auth.route('/custrange', methods=['GET', 'POST'])
def custrange():

    start = request.form['start']
    end = request.form['end']
    monthly_rev = 0
    monthly_ticket = 0
    yearly_rev = 0
    yearly_ticket = 0
    range_rev = 0
    range_ticket = 0

    cursor = conn.cursor()
    'SELECT sum(price) AS revenue, COUNT(*) AS sales FROM ticket JOIN purchased ON ticket.ticket_id=purchased.ticket_id JOIN flight ON ticket.flight_number=flight.flight_number WHERE email = %s AND purchased.purchase_date >= DATE_SUB(NOW(), INTERVAL 1 YEAR)'
    cursor.execute(query, session['user']['email'])
    yrevenue = cursor.fetchone()
    yearly_rev = yrevenue['revenue']
    yearly_ticket = yrevenue['sales']

    query = 'SELECT sum(price) AS revenue, COUNT(*) AS sales FROM ticket JOIN purchased ON ticket.ticket_id=purchased.ticket_id JOIN flight ON ticket.flight_number=flight.flight_number WHERE email = %s AND purchased.purchase_date >= DATE_SUB(NOW(), INTERVAL 1 MONTH)'
    cursor.execute(query, session['user']['email'])
    mrevenue = cursor.fetchone()
    monthly_rev = mrevenue['revenue']
    monthly_ticket = mrevenue['sales']

    query = 'SELECT sum(price) AS revenue, COUNT(*) AS sales FROM ticket JOIN purchased ON ticket.ticket_id=purchased.ticket_id JOIN flight ON ticket.flight_number=flight.flight_number WHERE email = %s AND purchase_date BETWEEN {start} AND {end}'
    cursor.execute(query, (session['user']['email'],start,end))
    rrevenue = cursor.fetchone()
    range_rev = rrevenue['revenue']
    range_ticket = rrevenue['sales']

    return render_template('/custfinance.html', yearly_rev = yearly_rev, yearly_ticket = yearly_ticket, monthly_rev = monthly_rev, monthly_ticket = monthly_ticket, range_rev = range_rev, range_ticket= range_ticket,session=session['user'])
