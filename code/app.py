from flask import Flask, request, jsonify, render_template, redirect
from flask_cors import CORS
import sqlite3, os

app = Flask(__name__)
CORS(app)

DB_PATH = os.getenv("DB_PATH", "EventManagement.db")


def initialize_database():
    """
    Check and initialize the database if necessary.
    """
    conn = None
    try:
        db_exists = os.path.exists(DB_PATH)
        conn = sqlite3.connect(DB_PATH)

        if db_exists and is_database_initialized(conn):
            print("Database is already initialized.")
        else:
            print("Database is uninitialized or missing. Setting up...")
            setup_database(conn)

    except sqlite3.Error as err:
        print(f"Database connection error: {err}")
    finally:
        if conn:
            conn.close()


def is_database_initialized(conn):
    """
    Check if the database is initialized by looking for the existence of the 'Customer' table.
    """
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='Customer';"
        )
        result = cursor.fetchone()
        return result is not None  # Database is initialized if 'Customer' table exists
    except sqlite3.Error as err:
        print(f"Error checking database initialization: {err}")
        return False


def setup_database(conn):
    """
    Create necessary tables in the database.
    """
    cursor = conn.cursor()

    # Create tables
    cursor.execute(
        """
    CREATE TABLE Customer (
        cid INTEGER PRIMARY KEY,
        mail TEXT NOT NULL UNIQUE,
        credit_info TEXT,
        f_name TEXT,
        l_name TEXT
    );
    """
    )

    cursor.execute(
        """
    CREATE TABLE Event (
        eid INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        type TEXT,
        time TEXT,
        date TEXT,
        capacity INTEGER
    );
    """
    )

    cursor.execute(
        """
    CREATE TABLE Ticket (
        tid INTEGER PRIMARY KEY,
        type TEXT,
        price REAL,
        availability BOOLEAN DEFAULT 1,
        seat_number INTEGER
    );
    """
    )

    cursor.execute(
        """
    CREATE TABLE Reservation (
        rid INTEGER PRIMARY KEY,
        eid INTEGER,
        cid INTEGER,
        date TEXT,
        total_price REAL,
        tickets_number INTEGER,
        FOREIGN KEY (eid) REFERENCES Event(eid),
        FOREIGN KEY (cid) REFERENCES Customer(cid)
    );
    """
    )

    cursor.execute(
        """
    CREATE TABLE Contains (
        eid INTEGER,
        tid INTEGER,
        PRIMARY KEY (eid, tid),
        FOREIGN KEY (eid) REFERENCES Event(eid),
        FOREIGN KEY (tid) REFERENCES Ticket(tid)
    );
    """
    )

    cursor.execute(
        """
    CREATE TABLE Makes (
        cid INTEGER,
        rid INTEGER,
        PRIMARY KEY (cid, rid),
        FOREIGN KEY (cid) REFERENCES Customer(cid),
        FOREIGN KEY (rid) REFERENCES Reservation(rid)
    );
    """
    )

    cursor.execute(
        """
    CREATE TABLE Has (
        tid INTEGER,
        eid INTEGER,
        PRIMARY KEY (tid, eid),
        FOREIGN KEY (tid) REFERENCES Ticket(tid),
        FOREIGN KEY (eid) REFERENCES Event(eid)
    );
    """
    )

    conn.commit()
    print("Database setup completed successfully.")


def db_connection():
    conn = sqlite3.connect(DB_PATH)  # Connect to the database
    conn.row_factory = sqlite3.Row  # This will return rows as dictionaries
    return conn


# Route to render the home page
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/login")
def login_page():
    return redirect("/", code=302)


# Route to manage customers: GET (fetch customers) and POST (add new customer)
@app.route("/customers", methods=["GET", "POST"])
def manage_customers():
    conn = db_connection()
    cursor = conn.cursor()

    try:
        # Handle GET request: fetch all customers from the database
        if request.method == "GET":
            cursor.execute(
                "SELECT * FROM Customer"
            )  # Execute SQL query to get all customers
            customers = [
                dict(row) for row in cursor.fetchall()
            ]  # Convert each row into a dictionary
            return jsonify(customers)  # Return the list of customers as a JSON response

        # Handle POST request: add a new customer to the database
        if request.method == "POST":
            new_customer = (
                request.json
            )  # Get the new customer data from the request body (in JSON format)
            
            # Validate required fields
            required_fields = ["mail", "f_name", "l_name"]
            for field in required_fields:
                if not new_customer.get(field):
                    return jsonify({"message": f"Missing required field: {field}"}), 400
            
            # Basic email validation
            if "@" not in new_customer["mail"] or "." not in new_customer["mail"]:
                return jsonify({"message": "Invalid email format"}), 400
            
            # Execute SQL query to insert the new customer into the Customer table
            cursor.execute(
                """
            INSERT INTO Customer (mail, credit_info, f_name, l_name)
            VALUES (?, ?, ?, ?)
            """,
                (
                    new_customer["mail"],
                    new_customer.get("credit_info", ""),
                    new_customer["f_name"],
                    new_customer["l_name"],
                ),
            )
            conn.commit()  # Commit the transaction to save the new customer
            return (
                jsonify({"message": "Customer added successfully!", "cid": cursor.lastrowid}),
                201,
            )  # Return success message
    except sqlite3.IntegrityError:
        return (
            jsonify({"message": "Error: Email already exists"}),
            409,
        )  # Return conflict error
    except Exception as e:
        return (
            jsonify({"message": f"Error: {str(e)}"}),
            500,
        )  # Return error message
    finally:
        conn.close()  # Always close the connection


# Route to manage events: GET (fetch events) and POST (add new event)
@app.route("/events", methods=["GET", "POST"])
def manage_events():
    conn = db_connection()
    cursor = conn.cursor()

    try:
        # Handle GET request: fetch all events from the database
        if request.method == "GET":
            cursor.execute("SELECT * FROM Event")  # Execute SQL query to get all events
            events = [
                dict(row) for row in cursor.fetchall()
            ]  # Convert each row into a dictionary
            return jsonify(events)  # Return the list of events as a JSON response

        # Handle POST request: add a new event to the database
        if request.method == "POST":
            new_event = (
                request.json
            )  # Get the new event data from the request body (in JSON format)
            
            # Validate required fields
            required_fields = ["name", "type", "time", "date", "capacity"]
            for field in required_fields:
                if not new_event.get(field):
                    return jsonify({"message": f"Missing required field: {field}"}), 400
            
            # Validate capacity is a positive integer
            try:
                capacity = int(new_event["capacity"])
                if capacity <= 0:
                    return jsonify({"message": "Capacity must be a positive number"}), 400
            except ValueError:
                return jsonify({"message": "Capacity must be a valid number"}), 400
            
            # Execute SQL query to insert the new event into the Event table
            cursor.execute(
                """
            INSERT INTO Event (name, type, time, date, capacity)
            VALUES (?, ?, ?, ?, ?)
            """,
                (
                    new_event["name"],
                    new_event["type"],
                    new_event["time"],
                    new_event["date"],
                    capacity,
                ),
            )
            id = cursor.lastrowid  # Get the ID of the newly inserted event
            conn.commit()  # Commit the transaction to save the new event
            return (
                jsonify({"message": "Event added successfully!", "id": id}),
                201,
            )  # Return success message with event ID
    except Exception as e:
        return jsonify({"message": f"Error: {str(e)}"}), 500  # Return error message
    finally:
        conn.close()  # Always close the connection


# Route to fetch the list of event names (for dropdown)
@app.route("/eventnames", methods=["GET"])
def dropdown_events():
    conn = db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT eid,name FROM Event"
        )  # Execute SQL query to get event ID and name
        events = [
            dict(row) for row in cursor.fetchall()
        ]  # Convert each row into a dictionary
        return jsonify(events)  # Return the list of event names as a JSON response
    except Exception as e:
        return jsonify({"message": f"Error: {str(e)}"}), 500
    finally:
        conn.close()


# Route to manage tickets: GET (fetch tickets) and POST (add new ticket)
@app.route("/tickets", methods=["GET", "POST"])
def manage_tickets():
    conn = db_connection()
    cursor = conn.cursor()

    try:
        # Handle GET request: fetch all tickets from the database
        if request.method == "GET":
            cursor.execute("SELECT * FROM Ticket")  # Execute SQL query to get all tickets
            tickets = [
                dict(row) for row in cursor.fetchall()
            ]  # Convert each row into a dictionary
            return jsonify(tickets)  # Return the list of tickets as a JSON response

        # Handle POST request: add a new ticket to the database
        if request.method == "POST":
            new_ticket = (
                request.json
            )  # Get the new ticket data from the request body (in JSON format)
            
            # Validate required fields
            required_fields = ["type", "price", "seat_number"]
            for field in required_fields:
                if field not in new_ticket:
                    return jsonify({"message": f"Missing required field: {field}"}), 400
            
            # Validate price is a positive number
            try:
                price = float(new_ticket["price"])
                if price < 0:
                    return jsonify({"message": "Price cannot be negative"}), 400
            except ValueError:
                return jsonify({"message": "Price must be a valid number"}), 400
            
            # Execute SQL query to insert the new ticket into the Ticket table
            cursor.execute(
                """
            INSERT INTO Ticket (type, price, availability, seat_number)
            VALUES (?, ?, ?, ?)
            """,
                (
                    new_ticket["type"],
                    price,
                    new_ticket.get("availability", 1),
                    new_ticket["seat_number"],
                ),
            )
            id = cursor.lastrowid  # Get the ID of the newly inserted ticket
            conn.commit()  # Commit the transaction to save the new ticket
            return (
                jsonify({"message": "Ticket added successfully!", "tid": id}),
                201,
            )  # Return success message with ticket ID
    except Exception as e:
        return jsonify({"message": f"Error: {str(e)}"}), 500  # Return error message
    finally:
        conn.close()  # Always close the connection


# Rotue to get reservations and add reservations
@app.route("/reservations", methods=["GET", "POST"])
def manage_reservations():
    # Establish a database connection
    conn = db_connection()
    cursor = conn.cursor()

    # Handling GET request to retrieve all reservations
    if request.method == "GET":
        cursor.execute("SELECT * FROM Reservation")
        reservations = [
            dict(row) for row in cursor.fetchall()
        ]  # Convert query result to dictionary
        return jsonify(reservations)  # Return list of reservations in JSON format

    # Handling POST request to create a new reservation
    if request.method == "POST":
        new_reservation = (
            request.json
        )  # Get the data from the request body (in JSON format)
        try:
            cursor.execute(
                """
            INSERT INTO Reservation (eid, cid, date, total_price, tickets_number)
            VALUES (?, ?, ?, ?, ?)
            """,
                (
                    new_reservation["eid"],
                    new_reservation["cid"],
                    new_reservation["date"],
                    new_reservation["total_price"],
                    new_reservation["tickets_number"],
                ),
            )
            inserted_id = cursor.lastrowid  # Get the ID of the newly inserted reservation
            conn.commit()  # Commit the transaction
            return (
                jsonify({"message": "Reservation added successfully!", "rid": inserted_id}),
                201,
            )  # Return success message
        except Exception as e:
            return jsonify({"message": f"Error: {str(e)}"}), 500  # Return error message
        finally:
            conn.close()  # Always close the connection


@app.route("/contains", methods=["GET", "POST"])
def manage_contains():
    # Establish a database connection
    conn = db_connection()
    cursor = conn.cursor()

    try:
        # Handling GET request to retrieve all entries in the Contains table
        if request.method == "GET":
            cursor.execute("SELECT * FROM Contains")
            res = [
                dict(row) for row in cursor.fetchall()
            ]  # Convert query result to dictionary
            return jsonify(res)  # Return the list of relations in JSON format

        # Handling POST request to add a new relation in the Contains table
        if request.method == "POST":
            new_contains = (
                request.json
            )  # Get the data from the request body (in JSON format)
            cursor.execute(
                """
            INSERT INTO Contains (eid, tid)
            VALUES (?, ?)
            """,
                (new_contains["eid"], new_contains["tid"]),
            )  # Insert the relation into the database
            conn.commit()  # Commit the transaction
            return (
                jsonify({"message": "Relation added successfully!"}),
                201,
            )  # Return success message
    except Exception as e:
        return jsonify({"message": f"Error: {str(e)}"}), 500  # Return error message
    finally:
        conn.close()  # Always close the connection


@app.route("/makes", methods=["GET", "POST"])
def manage_makes():
    # Establish a database connection
    conn = db_connection()
    cursor = conn.cursor()

    try:
        # Handling GET request to retrieve all entries in the Makes table
        if request.method == "GET":
            cursor.execute("SELECT * FROM Makes")
            res = [
                dict(row) for row in cursor.fetchall()
            ]  # Convert query result to dictionary
            return jsonify(res)  # Return the list of relations in JSON format

        # Handling POST request to add a new relation in the Makes table
        if request.method == "POST":
            new_makes = request.json  # Get the data from the request body (in JSON format)
            cursor.execute(
                """
            INSERT INTO Makes (cid, rid)
            VALUES (?, ?)
            """,
                (new_makes["cid"], new_makes["rid"]),
            )  # Insert the relation into the database
            conn.commit()  # Commit the transaction
            return (
                jsonify({"message": "Relation added successfully!"}),
                201,
            )  # Return success message
    except Exception as e:
        return jsonify({"message": f"Error: {str(e)}"}), 500  # Return error message
    finally:
        conn.close()  # Always close the connection


@app.route("/has", methods=["GET", "POST"])
def manage_has():
    # Establish a database connection
    conn = db_connection()
    cursor = conn.cursor()

    try:
        # Handling GET request to retrieve all entries in the Has table
        if request.method == "GET":
            cursor.execute("SELECT * FROM Has")
            res = [
                dict(row) for row in cursor.fetchall()
            ]  # Convert query result to dictionary
            return jsonify(res)  # Return the list of relations in JSON format

        # Handling POST request to add a new relation in the Has table
        if request.method == "POST":
            new_has = request.json  # Get the data from the request body (in JSON format)
            cursor.execute(
                """
            INSERT INTO Has (tid, eid)
            VALUES (?, ?)
            """,
                (new_has["tid"], new_has["eid"]),
            )  # Insert the relation into the database
            conn.commit()  # Commit the transaction
            return (
                jsonify({"message": "Relation added successfully!"}),
                201,
            )  # Return success message
    except Exception as e:
        return jsonify({"message": f"Error: {str(e)}"}), 500  # Return error message
    finally:
        conn.close()  # Always close the connection


# route to get available tickets
@app.route("/available_tickets/<int:eid>", methods=["GET"])
def get_available_tickets(eid):
    # Establish a database connection
    conn = db_connection()
    cursor = conn.cursor()

    # Handling GET request to retrieve available tickets for a specific event (eid)
    try:
        cursor.execute(
            """
        SELECT * FROM Ticket 
        WHERE availability = 1 AND tid IN (SELECT tid FROM Contains WHERE eid = ?)
        """,
            (eid,),
        )  # Query tickets that are available and belong to the event (eid)
        tickets = [
            dict(row) for row in cursor.fetchall()
        ]  # Convert query result to dictionary
        conn.close()  # Close the connection
        return jsonify(tickets)  # Return the list of available tickets in JSON format
    except:
        conn.close()  # Close the connection if an error occurs
        return jsonify({"message": "Error"}), 500  # Return error message


# route to get customer reservations
@app.route("/customer_reservations/<int:cid>", methods=["GET"])
def get_customer_reservations(cid):
    # Establish a database connection
    conn = db_connection()
    cursor = conn.cursor()

    # Handling GET request to retrieve all reservations for a specific customer (cid)
    try:
        cursor.execute(
            """
        SELECT * FROM Reservation WHERE cid = ?
        """,
            (cid,),
        )  # Query reservations for the given customer ID
        reservations = [
            dict(row) for row in cursor.fetchall()
        ]  # Convert query result to dictionary
        conn.close()  # Close the connection
        return jsonify(reservations)  # Return the list of reservations in JSON format
    except:
        conn.close()  # Close the connection if an error occurs
        return jsonify({"message": "Error"}), 500  # Return error message


# route to get reservation cost
@app.route("/reservation_cost/<int:rid>", methods=["GET"])
def get_reservation_cost(rid):
    # Establish a database connection
    conn = db_connection()
    cursor = conn.cursor()

    # Handling GET request to calculate the total cost of a reservation (rid)
    try:
        cursor.execute(
            """
        SELECT SUM(Ticket.price) AS total_cost
        FROM Ticket 
        JOIN Contains ON Ticket.tid = Contains.tid
        JOIN Reservation ON Contains.eid = Reservation.eid
        WHERE Reservation.rid = ?
        """,
            (rid,),
        )  # Join Ticket, Contains, and Reservation tables to calculate total cost for the given reservation ID
        cost = cursor.fetchone()  # Fetch the calculated total cost
        conn.close()  # Close the connection
        return jsonify(
            {"total_cost": cost["total_cost"] if cost else 0}
        )  # Return the total cost, or 0 if no cost found
    except:
        conn.close()  # Close the connection if an error occurs
        return jsonify({"message": "Error"}), 500  # Return error message


# route to delete customers
@app.route("/customers/<int:cid>", methods=["DELETE"])
def delete_customer(cid):
    # Establish a database connection
    conn = db_connection()
    cursor = conn.cursor()

    try:
        # Check if customer has any reservations
        cursor.execute("SELECT COUNT(*) FROM Reservation WHERE cid = ?", (cid,))
        if cursor.fetchone()[0] > 0:
            return jsonify({"message": "Cannot delete customer with active reservations. Cancel reservations first."}), 400
        
        # Delete customer record by customer ID
        cursor.execute("DELETE FROM Customer WHERE cid = ?", (cid,))
        if cursor.rowcount == 0:
            return jsonify({"message": f"Customer with ID {cid} not found"}), 404
        conn.commit()
        return (
            jsonify({"message": f"Customer with ID {cid} deleted successfully!"}),
            200,
        )
    except Exception as e:
        return jsonify({"message": f"Error: {str(e)}"}), 500
    finally:
        conn.close()


# route to delete events
@app.route("/events/<int:eid>", methods=["DELETE"])
def delete_event(eid):
    # Establish a database connection
    conn = db_connection()
    cursor = conn.cursor()

    try:
        # Check if event has any reservations
        cursor.execute("SELECT COUNT(*) FROM Reservation WHERE eid = ?", (eid,))
        if cursor.fetchone()[0] > 0:
            return jsonify({"message": "Cannot delete event with active reservations. Use cancel event instead."}), 400
        
        cursor.execute("DELETE FROM Event WHERE eid = ?", (eid,))
        if cursor.rowcount == 0:
            return jsonify({"message": f"Event with ID {eid} not found"}), 404
        conn.commit()
        return (
            jsonify({"message": f"Event with ID {eid} deleted successfully!"}),
            200,
        )
    except Exception as e:
        return jsonify({"message": f"Error: {str(e)}"}), 500
    finally:
        conn.close()


# Route to delete a specific ticket by its ID
@app.route("/tickets/<int:tid>", methods=["DELETE"])
def delete_ticket(tid):
    # Establish a database connection
    conn = db_connection()
    cursor = conn.cursor()

    # Handling DELETE request to remove a ticket by its ID
    try:
        cursor.execute(
            "DELETE FROM Ticket WHERE tid = ?", (tid,)
        )  # Delete the ticket record
        conn.commit()  # Commit the changes
        return (
            jsonify({"message": f"Ticket with ID {tid} deleted successfully!"}),
            200,
        )  # Return success message
    except Exception as e:
        return jsonify({"message": f"Error: {str(e)}"}), 500  # Return error message
    finally:
        conn.close()  # Always close the connection


# Route to delete a specific reservation by its ID
@app.route("/reservations/<int:rid>", methods=["DELETE"])
def delete_reservation(rid):
    # Establish a database connection
    conn = db_connection()
    cursor = conn.cursor()

    try:
        # First delete from Makes table
        cursor.execute("DELETE FROM Makes WHERE rid = ?", (rid,))
        
        # Delete the reservation record
        cursor.execute("DELETE FROM Reservation WHERE rid = ?", (rid,))
        if cursor.rowcount == 0:
            return jsonify({"message": f"Reservation with ID {rid} not found"}), 404
        conn.commit()
        return (
            jsonify({"message": f"Reservation with ID {rid} deleted successfully!"}),
            200,
        )
    except Exception as e:
        conn.rollback()
        return jsonify({"message": f"Error: {str(e)}"}), 500
    finally:
        conn.close()


# Route to get available seats for a specific event and seat type
@app.route("/available_seats/<int:eid>/<string:seat_type>", methods=["GET"])
def get_available_seats(eid, seat_type):
    # Establish a database connection
    conn = db_connection()
    cursor = conn.cursor()

    # Handling GET request to fetch available seats of a specific type for a given event
    try:
        cursor.execute(
            """
        SELECT * FROM Ticket 
        WHERE availability = 1 AND type = ? AND tid IN (SELECT tid FROM Contains WHERE eid = ?)
        """,
            (seat_type, eid),
        )  # Query to get available tickets of a specific seat type for the event
        tickets = [
            dict(row) for row in cursor.fetchall()
        ]  # Convert query result to a dictionary
        conn.close()  # Close the connection
        return jsonify(tickets)  # Return the list of available tickets in JSON format
    except:
        conn.close()  # Close the connection if an error occurs
        return jsonify({"message": "Error"}), 500  # Return error message


# Route to get the price of a ticket for a specific event and seat type
@app.route("/ticket_price/<int:eid>/<string:seat_type>", methods=["GET"])
def get_price_of_ticket(eid, seat_type):
    # Establish a database connection
    conn = db_connection()
    cursor = conn.cursor()

    # Handling GET request to fetch the price of a ticket for a specific event and seat type
    try:
        cursor.execute(
            """
        SELECT price FROM Ticket 
        WHERE type = ? AND tid IN (SELECT tid FROM Has WHERE eid = ?)
        LIMIT 1
        """,
            (seat_type, eid),
        )  # Query to get the price of the ticket for the event and seat type
        price = cursor.fetchone()[0]  # Fetch the price of the ticket
        print(price)  # Print the price (for debugging purposes)
        conn.close()  # Close the connection
        return jsonify({"price": price}), 200  # Return the price of the ticket as JSON
    except:
        conn.close()  # Close the connection if an error occurs
        return jsonify({"message": "Error"}), 500  # Return error message


# Route to get all available seats for a specific event
@app.route("/available_seats/<int:eid>", methods=["GET"])
def get_available_seats_all(eid):
    # Establish a database connection
    conn = db_connection()
    cursor = conn.cursor()

    # Handling GET request to fetch all available seats for a given event
    try:
        cursor.execute(
            """
        SELECT seat_number, type FROM Ticket 
        WHERE availability = 1 AND tid IN (SELECT tid FROM Has WHERE eid = ?)
        """,
            (eid,),
        )  # Query to get all available seats for the event
        seats = [
            dict(row) for row in cursor.fetchall()
        ]  # Convert query result to dictionary
        conn.close()  # Close the connection
        return jsonify(seats)  # Return the available seats as JSON
    except:
        conn.close()  # Close the connection if an error occurs
        return jsonify({"message": "Error"}), 500  # Return error message


# Helper function to check if there are enough available tickets for a given event and data
def check_we_have_enough(data):
    # Establish a database connection
    conn = db_connection()
    cursor = conn.cursor()

    # Initialize variables to hold the ticket IDs and the desired ticket count
    tids = []
    wanted_count = list(
        data["tickets"].values()
    )  # List of the number of tickets requested per seat type

    # Try block to execute the queries and fetch ticket IDs
    try:
        for seat_type in enumerate(list(data["tickets"].keys())):
            cursor.execute(
                """
            SELECT tid FROM Ticket 
            WHERE availability = 1 AND type= ? AND tid IN (SELECT tid FROM Has WHERE eid = ?)
            LIMIT %s
            """
                % wanted_count[seat_type[0]],
                (seat_type[1], data["eid"]),
            )  # Query to fetch available tickets for the seat type and event
            tmp_tids = [
                row[0] for row in cursor.fetchall()
            ]  # Fetch the ticket IDs and store them in the tids list
            tids.extend(tmp_tids)  # Add ticket IDs to the main list
    except:
        conn.close()  # Close the connection if an error occurs
        return (
            500,
            jsonify({"message": "Error fetching tids"}),
            1,
        )  # Return error code and message if fetching ticket IDs fails

    # Check if there are enough tickets available
    if len(tids) < sum(
        wanted_count
    ):  # If the available tickets are less than the requested tickets
        return (
            500,
            jsonify({"message": "Error: Not enough available seats"}),
            1,
        )  # Return error message

    return 0, 0, tids  # Return success (0) and the list of ticket IDs (tids)


# Function to fetch customer ID from their email
def get_cid_from_email(mail):
    conn = db_connection()
    cursor = conn.cursor()
    try:
        # Query to find customer ID based on email
        cursor.execute(
            """
        SELECT cid FROM Customer 
        WHERE mail = ?
        """,
            (mail,),
        )
        result = cursor.fetchone()
        if result is None:
            return (
                404,
                jsonify({"message": "Customer not found with this email"}),
                1,
            )
        cid = result[0]
        return 0, 0, cid  # Successful operation
    except Exception as e:
        return (
            500,
            jsonify({"message": f"Error finding customer from email: {str(e)}"}),
            1,
        )  # Error case
    finally:
        conn.close()


# Route to reserve tickets for a customer
@app.route("/reserve_tickets", methods=["POST"])
def reserve_tickets():
    data = request.json  # Data from the request body
    
    # Validate required fields
    required_fields = ["eid", "cid", "tickets", "tickets_number", "date"]
    for field in required_fields:
        if field not in data:
            return jsonify({"message": f"Missing required field: {field}"}), 400
    
    price_arr = []

    # Get the price for each ticket type
    for s_type in list(data["tickets"].keys()):
        jdata, status = get_price_of_ticket(data["eid"], s_type)
        if status != 500:
            price_arr.append(jdata.get_json()["price"])
        else:
            return jsonify({"message": "Error fetching ticket price"}), 500

    # Calculate total price based on ticket quantity and price
    data["total_price"] = sum(
        [a * b for a, b in zip(list(data["tickets"].values()), price_arr)]
    )

    # Check if enough tickets are available
    s, msg, data["tickets"] = check_we_have_enough(data)
    if s == 500:
        return msg, s  # Not enough seats

    # Get customer ID from email
    s, msg, data["cid"] = get_cid_from_email(data["cid"])
    if s != 0:
        return msg, s  # Error fetching customer ID

    # Connect to the database to insert reservation details
    conn = db_connection()
    cursor = conn.cursor()

    try:
        # Insert reservation details into the Reservation table
        cursor.execute(
            """
        INSERT INTO Reservation (eid, cid, date, total_price, tickets_number)
        VALUES (?, ?, ?, ?, ?)
        """,
            (
                data["eid"],
                data["cid"],
                data["date"],
                data["total_price"],
                data["tickets_number"],
            ),
        )
        rid = cursor.lastrowid  # Get the reservation ID
        tickets = data["tickets"]

        # For each ticket, update availability and add entry in Contains table
        for tid in tickets:
            cursor.execute(
                """
            UPDATE Ticket SET availability = 0 WHERE tid = ?
            """,
                (tid,),
            )
            cursor.execute(
                """
            INSERT INTO Contains (eid, tid) VALUES (?, ?)
            """,
                (data["eid"], tid),
            )

        # Insert entry into Makes table linking customer and reservation
        cursor.execute(
            """
        INSERT INTO Makes(cid, rid)
        VALUES (?, ?)
        """,
            (data["cid"], rid),
        )

        conn.commit()  # Commit the transaction
        return (
            jsonify(
                {
                    "message": "Reservation completed successfully!",
                    "reservation_id": rid,
                    "total_price": data["total_price"],
                }
            ),
            201,
        )
    except Exception as e:
        conn.rollback()
        return jsonify({"message": f"Error: {str(e)}"}), 500
    finally:
        conn.close()


# Route to cancel a reservation
@app.route("/cancel_reservation", methods=["POST"])
def cancel_reservation():
    conn = db_connection()
    cursor = conn.cursor()

    try:
        # Retrieve email and optional reservation_id from request data
        data = request.json
        email = data.get("email")
        specific_rid = data.get("reservation_id")  # Optional: cancel specific reservation

        if not email:
            return jsonify({"message": "Email is required"}), 400

        # Step 1: Get customer ID (cid) from Customer table based on email
        cursor.execute(
            """SELECT cid FROM Customer WHERE mail = ?""",
            (email,),
        )
        customer = cursor.fetchone()

        if not customer:
            return jsonify({"message": "Customer not found"}), 404

        cid = customer[0]

        # Step 2: Retrieve reservation(s) associated with the customer
        if specific_rid:
            cursor.execute(
                """SELECT rid, eid FROM Reservation WHERE cid = ? AND rid = ?""",
                (cid, specific_rid),
            )
        else:
            cursor.execute(
                """SELECT rid, eid FROM Reservation WHERE cid = ?""",
                (cid,),
            )
        
        reservations = cursor.fetchall()

        if not reservations:
            return jsonify({"message": "No reservations found for the customer"}), 404

        canceled_count = 0
        for reservation in reservations:
            rid = reservation[0]
            eid = reservation[1]

            # Step 3: Get tickets from Contains table for this reservation's event
            # that were marked as unavailable (booked)
            cursor.execute(
                """SELECT tid FROM Contains WHERE eid = ?""",
                (eid,),
            )
            tickets = cursor.fetchall()

            # Step 4: Update ticket availability to 1 (available)
            for ticket in tickets:
                cursor.execute(
                    """UPDATE Ticket SET availability = 1 WHERE tid = ?""",
                    (ticket[0],),
                )

            # Step 5: Delete entries in Contains table related to the reservation
            cursor.execute(
                """DELETE FROM Contains WHERE eid = ?""",
                (eid,),
            )

            # Step 6: Delete entry in Makes table related to the reservation
            cursor.execute(
                """DELETE FROM Makes WHERE rid = ?""",
                (rid,),
            )

            # Step 7: Delete reservation entry from Reservation table
            cursor.execute(
                """DELETE FROM Reservation WHERE rid = ?""",
                (rid,),
            )
            canceled_count += 1

        conn.commit()
        return jsonify({
            "message": f"Successfully canceled {canceled_count} reservation(s)!",
            "canceled_count": canceled_count
        }), 200

    except Exception as e:
        conn.rollback()
        return jsonify({"message": f"Error: {str(e)}"}), 500
    finally:
        conn.close()


# Route to cancel an event and refund all reservations
@app.route("/cancel_event/<int:eid>", methods=["DELETE", "GET"])
def cancel_event(eid):
    conn = db_connection()
    cursor = conn.cursor()
    try:
        # First, get all ticket IDs associated with this event (before deleting Has)
        cursor.execute(
            """SELECT tid FROM Has WHERE eid = ?""",
            (eid,),
        )
        ticket_ids = [row[0] for row in cursor.fetchall()]

        # Delete rows from Contains table related to the event
        cursor.execute(
            """
        DELETE FROM Contains 
        WHERE eid = ?""",
            (eid,),
        )

        # Delete rows from Makes table related to reservations of this event
        cursor.execute(
            """
        DELETE FROM Makes 
        WHERE rid IN (SELECT rid FROM Reservation WHERE eid = ?)""",
            (eid,),
        )

        # Delete rows from Has table related to the event
        cursor.execute(
            """
        DELETE FROM Has 
        WHERE eid = ?""",
            (eid,),
        )

        # Delete tickets associated with the event using previously fetched IDs
        if ticket_ids:
            placeholders = ','.join('?' * len(ticket_ids))
            cursor.execute(
                f"""DELETE FROM Ticket WHERE tid IN ({placeholders})""",
                ticket_ids,
            )

        # Delete reservations related to the event
        cursor.execute(
            """
        DELETE FROM Reservation 
        WHERE eid = ?""",
            (eid,),
        )

        # Delete the event itself
        cursor.execute(
            """
        DELETE FROM Event 
        WHERE eid = ?""",
            (eid,),
        )

        conn.commit()  # Commit all changes at once
        return (
            jsonify(
                {
                    "message": f"Event with ID {eid} canceled and all reservations refunded."
                }
            ),
            200,
        )
    except Exception as e:
        conn.rollback()  # Rollback on error
        return jsonify({"message": f"Error: {str(e)}"}), 500
    finally:
        conn.close()  # Always close the connection


# Route to fetch event revenue based on event ID or all events
@app.route("/revenue_event", methods=["POST"])
def event_revenue():
    data = request.json
    print(data)  # Log data for debugging
    conn = db_connection()
    cursor = conn.cursor()

    if data["type"] == "VIP":
        if data["eid"] != "All":
            try:
                # Calculate VIP revenue for a specific event
                cursor.execute(
                    """
                SELECT SUM(Ticket.price)
                FROM Ticket
                JOIN Contains ON Ticket.tid = Contains.tid
                WHERE Contains.eid = ? AND Ticket.type = 'VIP'
                """,
                    (int(data["eid"]),),
                )
                revenue = cursor.fetchone()[0]
                conn.close()
                return jsonify({"total_revenue": revenue if revenue else 0})
            except:
                conn.close()
                return jsonify({"message": "Error"}), 500
        else:
            try:
                # Calculate total VIP revenue across all events
                cursor.execute(
                    """
                SELECT SUM(Ticket.price)
                FROM Ticket
                JOIN Contains ON Ticket.tid = Contains.tid
                WHERE Ticket.type = 'VIP'
                """
                )
                revenue = cursor.fetchone()[0]
                conn.close()
                return jsonify({"total_revenue": revenue if revenue else 0})
            except:
                conn.close()
                return jsonify({"message": "Error"}), 500
    else:
        if data["eid"] != "All":
            try:
                # Calculate revenue for a specific event
                cursor.execute(
                    """
                SELECT SUM(total_price) FROM Reservation WHERE eid = ?
                """,
                    (int(data["eid"]),),
                )
                revenue = cursor.fetchone()[0]
                conn.close()
                return jsonify({"total_revenue": revenue if revenue else 0})
            except:
                conn.close()
                return (
                    jsonify({"message": "Error"}),
                    500,
                )  # Error fetching revenue for specific event
        else:
            try:
                # Calculate total revenue for all events
                cursor.execute(
                    """
                SELECT SUM(total_price) FROM Reservation
                """
                )
                revenue = cursor.fetchone()[0]
                conn.close()
                return jsonify({"total_revenue": revenue if revenue else 0})
            except:
                conn.close()
                return jsonify({"message": "Error2"}), 500
    return jsonify({"message": "Error3"}), 500


# Route to get the most popular event based on the number of reservations
@app.route("/most_popular_event", methods=["GET"])
def most_popular_event():
    conn = db_connection()
    cursor = conn.cursor()
    try:
        # Query to select the event name and the number of reservations for each event
        # It groups the results by event id and orders by the number of reservations
        cursor.execute(
            """
        SELECT Event.name, COUNT(Reservation.rid) AS reservations_count 
        FROM Event 
        JOIN Reservation ON Event.eid = Reservation.eid 
        GROUP BY Event.eid 
        ORDER BY reservations_count DESC 
        LIMIT 1
        """
        )
        # Fetch the event name and the count of reservations
        pos = cursor.fetchone()
        event = pos[0]
        count = pos[1]
        conn.close()
        # Return the name of the most popular event and its reservation count
        return jsonify({"name": event, "reservations_count": count})
    except:
        conn.close()
        # In case of error, return a message
        return jsonify({"message": "Error"}), 500


# Route to get the highest revenue-generating event within a given date range
@app.route("/highest_revenue_event", methods=["POST"])
def highest_revenue_event():
    conn = db_connection()
    cursor = conn.cursor()
    data = request.json
    try:
        # Query to get the event with the highest revenue within the specified date range
        cursor.execute(
            """
        SELECT Event.name, SUM(Reservation.total_price) AS revenue 
        FROM Event 
        JOIN Reservation ON Event.eid = Reservation.eid 
        WHERE Reservation.date BETWEEN ? AND ? 
        GROUP BY Event.eid 
        ORDER BY revenue DESC 
        LIMIT 1
        """,
            (data["start_date"], data["end_date"]),
        )
        # Fetch the event name and revenue
        pos = cursor.fetchone()
        event = pos[0]
        revenue = pos[1]
        conn.close()
        # Return the event's name and revenue
        return jsonify({"name": event, "revenue": revenue})
    except:
        conn.close()
        # In case of error, return a message
        return jsonify({"message": "Error"}), 500


# Route to get active reservations made between a given start and end date
@app.route("/active_reserve", methods=["POST"])
def active_reservations():
    conn = db_connection()
    cursor = conn.cursor()
    data = request.json
    try:
        # Query to fetch all active reservations within the date range
        cursor.execute(
            """
        SELECT cid, eid, date, tickets_number, total_price
        FROM Reservation 
        WHERE Reservation.date BETWEEN ? AND ? 
        """,
            (data["start_date"], data["end_date"]),
        )
        # Convert the result rows into a list of dictionaries
        active = [dict(row) for row in cursor.fetchall()]
        conn.close()
        # Return the list of active reservations
        return jsonify(active), 200
    except:
        conn.close()
        # In case of error, return a message
        return jsonify({"message": "Error"}), 500


# Route to get revenue by ticket type across all events
@app.route("/revenue_by_ticket_type", methods=["GET"])
def revenue_by_ticket_type():
    conn = db_connection()
    cursor = conn.cursor()
    try:
        # Query to calculate the total revenue generated by each ticket type
        cursor.execute(
            """
        SELECT type, SUM(price) AS total_revenue 
        FROM Ticket 
        JOIN Contains ON Ticket.tid = Contains.tid 
        GROUP BY type
        """
        )
        # Fetch the revenue by ticket type
        revenue = [dict(row) for row in cursor.fetchall()]
        conn.close()
        # Return the revenue breakdown by ticket type
        return jsonify(revenue)
    except:
        conn.close()
        # In case of error, return a message
        return jsonify({"message": "Error"}), 500


if __name__ == "__main__":
    # Initialize the database and start the Flask app
    initialize_database()
    app.run(debug=True)