# Airlines
Airline Reservation System

## Collaborators
Dahong Jiang and Ahnaf Kazi

## About
A program coded in Python Flask, HTML, and SQL to simulate an Airline Reservation System.

The core attributes of the program includes:

- Public Page
- Staff Page
- Customer Page

To access either the staff or customer page, users must enter credentials in the form of
a username and password, which are all stored in an SQL database

## Notable Features
- Web based application
- Constraints on user, creating security between different types of users
- Session management, requiring previous sessions to be destroyed before new sessions are created, as well as keeping relevant information within their respective sessions
- Secure against cross-site scripting vulnerabilities, such as changing url
- Easy to use interface for all users

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

## Comments
The project is constructed in a web-based application form, mainly with Python Flask. 
Since we weren't familiar with web-based development, Python Flask, HTML, and were learning SQL, this was an interesting project to tackle. Some difficulties that we faced 
upon diving into the project were figuring out how we wanted to format the pages to connect with each other along with the header. Initially we had multiple different headers
for base, customer, and staff but we learned to streamline the headers and their navigations. Some enjoyable aspects of the project were learning how to link the database to the
fill in boxes, writing SQL queries to fetch data and use them for display, and connecting the pages together. Overall, we learned a substantial amount throughout the entire process.
