from flask import Flask, render_template, request, redirect, session
from database import get_db_connection

app = Flask(__name__)

# =========================================================
# SECRET KEY
# =========================================================

app.secret_key = "blood_donation_secret_key"


# =========================================================
# LOCATION COORDINATES
# =========================================================

locations = {

    "Chennai": (13.0827, 80.2707),

    "Trichy": (10.7905, 78.7047),

    "Madurai": (9.9252, 78.1198),

    "Coimbatore": (11.0168, 76.9558),

    "Salem": (11.6643, 78.1460),

    "Erode": (11.3410, 77.7172),

    "Vellore": (12.9165, 79.1325),

    "Thanjavur": (10.7870, 79.1378),

    "Tirunelveli": (8.7139, 77.7567),

    "Kanchipuram": (12.8342, 79.7036),

    "Pondicherry": (11.9416, 79.8083),

    "Hosur": (12.7409, 77.8253),

    "Dindigul": (10.3673, 77.9803),

    "Thoothukudi": (8.7642, 78.1348),

    "Nagercoil": (8.1833, 77.4119)
}


# =========================================================
# HOME PAGE
# =========================================================

@app.route("/")
def home():

    return render_template("index.html")


# =========================================================
# COMBINED LOGIN - PATIENT / DONOR / HOSPITAL / ADMIN
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"].strip()
        password = request.form["password"]
        role = request.form["role"]

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # =================================================
        # PATIENT LOGIN
        # =================================================
        if role == "patient":

            cursor.execute("""
                SELECT *
                FROM patients
                WHERE email = %s
                AND password = %s
            """, (email, password))

            patient = cursor.fetchone()

            cursor.close()
            connection.close()

            if patient:
                session.clear()
                session["patient_id"] = patient["patient_id"]
                session["patient_name"] = patient["name"]
                session["role"] = "patient"

                return redirect("/patient/dashboard")

            return "Invalid patient email or password!"

        # =================================================
        # DONOR LOGIN
        # =================================================
        elif role == "donor":

            cursor.execute("""
                SELECT
                    user_id,
                    name,
                    email,
                    role
                FROM users
                WHERE email = %s
                AND password = %s
                AND role = 'donor'
            """, (email, password))

            donor = cursor.fetchone()

            cursor.close()
            connection.close()

            if donor:
                session.clear()
                session["donor_user_id"] = donor["user_id"]
                session["donor_name"] = donor["name"]
                session["role"] = "donor"

                return redirect("/donor/dashboard")

            return "Invalid donor email or password!"

        # =================================================
        # HOSPITAL LOGIN
        # =================================================
        elif role == "hospital":

            cursor.execute("""
                SELECT
                    hospital_id,
                    hospital_name,
                    email
                FROM hospital_users
                WHERE email = %s
                AND password = %s
            """, (email, password))

            hospital = cursor.fetchone()

            cursor.close()
            connection.close()

            if hospital:
                session.clear()
                session["hospital_id"] = hospital["hospital_id"]
                session["hospital_name"] = hospital["hospital_name"]
                session["hospital_email"] = hospital["email"]
                session["role"] = "hospital"

                return redirect("/hospital/screening")

            return "Invalid hospital email or password!"

        # =================================================
        # ADMIN LOGIN
        # =================================================
        elif role == "admin":

            cursor.execute("""
                SELECT
                    admin_id,
                    name,
                    email
                FROM admin_users
                WHERE email = %s
                AND password = %s
            """, (email, password))

            admin = cursor.fetchone()

            cursor.close()
            connection.close()

            if admin:
                session.clear()
                session["admin_id"] = admin["admin_id"]
                session["admin_name"] = admin["name"]
                session["admin_email"] = admin["email"]
                session["role"] = "admin"

                return redirect("/admin/dashboard")

            return "Invalid admin email or password!"

        # =================================================
        # INVALID ROLE
        # =================================================
        else:

            cursor.close()
            connection.close()

            return "Please select Patient, Donor, Hospital, or Admin!"

    return render_template("login.html")


# =========================================================
# DONOR REGISTRATION
# =========================================================

@app.route("/donor/register", methods=["GET", "POST"])
def donor_register():

    if request.method == "POST":

        # =================================================
        # BASIC ACCOUNT DETAILS
        # =================================================

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        # =================================================
        # DONOR DETAILS
        # =================================================

        blood_group = request.form["blood_group"]
        age = request.form["age"]
        gender = request.form["gender"]
        phone = request.form["phone"]
        location = request.form["location"]
        last_donation_date = request.form["last_donation_date"]

        # =================================================
        # LOCATION → LATITUDE / LONGITUDE
        # =================================================

        if location not in locations:

            return "Invalid location selected!"

        latitude, longitude = locations[location]

        # =================================================
        # DATABASE CONNECTION
        # =================================================

        connection = get_db_connection()
        cursor = connection.cursor()

        try:

            # =================================================
            # INSERT INTO USERS TABLE
            # =================================================

            user_query = """
            INSERT INTO users
            (
                name,
                email,
                password,
                role
            )
            VALUES (%s, %s, %s, %s)
            """

            user_values = (
                name,
                email,
                password,
                "donor"
            )

            cursor.execute(user_query, user_values)

            # Get newly created user ID
            user_id = cursor.lastrowid


            # =================================================
            # INSERT INTO DONORS TABLE
            # =================================================

            donor_query = """
            INSERT INTO donors
            (
                user_id,
                blood_group,
                age,
                gender,
                phone,
                location,
                last_donation_date,
                availability,
                latitude,
                longitude
            )
            VALUES
            (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            donor_values = (
                user_id,
                blood_group,
                age,
                gender,
                phone,
                location,
                last_donation_date,
                "Available",
                latitude,
                longitude
            )

            cursor.execute(donor_query, donor_values)

            # Save both records
            connection.commit()

            cursor.close()
            connection.close()

            return redirect("/login")


        except Exception as e:

            connection.rollback()

            cursor.close()
            connection.close()

            return "Donor registration failed: " + str(e)


    return render_template("donor_register.html")


# =========================================================
# PATIENT REGISTRATION
# =========================================================

@app.route("/patient/register", methods=["GET", "POST"])
def patient_register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        phone = request.form["phone"]
        password = request.form["password"]
        blood_group = request.form["blood_group"]
        hospital = request.form["hospital"]
        location = request.form["location"]

        connection = get_db_connection()
        cursor = connection.cursor()

        query = """
        INSERT INTO patients
        (
            name,
            email,
            phone,
            password,
            blood_group,
            hospital,
            location
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """

        values = (
            name,
            email,
            phone,
            password,
            blood_group,
            hospital,
            location
        )

        cursor.execute(query, values)

        connection.commit()

        cursor.close()
        connection.close()

        return "Patient registration successful!"


    return render_template("patient_register.html")


# =========================================================
# PATIENT DASHBOARD
# =========================================================

@app.route("/patient/dashboard")
def patient_dashboard():

    if "patient_id" not in session:

        return redirect("/login")


    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)


    # =====================================================
    # GET BLOOD INVENTORY
    # =====================================================

    cursor.execute("""
        SELECT
            inventory_id,
            blood_group,
            units_available
        FROM blood_inventory
        ORDER BY inventory_id
    """)

    inventory = cursor.fetchall()


    cursor.close()
    connection.close()


    return render_template(
        "patient_dashboard.html",
        patient_name=session["patient_name"],
        inventory=inventory
    )


# =========================================================
# BLOOD INVENTORY
# =========================================================

@app.route("/patient/blood-inventory")
def blood_inventory():

    if "patient_id" not in session:

        return redirect("/login")


    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)


    cursor.execute("""
        SELECT
            blood_group,
            units_available
        FROM blood_inventory
        ORDER BY inventory_id
    """)

    inventory = cursor.fetchall()


    cursor.close()
    connection.close()


    return render_template(
        "blood_inventory.html",
        inventory=inventory
    )


# =========================================================
# PATIENT BLOOD REQUEST
# =========================================================

@app.route("/patient/request-blood", methods=["GET", "POST"])
def request_blood():

    if "patient_id" not in session:

        return redirect("/login")


    if request.method == "POST":

        blood_group = request.form["blood_group"]
        units_required = request.form["units_required"]
        hospital = request.form["hospital_name"]
        location = request.form["location"]
        
        urgency = request.form["urgency"]

        if urgency not in ("Normal", "Urgent", "Critical"):
            urgency = "Normal"

        patient_id = session["patient_id"]



        # =================================================
        # GET HOSPITAL LOCATION COORDINATES
        # =================================================

        if location not in locations:

            return "Invalid hospital location selected!"


        hospital_latitude, hospital_longitude = locations[location]


        connection = get_db_connection()
        cursor = connection.cursor()


        # =================================================
        # INSERT BLOOD REQUEST
        # =================================================

        query = """
        INSERT INTO blood_requests
        (
            patient_id,
            blood_group,
            units_required,
            hospital_name,
            location,
            urgency,
            status,
            hospital_latitude,
            hospital_longitude
        )
        VALUES
        (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """


        values = (
            patient_id,
            blood_group,
            units_required,
            hospital,
            location,
            urgency,
            "Pending",
            hospital_latitude,
            hospital_longitude
        )


        cursor.execute(query, values)

        connection.commit()

        cursor.close()
        connection.close()


        return "Blood request submitted successfully!"


    return render_template("request_blood.html")


# =========================================================
# FIND RECOMMENDED DONORS
# =========================================================

@app.route("/patient/find-donors")
def find_donors():

    if "patient_id" not in session:
        return redirect("/login")

    patient_id = session["patient_id"]

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        query = """
            SELECT
                br.request_id,
                br.patient_id,
                br.blood_group AS requested_blood_group,
                br.units_required,
                br.urgency,
                CASE
                    WHEN br.urgency = 'Critical' THEN 1
                    WHEN br.urgency = 'Urgent' THEN 2
                    ELSE 3
                END AS urgency_priority,
                br.hospital_name,
                d.donor_id,
                d.blood_group AS donor_blood_group,
                d.phone AS donor_phone,
                d.location AS donor_location,
                d.age,
                d.gender,
                d.last_donation_date,
                drm.distance_km
            FROM blood_requests br
            JOIN donors d
                ON d.blood_group = br.blood_group
            LEFT JOIN donor_request_matches drm
                ON drm.request_id = br.request_id
                AND drm.donor_id = d.donor_id
            WHERE br.patient_id = %s
                AND br.status = 'Pending'
                AND d.availability = 'Available'
                AND d.age BETWEEN 18 AND 65
                AND (
                    d.last_donation_date IS NULL
                    OR d.last_donation_date <=
                       DATE_SUB(CURDATE(), INTERVAL 90 DAY)
                )
            ORDER BY
                urgency_priority ASC,
                br.request_id ASC,
                drm.distance_km ASC
        """

        cursor.execute(query, (patient_id,))
        recommendations = cursor.fetchall()

        current_request = None
        rank = 0

        for donor in recommendations:
            if donor["request_id"] != current_request:
                current_request = donor["request_id"]
                rank = 1
            else:
                rank += 1

            donor["rank"] = rank

        return render_template(
            "find_donors.html",
            recommendations=recommendations
        )

    finally:
        cursor.close()
        connection.close()




# =========================================================
# TRACK BLOOD REQUEST
# =========================================================

@app.route("/patient/track-request")
def track_request():

    if "patient_id" not in session:

        return redirect("/login")


    patient_id = session["patient_id"]


    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)


    query = """
    SELECT
        request_id,
        blood_group,
        units_required,
        hospital_name,
        location,
        urgency,
        status,
        created_at
    FROM blood_requests
    WHERE patient_id = %s
    ORDER BY created_at DESC
    """


    cursor.execute(query, (patient_id,))

    requests = cursor.fetchall()


    cursor.close()
    connection.close()


    return render_template(
        "track_request.html",
        requests=requests
    )

# =========================================================
# PATIENT VIEW DONOR RESPONSES
# =========================================================

@app.route("/patient/donor-responses")
def patient_donor_responses():

    if "patient_id" not in session:
        return redirect("/login")

    patient_id = session["patient_id"]

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    query = """
    SELECT
        dr.response_id,
        dr.request_id,
        dr.response_status,
        dr.responded_at,

        d.donor_id,
        d.blood_group,
        d.phone,
        d.location,
        d.age,
        d.gender,

        u.name AS donor_name,
        u.email AS donor_email

    FROM donor_responses dr

    JOIN blood_requests br
        ON dr.request_id = br.request_id

    JOIN donors d
        ON dr.donor_id = d.donor_id

    JOIN users u
        ON d.user_id = u.user_id

    WHERE br.patient_id = %s

    ORDER BY dr.responded_at DESC
    """

    cursor.execute(query, (patient_id,))

    responses = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "patient_donor_responses.html",
        responses=responses
    )

# =========================================================
# PATIENT SELECTS DONOR
# =========================================================

@app.route("/patient/select-donor/<int:response_id>", methods=["POST"])
def select_donor(response_id):

    if "patient_id" not in session:
        return redirect("/login")

    patient_id = session["patient_id"]

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    # Verify response belongs to this patient
    cursor.execute("""
        SELECT
            dr.response_id,
            dr.request_id,
            dr.donor_id,
            dr.response_status
        FROM donor_responses dr
        JOIN blood_requests br
            ON dr.request_id = br.request_id
        WHERE dr.response_id = %s
          AND br.patient_id = %s
    """, (response_id, patient_id))

    response = cursor.fetchone()

    if not response:
        cursor.close()
        connection.close()
        return "Donor response not found!"

    # Check request status
    cursor.execute("""
        SELECT status
        FROM blood_requests
        WHERE request_id = %s
    """, (response["request_id"],))

    request_data = cursor.fetchone()

    if not request_data:
        cursor.close()
        connection.close()
        return "Blood request not found!"

    if request_data["status"] != "Pending":
        cursor.close()
        connection.close()
        return "This blood request is no longer pending."

    # Accept selected donor
    cursor.execute("""
        UPDATE donor_responses
        SET response_status = 'Accepted'
        WHERE response_id = %s
    """, (response_id,))

    # Reject other donors for the same request
    cursor.execute("""
        UPDATE donor_responses
        SET response_status = 'Rejected'
        WHERE request_id = %s
          AND response_id != %s
    """, (response["request_id"], response_id))

    # Get request information for notification
    cursor.execute("""
        SELECT
            request_id,
            blood_group,
            units_required,
            hospital_name,
            location
        FROM blood_requests
        WHERE request_id = %s
    """, (response["request_id"],))

    request_info = cursor.fetchone()

    if request_info:
        message = (
            f"You have been selected for Blood Request "
            f"#{request_info['request_id']}. "
            f"Blood Group: {request_info['blood_group']}, "
            f"Units Required: {request_info['units_required']}, "
            f"Hospital: {request_info['hospital_name']}, "
            f"Location: {request_info['location']}."
        )

        cursor.execute("""
            INSERT INTO donor_notifications
            (
                donor_id,
                request_id,
                message,
                is_read
            )
            VALUES (%s, %s, %s, %s)
        """, (
            response["donor_id"],
            response["request_id"],
            message,
            "No"
        ))
    # Keep blood_requests.status as Pending.
    # The database status ENUM supports Pending, Fulfilled and Cancelled.
    connection.commit()

    cursor.close()
    connection.close()

    return redirect("/patient/donor-responses")

# =========================================================
# DONOR NOTIFICATIONS
# =========================================================

@app.route("/donor/notifications")
def donor_notifications():

    if "donor_user_id" not in session:
        return redirect("/login")

    user_id = session["donor_user_id"]

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    # Get donor ID
    cursor.execute("""
        SELECT donor_id
        FROM donors
        WHERE user_id = %s
    """, (user_id,))

    donor = cursor.fetchone()

    if not donor:
        cursor.close()
        connection.close()
        return "Donor profile not found!"

    donor_id = donor["donor_id"]

    # Get notifications
    cursor.execute("""
        SELECT
            notification_id,
            request_id,
            message,
            is_read,
            created_at
        FROM donor_notifications
        WHERE donor_id = %s
        ORDER BY created_at DESC
    """, (donor_id,))

    notifications = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "donor_notifications.html",
        notifications=notifications
    )
# =========================================================
# DONOR DASHBOARD
# =========================================================

@app.route("/donor/dashboard")
def donor_dashboard():

    if "donor_user_id" not in session:

        return redirect("/login")


    user_id = session["donor_user_id"]


    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)


    query = """
    SELECT
        donor_id,
        blood_group,
        age,
        gender,
        phone,
        location,
        last_donation_date,
        availability
    FROM donors
    WHERE user_id = %s
    """


    cursor.execute(query, (user_id,))

    donor = cursor.fetchone()


    cursor.close()
    connection.close()


    if not donor:

        return "Donor profile not found!"


    return render_template(
        "donor_dashboard.html",
        donor=donor,
        donor_name=session["donor_name"]
    )


# =========================================================
# DONOR VIEW COMPATIBLE BLOOD REQUESTS WITH DISTANCE
# =========================================================

@app.route("/donor/blood-requests")
def donor_blood_requests():

    if "donor_user_id" not in session:

        return redirect("/login")


    user_id = session["donor_user_id"]


    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)


    # =====================================================
    # GET DONOR DETAILS
    # =====================================================

    donor_query = """
    SELECT
        donor_id,
        blood_group,
        location,
        latitude,
        longitude,
        availability
    FROM donors
    WHERE user_id = %s
    """


    cursor.execute(donor_query, (user_id,))

    donor = cursor.fetchone()


    if not donor:

        cursor.close()
        connection.close()

        return "Donor profile not found!"


    # =====================================================
    # ONLY AVAILABLE DONORS CAN VIEW MATCHING REQUESTS
    # =====================================================

    if donor["availability"] != "Available":

        cursor.close()
        connection.close()


        return render_template(
            "donor_blood_requests.html",
            requests=[],
            donor=donor,
            message="You are currently unavailable for donation."
        )


    donor_blood_group = donor["blood_group"]


    # =====================================================
    # FIND COMPATIBLE PENDING REQUESTS
    # =====================================================

    query = """
    SELECT
        br.request_id,
        br.blood_group,
        br.units_required,
        br.hospital_name,
        br.location,
        br.urgency,
        br.status,
        br.created_at,
        br.hospital_latitude,
        br.hospital_longitude,

        (
            6371 * ACOS(
                LEAST(
                    1,
                    GREATEST(
                        -1,
                        COS(RADIANS(br.hospital_latitude))
                        * COS(RADIANS(%s))
                        * COS(
                            RADIANS(%s)
                            - RADIANS(br.hospital_longitude)
                        )
                        +
                        SIN(RADIANS(br.hospital_latitude))
                        * SIN(RADIANS(%s))
                    )
                )
            )
        ) AS distance_km

    FROM blood_requests br

    WHERE br.status = 'Pending'

    AND
    (
        (%s = 'O-' AND br.blood_group IN
            ('O-', 'O+', 'A-', 'A+', 'B-', 'B+', 'AB-', 'AB+'))

        OR

        (%s = 'O+' AND br.blood_group IN
            ('O+', 'A+', 'B+', 'AB+'))

        OR

        (%s = 'A-' AND br.blood_group IN
            ('A-', 'A+', 'AB-', 'AB+'))

        OR

        (%s = 'A+' AND br.blood_group IN
            ('A+', 'AB+'))

        OR

        (%s = 'B-' AND br.blood_group IN
            ('B-', 'B+', 'AB-', 'AB+'))

        OR

        (%s = 'B+' AND br.blood_group IN
            ('B+', 'AB+'))

        OR

        (%s = 'AB-' AND br.blood_group IN
            ('AB-', 'AB+'))

        OR

        (%s = 'AB+' AND br.blood_group IN
            ('AB+'))
    )

    ORDER BY
        CASE
            WHEN br.urgency = 'Critical' THEN 1
            WHEN br.urgency = 'Urgent' THEN 2
            WHEN br.urgency = 'Normal' THEN 3
            ELSE 4
        END,

        distance_km ASC,

        br.created_at DESC
    """


    values = (

        donor["latitude"],
        donor["longitude"],
        donor["latitude"],

        donor_blood_group,
        donor_blood_group,
        donor_blood_group,
        donor_blood_group,
        donor_blood_group,
        donor_blood_group,
        donor_blood_group,
        donor_blood_group
    )


    cursor.execute(query, values)

    requests = cursor.fetchall()


    cursor.close()
    connection.close()


    return render_template(
        "donor_blood_requests.html",
        requests=requests,
        donor=donor
    )

# =========================================================
# DONOR RESPONDS TO BLOOD REQUEST
# =========================================================

@app.route("/donor/respond/<int:request_id>", methods=["POST"])
def donor_respond(request_id):

    # Check donor login
    if "donor_user_id" not in session:
        return redirect("/login")

    user_id = session["donor_user_id"]

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    # =====================================================
    # GET DONOR ID
    # =====================================================

    cursor.execute("""
        SELECT donor_id, availability
        FROM donors
        WHERE user_id = %s
    """, (user_id,))

    donor = cursor.fetchone()

    if not donor:
        cursor.close()
        connection.close()
        return "Donor profile not found!"

    # =====================================================
    # CHECK DONOR AVAILABILITY
    # =====================================================

    if donor["availability"] != "Available":

        cursor.close()
        connection.close()

        return "You are currently unavailable for donation."


    donor_id = donor["donor_id"]


    # =====================================================
    # CHECK WHETHER REQUEST EXISTS
    # =====================================================

    cursor.execute("""
        SELECT request_id
        FROM blood_requests
        WHERE request_id = %s
        AND status = 'Pending'
    """, (request_id,))

    blood_request = cursor.fetchone()

    if not blood_request:

        cursor.close()
        connection.close()

        return "Blood request not found or is no longer pending."


    # =====================================================
    # CHECK WHETHER DONOR ALREADY RESPONDED
    # =====================================================

    cursor.execute("""
        SELECT response_id
        FROM donor_responses
        WHERE request_id = %s
        AND donor_id = %s
    """, (request_id, donor_id))

    existing_response = cursor.fetchone()


    if existing_response:

        cursor.close()
        connection.close()

        return "You have already responded to this blood request."


    # =====================================================
    # SAVE DONOR RESPONSE
    # =====================================================

    cursor.execute("""
        INSERT INTO donor_responses
        (
            request_id,
            donor_id,
            response_status
        )
        VALUES (%s, %s, %s)
    """, (
        request_id,
        donor_id,
        "Interested"
    ))


    # =====================================================
    # AUTOMATICALLY CREATE HOSPITAL SCREENING
    # =====================================================

    cursor.execute("""
        SELECT screening_id
        FROM hospital_screenings
        WHERE request_id = %s
          AND donor_id = %s
    """, (
        request_id,
        donor_id
    ))

    existing_screening = cursor.fetchone()

    if not existing_screening:

        cursor.execute("""
            INSERT INTO hospital_screenings
            (
                request_id,
                donor_id,
                screening_status
            )
            VALUES (%s, %s, %s)
        """, (
            request_id,
            donor_id,
            "Pending"
        ))


    connection.commit()

    cursor.close()
    connection.close()


    return redirect("/donor/blood-requests")

# =========================================================
# DONOR UPDATE AVAILABILITY
# =========================================================

@app.route("/donor/update-availability", methods=["GET", "POST"])
def update_availability():

    if "donor_user_id" not in session:

        return redirect("/login")


    user_id = session["donor_user_id"]


    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)


    if request.method == "POST":

        availability = request.form["availability"]


        update_query = """
        UPDATE donors
        SET availability = %s
        WHERE user_id = %s
        """


        cursor.execute(
            update_query,
            (availability, user_id)
        )


        connection.commit()

        cursor.close()
        connection.close()


        return redirect("/donor/dashboard")


    # =====================================================
    # GET CURRENT AVAILABILITY
    # =====================================================

    query = """
    SELECT availability
    FROM donors
    WHERE user_id = %s
    """


    cursor.execute(query, (user_id,))

    donor = cursor.fetchone()


    cursor.close()
    connection.close()


    if not donor:

        return "Donor profile not found!"


    return render_template(
        "update_availability.html",
        availability=donor["availability"]
    )
# =========================================================
# ADMIN DASHBOARD
# =========================================================

@app.route("/admin/dashboard")
def admin_dashboard():

    if "admin_id" not in session or session.get("role") != "admin":
        return redirect("/login")

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("SELECT COUNT(*) AS total FROM patients")
    total_patients = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) AS total FROM donors")
    total_donors = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) AS total FROM hospital_users")
    total_hospitals = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) AS total FROM blood_requests")
    total_requests = cursor.fetchone()["total"]

    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM blood_requests
        WHERE status = 'Pending'
    """)
    pending_requests = cursor.fetchone()["total"]

    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM blood_requests
        WHERE status = 'Fulfilled'
    """)
    fulfilled_requests = cursor.fetchone()["total"]

    cursor.execute("""
        SELECT blood_group, units_available
        FROM blood_inventory
        ORDER BY inventory_id
    """)
    inventory = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "admin_dashboard.html",
        admin_name=session["admin_name"],
        total_patients=total_patients,
        total_donors=total_donors,
        total_hospitals=total_hospitals,
        total_requests=total_requests,
        pending_requests=pending_requests,
        fulfilled_requests=fulfilled_requests,
        inventory=inventory
    )

# =========================================================
# ADMIN - VIEW ALL USERS
# =========================================================

@app.route("/admin/users")
def admin_users():

    # Only Admin can access this page
    if "admin_id" not in session or session.get("role") != "admin":
        return redirect("/login")

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    # =====================================================
    # GET PATIENTS
    # =====================================================

    cursor.execute("""
        SELECT
            patient_id,
            name,
            email,
            phone,
            blood_group,
            hospital,
            location
        FROM patients
        ORDER BY patient_id DESC
    """)

    patients = cursor.fetchall()


    # =====================================================
    # GET DONORS
    # =====================================================

    cursor.execute("""
        SELECT
            u.user_id,
            u.name,
            u.email,
            d.phone,
            d.blood_group,
            d.location,
            d.availability
        FROM users u
        INNER JOIN donors d
            ON u.user_id = d.user_id
        WHERE u.role = 'donor'
        ORDER BY u.user_id DESC
    """)

    donors = cursor.fetchall()


    # =====================================================
    # GET HOSPITALS
    # =====================================================

    cursor.execute("""
        SELECT
            hospital_id,
            hospital_name,
            email
        FROM hospital_users
        ORDER BY hospital_id DESC
    """)

    hospitals = cursor.fetchall()


    cursor.close()
    connection.close()


    return render_template(
        "admin_users.html",
        admin_name=session["admin_name"],
        patients=patients,
        donors=donors,
        hospitals=hospitals
    )

    # =========================================================
# ADMIN - VIEW ALL BLOOD REQUESTS
# =========================================================

@app.route("/admin/blood-requests")
def admin_blood_requests():

    # Only Admin can access this page
    if "admin_id" not in session or session.get("role") != "admin":
        return redirect("/login")

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    # Get all blood requests with patient information
    cursor.execute("""
        SELECT
            br.request_id,
            br.patient_id,
            p.name AS patient_name,
            p.email AS patient_email,
            br.blood_group,
            br.units_required,
            br.hospital_name,
            br.location,
            br.urgency,
            br.status,
            br.created_at
        FROM blood_requests br
        LEFT JOIN patients p
            ON br.patient_id = p.patient_id
        ORDER BY br.created_at DESC
    """)

    requests = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "admin_blood_requests.html",
        admin_name=session["admin_name"],
        requests=requests
    )
    # =========================================================
# ADMIN - MARK BLOOD REQUEST AS FULFILLED
# =========================================================

@app.route("/admin/blood-request/<int:request_id>/fulfill", methods=["POST"])
def admin_fulfill_blood_request(request_id):

    # Only Admin can perform this action
    if "admin_id" not in session or session.get("role") != "admin":
        return redirect("/login")

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    # Check that the request exists
    cursor.execute("""
        SELECT
            request_id,
            status
        FROM blood_requests
        WHERE request_id = %s
    """, (request_id,))

    blood_request = cursor.fetchone()

    if not blood_request:

        cursor.close()
        connection.close()

        return "Blood request not found!"


    # Only pending requests can be fulfilled
    if blood_request["status"] != "Pending":

        cursor.close()
        connection.close()

        return "Only pending blood requests can be marked as fulfilled!"


    # Update request status
    cursor.execute("""
        UPDATE blood_requests
        SET status = 'Fulfilled'
        WHERE request_id = %s
    """, (request_id,))

    connection.commit()

    cursor.close()
    connection.close()


    return redirect("/admin/blood-requests")

    # =========================================================
# ADMIN - CANCEL BLOOD REQUEST
# =========================================================

@app.route("/admin/blood-request/<int:request_id>/cancel", methods=["POST"])
def admin_cancel_blood_request(request_id):

    # Only Admin can perform this action
    if "admin_id" not in session or session.get("role") != "admin":
        return redirect("/login")

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    # Check whether the request exists
    cursor.execute("""
        SELECT
            request_id,
            status
        FROM blood_requests
        WHERE request_id = %s
    """, (request_id,))

    blood_request = cursor.fetchone()

    if not blood_request:

        cursor.close()
        connection.close()

        return "Blood request not found!"


    # Only Pending requests can be cancelled
    if blood_request["status"] != "Pending":

        cursor.close()
        connection.close()

        return "Only pending blood requests can be cancelled!"


    # Change status to Cancelled
    cursor.execute("""
        UPDATE blood_requests
        SET status = 'Cancelled'
        WHERE request_id = %s
    """, (request_id,))

    connection.commit()

    cursor.close()
    connection.close()


    return redirect("/admin/blood-requests")

    # =========================================================
# ADMIN - VIEW HOSPITAL SCREENING RECORDS
# =========================================================

@app.route("/admin/screenings")
def admin_screenings():

    # Only Admin can access this page
    if "admin_id" not in session or session.get("role") != "admin":
        return redirect("/login")

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            hs.screening_id,
            hs.request_id,
            hs.donor_id,
            hs.screening_status,
            hs.remarks,
            hs.screened_at,

            br.blood_group,
            br.units_required,
            br.hospital_name,
            br.location,
            br.urgency,
            br.status AS request_status,

            u.name AS donor_name,
            u.email AS donor_email

        FROM hospital_screenings hs

        LEFT JOIN blood_requests br
            ON hs.request_id = br.request_id

        LEFT JOIN donors d
            ON hs.donor_id = d.donor_id

        LEFT JOIN users u
            ON d.user_id = u.user_id

        ORDER BY hs.screening_id DESC
    """)

    screenings = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "admin_screenings.html",
        admin_name=session["admin_name"],
        screenings=screenings
    )
    # =========================================================
# ADMIN - BLOOD INVENTORY MANAGEMENT
# =========================================================

@app.route("/admin/inventory")
def admin_inventory():

    # Only Admin can access this page
    if "admin_id" not in session or session.get("role") != "admin":
        return redirect("/login")

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            inventory_id,
            blood_group,
            units_available,
            last_updated,
            blood_bank_id
        FROM blood_inventory
        ORDER BY blood_group
    """)

    inventory = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "admin_inventory.html",
        admin_name=session["admin_name"],
        inventory=inventory
    )
    # =========================================================
# ADMIN - UPDATE BLOOD INVENTORY
# =========================================================

@app.route("/admin/inventory/update/<int:inventory_id>", methods=["GET", "POST"])
def admin_update_inventory(inventory_id):

    # Only Admin can access this page
    if "admin_id" not in session or session.get("role") != "admin":
        return redirect("/login")

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    # Get the selected inventory record
    cursor.execute("""
        SELECT
            inventory_id,
            blood_group,
            units_available,
            blood_bank_id,
            last_updated
        FROM blood_inventory
        WHERE inventory_id = %s
    """, (inventory_id,))

    inventory = cursor.fetchone()

    if not inventory:

        cursor.close()
        connection.close()

        return "Blood inventory record not found!"


    # =====================================================
    # UPDATE
    # =====================================================

    if request.method == "POST":

        units_available = request.form.get("units_available")

        try:

            units_available = int(units_available)

            if units_available < 0:

                cursor.close()
                connection.close()

                return "Units available cannot be negative!"

        except (TypeError, ValueError):

            cursor.close()
            connection.close()

            return "Please enter a valid number of units!"


        cursor.execute("""
            UPDATE blood_inventory
            SET units_available = %s
            WHERE inventory_id = %s
        """, (units_available, inventory_id))

        connection.commit()

        cursor.close()
        connection.close()

        return redirect("/admin/inventory")


    cursor.close()
    connection.close()

    return render_template(
        "admin_update_inventory.html",
        admin_name=session["admin_name"],
        inventory=inventory
    )
    # =========================================================
# ADMIN - ADD BLOOD STOCK
# =========================================================

@app.route("/admin/inventory/add", methods=["GET", "POST"])
def admin_add_inventory():

    # Only Admin can access this page
    if "admin_id" not in session or session.get("role") != "admin":
        return redirect("/login")

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    if request.method == "POST":

        blood_group = request.form.get("blood_group", "").strip()
        units_to_add = request.form.get("units_to_add", "").strip()

        # Validate blood group
        allowed_groups = [
            "A+", "A-",
            "B+", "B-",
            "AB+", "AB-",
            "O+", "O-"
        ]

        if blood_group not in allowed_groups:

            cursor.close()
            connection.close()

            return "Invalid blood group!"


        # Validate units
        try:

            units_to_add = int(units_to_add)

            if units_to_add <= 0:

                cursor.close()
                connection.close()

                return "Units to add must be greater than 0!"

        except (TypeError, ValueError):

            cursor.close()
            connection.close()

            return "Please enter a valid number of units!"


        # Check whether this blood group already exists
        cursor.execute("""
            SELECT
                inventory_id
            FROM blood_inventory
            WHERE blood_group = %s
            LIMIT 1
        """, (blood_group,))

        existing = cursor.fetchone()


        if existing:

            # Add units to existing stock
            cursor.execute("""
                UPDATE blood_inventory
                SET units_available = units_available + %s
                WHERE inventory_id = %s
            """, (
                units_to_add,
                existing["inventory_id"]
            ))

        else:

            # Create a new inventory record
            cursor.execute("""
                INSERT INTO blood_inventory
                (
                    blood_group,
                    units_available
                )
                VALUES (%s, %s)
            """, (
                blood_group,
                units_to_add
            ))


        connection.commit()

        cursor.close()
        connection.close()

        return redirect("/admin/inventory")


    cursor.close()
    connection.close()

    return render_template(
        "admin_add_inventory.html",
        admin_name=session["admin_name"]
    )
# =========================================================
# HOSPITAL SCREENING DASHBOARD
# =========================================================

@app.route("/hospital/screening")
def hospital_screening():

    if "hospital_id" not in session or session.get("role") != "hospital":
        return redirect("/login")

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    query = """
    SELECT
        hs.screening_id,
        hs.request_id,
        hs.donor_id,
        hs.screening_status,
        hs.remarks,
        hs.screened_at,

        br.blood_group,
        br.units_required,
        br.hospital_name,
        br.location,
        br.urgency,

        d.age,
        d.gender,
        d.phone,
        d.location AS donor_location,
        d.last_donation_date,

        u.name AS donor_name,
        u.email AS donor_email

    FROM hospital_screenings hs

    JOIN blood_requests br
        ON hs.request_id = br.request_id

    JOIN donors d
        ON hs.donor_id = d.donor_id

    JOIN users u
        ON d.user_id = u.user_id

    ORDER BY hs.screened_at DESC
    """

    cursor.execute(query)

    screenings = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "hospital_screening.html",
        screenings=screenings
    )
# =========================================================
# HOSPITAL APPROVE / REJECT DONOR
# =========================================================

# =========================================================
# HOSPITAL APPROVE / REJECT DONOR
# =========================================================

@app.route("/hospital/screen/<int:screening_id>", methods=["POST"])
def hospital_screen(screening_id):

    if "hospital_id" not in session or session.get("role") != "hospital":
        return redirect("/login")

    decision = request.form["decision"]
    remarks = request.form.get("remarks", "").strip()

    if decision not in ["Approved", "Rejected"]:
        return "Invalid screening decision!"

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT screening_id, request_id, donor_id, screening_status
            FROM hospital_screenings
            WHERE screening_id = %s
        """, (screening_id,))
        screening = cursor.fetchone()

        if not screening:
            return "Screening record not found!"

        if screening["screening_status"] != "Pending":
            return "This donor has already been screened."

        cursor.execute("""
            SELECT donor_id, blood_group
            FROM donors
            WHERE donor_id = %s
        """, (screening["donor_id"],))
        donor = cursor.fetchone()

        if not donor:
            return "Donor profile not found!"

        cursor.execute("""
            UPDATE hospital_screenings
            SET screening_status = %s, remarks = %s, screened_at = CURRENT_TIMESTAMP
            WHERE screening_id = %s
        """, (decision, remarks, screening_id))

        if decision == "Approved":
            cursor.execute("""
                UPDATE donors
                SET availability = 'Unavailable'
                WHERE donor_id = %s
            """, (screening["donor_id"],))

            cursor.execute("""
                SELECT inventory_id
                FROM blood_inventory
                WHERE blood_group = %s
                LIMIT 1
            """, (donor["blood_group"],))
            inventory = cursor.fetchone()

            if not inventory:
                connection.rollback()
                return (
                    "Blood group " + str(donor["blood_group"]) +
                    " does not exist in blood inventory. "
                    "Please add this blood group to inventory first."
                )

            cursor.execute("""
                UPDATE blood_inventory
                SET units_available = units_available + 1
                WHERE inventory_id = %s
            """, (inventory["inventory_id"],))

            # Mark the related blood request as fulfilled
            cursor.execute("""
                UPDATE blood_requests
                SET status = 'Fulfilled'
                WHERE request_id = %s
                  AND status IN ('Pending', 'Approved')
            """, (screening["request_id"],))

        elif decision == "Rejected":
            cursor.execute("""
                UPDATE donors
                SET availability = 'Available'
                WHERE donor_id = %s
            """, (screening["donor_id"],))

        connection.commit()

    except Exception as e:
        connection.rollback()
        return "Hospital screening update failed: " + str(e)

    finally:
        cursor.close()
        connection.close()

    return redirect("/hospital/screening")

# =========================================================
# HOSPITAL LOGOUT
# =========================================================

@app.route("/hospital/logout")
def hospital_logout():

    session.clear()
    return redirect("/login")


# =========================================================
# ADMIN LOGOUT
# =========================================================

@app.route("/admin/logout")
def admin_logout():

    session.clear()
    return redirect("/login")

# =========================================================
# PATIENT NOTIFICATIONS
# =========================================================

@app.route("/patient/notifications")
def patient_notifications():

    if "patient_id" not in session:
        return redirect("/login")

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    # Create patient notifications table if it does not exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patient_notifications (
            notification_id INT AUTO_INCREMENT PRIMARY KEY,
            patient_id INT NOT NULL,
            request_id INT NULL,
            message TEXT NOT NULL,
            is_read VARCHAR(10) DEFAULT 'No',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Get notifications for logged-in patient
    cursor.execute("""
        SELECT
            notification_id,
            request_id,
            message,
            is_read,
            created_at
        FROM patient_notifications
        WHERE patient_id = %s
        ORDER BY created_at DESC
    """, (session["patient_id"],))

    notifications = cursor.fetchall()

    # Mark notifications as read
    cursor.execute("""
        UPDATE patient_notifications
        SET is_read = 'Yes'
        WHERE patient_id = %s
    """, (session["patient_id"],))

    connection.commit()

    cursor.close()
    connection.close()

    return render_template(
        "patient_notifications.html",
        notifications=notifications
    )

# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":

    app.run(debug=True)