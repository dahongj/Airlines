# Airlines
Airline Reservation System

Dahong Jiang and Ahnaf Kazi

A program coded in Python Flask, HTML, and SQL to simulate an Airline Reservation System.

The core attributes of the program includes:

- Public Page
- Staff Page
- Customer Page

To access either the staff or customer page, users must enter credentials in the form of
a username and password, which are all stored in an SQL database

## Public Page
The public page contains:
- Search functionality for flights based on source city, destination, date, and airport names
- Registration for either staff or customer members
- Encrypted login for either staff or customer members

## Customer Page
The customer can log in and view:
- Their purchased future flights
- Functionality to search for a flight from the flight database
- Purchase a ticket from the flight list
- Cancel a future flight
- Give a comment and a rating on a previous flight taken
- Track total spending
- Logout

## Staff Page
The staff can log in and view:
- The flight list
- Create a new flight
- Change the status of a flight(on-time/delayed)
- Add a plane to the system
- Add an airport to the system
- View the flight rating and comments
- View frequent customers and the flights that the customer has taken
- View ticket sale reports
- View total revenue
