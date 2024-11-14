import streamlit as st
import mysql.connector
from datetime import datetime, timedelta
import hashlib
import re
from typing import Dict, List, Tuple, Optional

# Configuration and Constants
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "N3wDelhi",
    "database": "restaurant_db",
}


# Utility Functions
def get_database_connection():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except mysql.connector.Error as error:
        st.error(f"Database Connection Error: {error}")
        return None


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def validate_email(email):
    return bool(re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email))


# Authentication Functions
def check_staff_login(username, password, role):
    conn = get_database_connection()
    if not conn:
        return False, None

    try:
        cursor = conn.cursor(dictionary=True)
        hashed_password = hash_password(password)
        cursor.execute(
            "SELECT Staff_ID, Username, Role FROM Staff WHERE Username = %s AND Password = %s AND Role = %s",
            (username, hashed_password, role),
        )
        result = cursor.fetchone()
        return bool(result), result
    except mysql.connector.Error as error:
        st.error(f"Login Error: {error}")
        return False, None
    finally:
        conn.close()


def register_new_user(username, password, email):
    if not validate_email(email):
        st.error("Invalid email format")
        return
    conn = get_database_connection()
    if not conn:
        return
    try:
        cursor = conn.cursor()
        hashed_password = hash_password(password)
        cursor.execute(
            "INSERT INTO Customers (Cust_Name, Email) VALUES (%s, %s)",
            (username, email),
        )
        conn.commit()
        st.success("User registered successfully!")
    except mysql.connector.Error as error:
        st.error(f"Error: {error}")
    finally:
        conn.close()

# Manager portal
def get_active_tables_count():
    conn = get_database_connection()
    if not conn:
        return 0
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM Tables WHERE table_status = 'Occupied'")
        return cursor.fetchone()[0]
    except mysql.connector.Error as error:
        st.error(f"Error getting active tables: {error}")
        return 0
    finally:
        conn.close()

def get_open_orders_count():
    conn = get_database_connection()
    if not conn:
        return 0
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM Orders WHERE Order_Status != 'Completed'")
        return cursor.fetchone()[0]
    except mysql.connector.Error as error:
        st.error(f"Error getting open orders: {error}")
        return 0
    finally:
        conn.close()


# Staff Management Functions
def get_all_staff():
    conn = get_database_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Staff ORDER BY Role, Username")
        return cursor.fetchall()
    except mysql.connector.Error as error:
        st.error(f"Error fetching staff: {error}")
        return []
    finally:
        conn.close()

def update_staff_member(staff_id, username, role, active):
    conn = get_database_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE Staff 
            SET Username = %s, Role = %s, Active = %s 
            WHERE Staff_ID = %s
        """, (username, role, active, staff_id))
        conn.commit()
        return True
    except mysql.connector.Error as error:
        st.error(f"Error updating staff: {error}")
        return False
    finally:
        conn.close()

def add_staff_member(username, password, role):
    conn = get_database_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        hashed_password = hash_password(password)
        cursor.execute("""
            INSERT INTO Staff (Username, Password, Role, Active) 
            VALUES (%s, %s, %s, TRUE)
        """, (username, hashed_password, role))
        conn.commit()
        return True
    except mysql.connector.Error as error:
        st.error(f"Error adding staff: {error}")
        return False
    finally:
        conn.close()

# Report Functions
def get_sales_report(start_date, end_date):
    conn = get_database_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT 
                DATE(o.Order_Time) as Date,
                COUNT(DISTINCT o.Order_ID) as Total_Orders,
                SUM(oi.Price * oi.Quantity) as Revenue
            FROM Orders o
            JOIN Order_Items oi ON o.Order_ID = oi.Order_ID
            WHERE DATE(o.Order_Time) BETWEEN %s AND %s
            GROUP BY DATE(o.Order_Time)
            ORDER BY Date
        """, (start_date, end_date))
        return cursor.fetchall()
    except mysql.connector.Error as error:
        st.error(f"Error generating sales report: {error}")
        return None
    finally:
        conn.close()

def get_inventory_report(start_date, end_date):
    conn = get_database_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT 
                i.Item_Name,
                i.Current_Stock,
                i.Reorder_Level,
                COUNT(oi.Order_ID) as Times_Ordered
            FROM Inventory i
            LEFT JOIN Menu_Items mi ON i.Item_Name = mi.Item_Name
            LEFT JOIN Order_Items oi ON mi.Item_Id = oi.Item_ID
            LEFT JOIN Orders o ON oi.Order_ID = o.Order_ID
            AND DATE(o.Order_Time) BETWEEN %s AND %s
            GROUP BY i.Item_Name
            ORDER BY Times_Ordered DESC
        """, (start_date, end_date))
        return cursor.fetchall()
    except mysql.connector.Error as error:
        st.error(f"Error generating inventory report: {error}")
        return None
    finally:
        conn.close()

def get_staff_performance(start_date, end_date):
    conn = get_database_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT 
                s.Username,
                s.Role,
                COUNT(o.Order_ID) as Orders_Handled,
                SUM(oi.Price * oi.Quantity) as Total_Sales
            FROM Staff s
            LEFT JOIN Orders o ON s.Staff_ID = o.Staff_ID
            AND DATE(o.Order_Time) BETWEEN %s AND %s
            LEFT JOIN Order_Items oi ON o.Order_ID = oi.Order_ID
            GROUP BY s.Staff_ID
            ORDER BY Total_Sales DESC
        """, (start_date, end_date))
        return cursor.fetchall()
    except mysql.connector.Error as error:
        st.error(f"Error generating staff performance report: {error}")
        return None
    finally:
        conn.close()

def get_revenue_analysis(start_date, end_date):
    conn = get_database_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT 
                DATE(o.Order_Time) as Date,
                mi.Category,
                SUM(oi.Price * oi.Quantity) as Revenue
            FROM Orders o
            JOIN Order_Items oi ON o.Order_ID = oi.Order_ID
            JOIN Menu_Items mi ON oi.Item_ID = mi.Item_Id
            WHERE DATE(o.Order_Time) BETWEEN %s AND %s
            GROUP BY DATE(o.Order_Time), mi.Category
            ORDER BY Date, Category
        """, (start_date, end_date))
        return cursor.fetchall()
    except mysql.connector.Error as error:
        st.error(f"Error generating revenue analysis: {error}")
        return None
    finally:
        conn.close()
# Table Management Functions
def get_table_status():
    conn = get_database_connection()
    if not conn:
        return []

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT Table_Id, Capacity, table_status, Current_Order_ID 
            FROM Tables 
            ORDER BY Table_Id
        """
        )
        return cursor.fetchall()
    except mysql.connector.Error as error:
        st.error(f"Error fetching tables: {error}")
        return []
    finally:
        conn.close()


def update_table_status(table_id, status, order_id=None):
    conn = get_database_connection()
    if not conn:
        return False

    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE Tables 
            SET table_status = %s, Current_Order_ID = %s 
            WHERE Table_Id = %s
        """,
            (status, order_id, table_id),
        )
        conn.commit()
        return True
    except mysql.connector.Error as error:
        st.error(f"Error updating table: {error}")
        return False
    finally:
        conn.close()


# Menu Management Functions
def get_menu_items(category=None):
    conn = get_database_connection()
    if not conn:
        return []

    try:
        cursor = conn.cursor(dictionary=True)
        if category:
            cursor.execute(
                """
                SELECT * FROM Menu_Items 
                WHERE Category = %s
                ORDER BY Item_Name
            """,
                (category,),
            )
        else:
            cursor.execute(
                """
                SELECT * FROM Menu_Items
                ORDER BY Category, Item_Name
            """
            )
        return cursor.fetchall()
    except mysql.connector.Error as error:
        st.error(f"Error fetching menu: {error}")
        return []
    finally:
        conn.close()


def update_menu_item(item_id, name, price, category, description):
    conn = get_database_connection()
    if not conn:
        return False

    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE Menu_Items 
            SET Item_Name = %s, Price = %s, Category = %s, 
                Description = %s
            WHERE Item_Id = %s
        """,
            (name, price, category, description, item_id),
        )
        conn.commit()
        return True
    except mysql.connector.Error as error:
        st.error(f"Error updating menu item: {error}")
        return False
    finally:
        conn.close()

def add_menu_item(name, price, category, description):
    conn = get_database_connection()
    if not conn:
        return False

    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO Menu_Items (Item_Name, Price, Category, Description) 
            VALUES (%s, %s, %s, %s)
            """,
            (name, price, category, description)
        )
        conn.commit()
        return True
    except mysql.connector.Error as error:
        st.error(f"Error adding menu item: {error}")
        return False
    finally:
        conn.close()


# Order Management Functions
def create_order(table_id, item_name, quantity):
    # Logic to create the order
    try:
        conn = get_database_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO Orders (Table_ID, Order_Status, Order_Time)
                VALUES (%s, 'Pending', NOW())
                """,
                (table_id,)
            )
            order_id = cursor.lastrowid  # Get the last inserted Order_ID

            cursor.execute(
                    """
                    INSERT INTO Order_Items (Order_ID, Item_Name, Quantity)
                    VALUES (%s, %s, %s)
                    """,
                    (order_id, item_name, quantity)
                )

            conn.commit()
            return True, order_id
    except Exception as e:
        return False, str(e)

# Inventory Management Functions
def check_inventory_levels():
    conn = get_database_connection()
    if not conn:
        return []

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT * FROM Inventory 
            WHERE Current_Stock <= Reorder_Level
            ORDER BY Current_Stock/Reorder_Level
        """
        )
        return cursor.fetchall()
    except mysql.connector.Error as error:
        st.error(f"Error checking inventory: {error}")
        return []
    finally:
        conn.close()

def get_inventory_items():
    conn = get_database_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT * FROM Inventory
            """
        )
        return cursor.fetchall()
    except mysql.connector.Error as error:
        st.error(f"Error getting inventory: {error}")
        return []
    finally:
        conn.close()  # Close the connection properly here

def update_inventory_item(inventory_id, current_stock, reorder_level):
    conn = get_database_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            UPDATE Inventory
            SET Current_Stock = %s, Reorder_Level = %s
            WHERE Inventory_Id = %s
            """, (current_stock, reorder_level, inventory_id)
        )
        conn.commit()  # Ensure the update is committed
        return True
    except mysql.connector.Error as error:
        st.error(f"Error updating inventory: {error}")
        return False
    finally:
        conn.close()  # Close the connection properly here

def add_inventory_item(item_name, current_stock, reorder_level):
    conn = get_database_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            INSERT INTO Inventory (Item_Name, Current_Stock, Reorder_Level)
            VALUES (%s, %s, %s)
            """, (item_name, current_stock, reorder_level)
        )
        conn.commit()  # Ensure the insert is committed
        return True
    except mysql.connector.Error as error:
        st.error(f"Error adding inventory item: {error}")
        return False
    finally:
        conn.close()  # Close the connection properly here


# Reservation Management Functions
def create_reservation(
    customer_name, contact_number, table_id, reservation_datetime, party_size
):
    conn = get_database_connection()
    if not conn:
        return False, None

    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO Reservation (
                Customer_Id, 
                Table_Id, 
                Date, 
                Time, 
                Status,
                Party_Size
            ) VALUES ((SELECT Cust_Id FROM Customers WHERE Cust_Name = %s AND PhoneNumber = %s), %s, %s, 'Booked', %s)
            """,
            (
                customer_name,
                contact_number,
                table_id,
                reservation_datetime.date(),
                reservation_datetime.time(),
                party_size,
            ),
        )
        conn.commit()
        return True, cursor.lastrowid
    except mysql.connector.Error as error:
        st.error(f"Error: {error}")
        return False, None
    finally:
        conn.close()


def get_reservation(date_filter):
    conn = get_database_connection()
    if not conn:
        return []

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT r.Reserve_Id, c.Cust_Name AS Customer_Name, r.Table_Id, r.Date, r.Time, r.Status, r.Party_Size
            FROM Reservation r
            JOIN Customers c ON r.Customer_Id = c.Cust_Id
            WHERE r.Date = %s
            """,
            (date_filter,),
        )
        return cursor.fetchall()
    except mysql.connector.Error as error:
        st.error(f"Error fetching reservation: {error}")
        return []
    finally:
        conn.close()


def update_reservation_status(reservation_id, status):
    conn = get_database_connection()
    if not conn:
        return False

    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE Reservation 
            SET Status = %s 
            WHERE Reserve_Id = %s
        """,
            (status, reservation_id),
        )
        conn.commit()
        return True
    except mysql.connector.Error as error:
        st.error(f"Error updating reservation: {error}")
        return False
    finally:
        conn.close()


def check_table_availability(table_id, desired_datetime):
    conn = get_database_connection()
    if not conn:
        return False

    try:
        cursor = conn.cursor(dictionary=True)
        # Check 2 hours before and after the desired time
        start_time = desired_datetime - timedelta(hours=2)
        end_time = desired_datetime + timedelta(hours=2)

        cursor.execute(
            """
            SELECT COUNT(*) as conflict_count
            FROM Reservation
            WHERE Table_Id = %s
            AND Status = 'Booked'
            AND Date = %s
            AND Time BETWEEN %s AND %s
        """,
            (table_id, desired_datetime.date(), start_time.time(), end_time.time()),
        )

        result = cursor.fetchone()
        return result["conflict_count"] == 0
    except mysql.connector.Error as error:
        st.error(f"Error checking table availability: {error}")
        return False
    finally:
        conn.close()


# UI Components
def login_page():
    st.title("Restaurant Management System")

    with st.form("login_form"):
        username = st.text_input("Username")
        role = st.text_input("Role")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
        if submit:
            if username and role and password:
                st.session_state["logged_in"] = True
                st.session_state["user_data"] = {"Name": username, "Role": role}
                st.success(f"Welcome, {username}!")
                st.rerun()
            else:
                st.error("Please fill in all fields")
        


def reservation_management_ui():
    st.subheader("Reservation Management")

    tab1, tab2 = st.tabs(["View Reservation", "Create Reservation"])

    with tab1:
        # View and manage existing reservation
        date_filter = st.date_input("Select Date", datetime.now().date())
        reservation = get_reservation(date_filter)

        if reservation:
            for reservation in reservation:
                with st.expander(
                    f"{reservation['Customer_Name']} - Table {reservation['Table_Id']} - {reservation['Party_Size']} people"
                ):
                    st.write(f"Reservation ID: {reservation['Reserve_Id']}")
                    st.write(f"Date: {reservation['Date']}")
                    st.write(f"Time: {reservation['Time']}")
                    st.write(f"Status: {reservation['Status']}")
                    st.write(f"Party Size: {reservation['Party_Size']}")
        else:
            st.write("No reservation found for the selected date.")

    with tab2:
        # Create a new reservation
        st.subheader("Create a New Reservation")
        customer_name = st.text_input("Customer Name")
        contact_number = st.text_input("Contact Number")
        table_id = st.number_input("Table ID", min_value=1, step=1)
        reservation_date = st.date_input("Reservation Date", datetime.now().date())
        reservation_time = st.time_input("Reservation Time", datetime.now().time())
        party_size = st.number_input("Party Size", min_value=1, step=1)
        submit_button = st.button("Create Reservation")

        if submit_button:
            reservation_datetime = datetime.combine(reservation_date, reservation_time)
            # Debug statements to check parameter values
            st.write(f"Customer Name: {customer_name}")
            st.write(f"Contact Number: {contact_number}")
            st.write(f"Table ID: {table_id}")
            st.write(f"Reservation DateTime: {reservation_datetime}")
            st.write(f"Party Size: {party_size}")

            success, reservation_id = make_reservation(
                customer_name,
                contact_number,
                table_id,
                reservation_datetime,
                party_size,
            )
            if success:
                st.success(
                    f"Reservation created successfully! Reservation ID: {reservation_id}"
                )
            else:
                st.error("Failed to create reservation.")


def manager_portal():
    st.title("Restaurant Management Portal")

    menu = st.sidebar.selectbox(
        "Menu",
        [
            "Dashboard",
            "Menu Management",
            "Staff Management",
            "Inventory",
            "Reservation",
        ],
    )

    if menu == "Dashboard":
        show_dashboard()
    elif menu == "Menu Management":
        show_menu_management()
    elif menu == "Staff Management":
        show_staff_management()
    elif menu == "Inventory":
        show_inventory_management()
    elif menu == "Reservation":
        reservation_management_ui()

def show_dashboard():
    # Revenue metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        active_tables = get_active_tables_count()
        st.metric("Active Tables", f"{active_tables}/4")
    with col2:
        open_orders = get_open_orders_count()
        st.metric("Open Orders", str(open_orders))


    # Table Status
    st.subheader("Table Status")
    tables = get_table_status()
    st.dataframe(tables)

    # Low Inventory Alerts
    st.subheader("Low Inventory Alerts")
    low_inventory = check_inventory_levels()
    if low_inventory:
        st.warning(f"{len(low_inventory)} items need reordering")
        st.dataframe(low_inventory)

def show_menu_management():
    st.subheader("Menu Management")
    
    tab1, tab2 = st.tabs(["View/Edit Menu", "Add New Item"])
    
    with tab1:
        menu_items = get_menu_items()
        for item in menu_items:
            with st.expander(f"{item['Item_Name']} - ₹{item['Price']}"):
                with st.form(f"edit_item_{item['Item_Id']}"):
                    name = st.text_input("Name", item['Item_Name'])
                    price = st.number_input("Price", value=float(item['Price']), min_value=0.0)
                    category = st.selectbox(
                        "Category",
                        ["Appetizers", "Main Course", "Desserts", "Beverages"],
                        index=["Appetizers", "Main Course", "Desserts", "Beverages"].index(item['Category'])
                    )
                    description = st.text_area("Description", item['Description'])
                    
                    if st.form_submit_button("Update Item"):
                        if update_menu_item(item['Item_Id'], name, price, category, description):
                            st.success("Item updated successfully!")
                            st.rerun()
    
    with tab2:
        with st.form("add_new_item"):
            name = st.text_input("Name")
            price = st.number_input("Price", min_value=0.0)
            category = st.selectbox("Category", ["Appetizers", "Main Course", "Desserts", "Beverages"])
            description = st.text_area("Description")

            if st.form_submit_button("Add Item"):
                if add_menu_item(name, price, category, description):
                    st.success("New item added successfully!")
                    st.rerun()



def show_staff_management():
    st.subheader("Staff Management")
    
    tab1, tab2 = st.tabs(["View Staff", "Add New Staff"])
    
    with tab1:
        staff = get_all_staff()
        for employee in staff:
            with st.expander(f"{employee['Username']} - {employee['Role']}"):
                with st.form(f"edit_staff_{employee['Staff_ID']}"):
                    username = st.text_input("Username", employee['Username'])
                    role = st.selectbox(
                        "Role",
                        ["Manager", "Waiter", "Chef", "Cashier"],
                        index=["Manager", "Waiter", "Chef", "Cashier"].index(employee['Role'])
                    )
                    active = st.checkbox("Active", value=employee['Active'])
                    
                    if st.form_submit_button("Update Staff"):
                        if update_staff_member(employee['Staff_ID'], username, role, active):
                            st.success("Staff member updated successfully!")
                            st.rerun()
    
    with tab2:
        with st.form("add_new_staff"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            role = st.selectbox("Role", ["Manager", "Waiter", "Chef", "Cashier"])
            
            if st.form_submit_button("Add Staff"):
                if add_staff_member(username, password, role):
                    st.success("New staff member added successfully!")
                    st.rerun()

def show_inventory_management():
    st.subheader("Inventory Management")
    
    tab1, tab2 = st.tabs(["Current Inventory", "Add New Item"])
    
    with tab1:
        inventory = get_inventory_items()
        for item in inventory:
            # We no longer use Inventory_ID, so the form and dynamic naming can be simpler
            with st.expander(f"{item['Item_Name']} - Stock: {item['Current_Stock']}"):
                with st.form(f"edit_inventory_{item['Item_Name']}"):  # Use Item_Name for dynamic form name
                    quantity = st.number_input("Current Stock", value=item['Current_Stock'], min_value=0)
                    reorder_level = st.number_input("Reorder Level", value=item['Reorder_Level'], min_value=0)
                    
                    if st.form_submit_button("Update Stock"):
                        if update_inventory_item(item['Item_Name'], quantity, reorder_level):
                            st.success("Inventory updated successfully!")
                            st.rerun()
    
    with tab2:
        with st.form("add_inventory_item"):
            name = st.text_input("Item Name")
            quantity = st.number_input("Initial Stock", min_value=0)
            reorder_level = st.number_input("Reorder Level", min_value=0)
            
            if st.form_submit_button("Add Item"):
                if add_inventory_item(name, quantity, reorder_level):
                    st.success("New inventory item added successfully!")
                    st.rerun()


def waiter_portal():
    st.title("Waiter Portal")

    # Sidebar menu selection
    menu = st.sidebar.selectbox("Menu", ["Take Order", "View Orders", "Table Status"])

    # Handle "Take Order" functionality
    if menu == "Take Order":
        # Table selection (allow for both available and occupied tables)
        tables = get_table_status()
        selectable_tables = [t for t in tables if t["table_status"] in ["Available", "Occupied"]]
        
        if not selectable_tables:
            st.warning("No tables are available or occupied")
            return

        table = st.selectbox(
            "Select Table",
            selectable_tables,
            format_func=lambda x: f"Table {x['Table_Id']} - {x['table_status']}",
        )

        # Fetch menu items
        menu_items = get_menu_items()
        with st.form("order_form"):
            for item in menu_items:
                quantity = st.number_input(
                    f"{item['Item_Name']} (₹{item['Price']})", min_value=0, step=1, key=item['Item_Name']
                )
            submit = st.form_submit_button("Place Order")
            if submit:
                for item in menu_items:
                    quantity = st.session_state.get(item['Item_Name'], 0)
                    if quantity > 0:
                        success, order_id = create_order(table["Table_Id"], item["Item_Name"], quantity)
                        if success:
                            st.success(f"Order #{order_id} for {item['Item_Name']} placed successfully")
                        else:
                            st.error(f"Error placing order for {item['Item_Name']}: {order_id}")
                st.rerun()

    elif menu == "View Orders":
        conn = get_database_connection()
        if conn:
            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute(
                    """
                    SELECT o.Order_ID, o.Table_ID, o.Order_Time, o.Order_Status,
                           GROUP_CONCAT(CONCAT(mi.Item_Name, ' x', oi.Quantity)) as Items
                    FROM Orders o
                    JOIN Order_Items oi ON o.Order_ID = oi.Order_ID
                    JOIN Menu_Items mi ON oi.Item_ID = mi.Item_Id
                    WHERE o.Order_Status != 'Completed'
                    GROUP BY o.Order_ID
                    ORDER BY o.Order_Time
                """
                )
                orders = cursor.fetchall()

                if not orders:
                    st.info("No active orders")
                else:
                    for order in orders:
                        with st.expander(
                            f"Order #{order['Order_ID']} - Table {order['Table_ID']} - {order['Order_Status']}"
                        ):
                            st.write(f"Time: {order['Order_Time']}")
                            st.write(f"Items: {order['Items']}")
            except Exception as e:
                st.error(f"Error fetching orders: {e}")
            finally:
                conn.close()
    elif menu == "Table Status":
        tables = get_table_status()
        st.dataframe(tables)

def chef_portal():
    st.title("Kitchen Display System")

    # Active orders display
    st.header("Active Orders")
    conn = get_database_connection()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT o.Order_ID, o.Table_ID, o.Order_Time,
                       GROUP_CONCAT(CONCAT(mi.Item_Name, ' x', oi.Quantity)) as Items
                FROM Orders o
                JOIN Order_Items oi ON o.Order_ID = oi.Order_ID
                JOIN Menu_Items mi ON oi.Item_ID = mi.Item_Id
                WHERE o.Order_Status = 'Pending'
                GROUP BY o.Order_ID
                ORDER BY o.Order_Time
            """
            )
            orders = cursor.fetchall()

            if not orders:
                st.info("No pending orders")
                return

            for order in orders:
                with st.container():
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(
                            f"Order #{order['Order_ID']} - Table {order['Table_ID']}"
                        )
                        st.write(f"Time: {order['Order_Time']}")
                        st.write(f"Items: {order['Items']}")
                    with col2:
                        if st.button("Mark Ready", key=f"ready_{order['Order_ID']}"):
                            try:
                                cursor.execute(
                                    """
                                    UPDATE Orders 
                                    SET Order_Status = 'Ready' 
                                    WHERE Order_ID = %s
                                """,
                                    (order["Order_ID"],),
                                )
                                conn.commit()
                                st.success("Order marked as ready")
                                st.experimental_rerun()
                            except Exception as e:
                                st.error(f"Error updating order status: {e}")
        except Exception as e:
            st.error(f"Error fetching orders: {e}")
        finally:
            conn.close()

def cashier_portal():
    st.title("Cashier Portal")

    # Show active tables with orders
    tables = get_table_status()
    occupied_tables = [t for t in tables if t["table_status"] == "Occupied"]

    if occupied_tables:
        for table in occupied_tables:
            with st.expander(
                f"Table {table['Table_Id']} - Order #{table['Current_Order_ID']}"
            ):
                conn = get_database_connection()
                if conn:
                    try:
                        cursor = conn.cursor(dictionary=True)
                        # Get order details
                        cursor.execute(
                            """
                            SELECT 
                                mi.Item_Name,
                                mi.Price,
                                oi.Quantity,
                                (mi.Price * oi.Quantity) as Subtotal
                            FROM Order_Items oi
                            JOIN Menu_Items mi ON oi.Item_ID = mi.Item_Id
                            WHERE oi.Order_ID = %s
                        """,
                            (table["Current_Order_ID"],),
                        )
                        items = cursor.fetchall()

                        if not items:
                            st.warning("No items found for this order")
                            continue

                        # Display order items
                        total = 0
                        for item in items:
                            st.write(
                                f"{item['Item_Name']} x{item['Quantity']} = ₹{item['Subtotal']}"
                            )
                            total += item["Subtotal"]

                        st.write(f"**Total: ₹{total}**")

                        col1, col2 = st.columns(2)
                        payment_method = col1.selectbox(
                            "Payment Method",
                            ["Cash", "Card", "UPI"],
                            key=f"payment_{table['Current_Order_ID']}",
                        )

                        if col2.button(
                            "Process Payment", key=f"pay_{table['Current_Order_ID']}"
                        ):
                            try:
                                # Update order status
                                cursor.execute(
                                    """
                                    UPDATE Orders 
                                    SET Order_Status = 'Completed', 
                                        Payment_Status = 'Paid',
                                        Payment_Method = %s
                                    WHERE Order_ID = %s
                                """,
                                    (payment_method, table["Current_Order_ID"]),
                                )

                                # Update table status
                                cursor.execute(
                                    """
                                    UPDATE Tables 
                                    SET table_status = 'Available', Current_Order_ID = NULL
                                    WHERE Table_Id = %s
                                """,
                                    (table["Table_Id"],),
                                )

                                conn.commit()
                                st.success("Payment processed successfully")
                                st.experimental_rerun()
                            except Exception as e:
                                st.error(f"Error processing payment: {e}")
                    except Exception as e:
                        st.error(f"Error fetching order details: {e}")
                    finally:
                        conn.close()
    else:
        st.info("No active orders to process")


def create_order(
    table_id: int, staff_id: int, order_items: Dict[int, int]
) -> Tuple[bool, Optional[int]]:
    """
    Create a new order in the database.

    Args:
        table_id: The ID of the table
        staff_id: The ID of the staff member
        order_items: Dictionary mapping item IDs to quantities

    Returns:
        Tuple of (success: bool, order_id: Optional[int])
    """
    conn = get_database_connection()
    if not conn:
        return False, None

    try:
        cursor = conn.cursor()

        # Create order
        cursor.execute(
            """
            INSERT INTO Orders (Table_ID, Staff_ID, Order_Status, Payment_Status)
            VALUES (%s, %s, 'Pending', 'Pending')
        """,
            (table_id, staff_id),
        )

        order_id = cursor.lastrowid

        # Create order items
        for item_id, quantity in order_items.items():
            cursor.execute(
                """
                INSERT INTO Order_Items (Order_ID, Item_ID, Quantity)
                VALUES (%s, %s, %s)
            """,
                (order_id, item_id, quantity),
            )

        conn.commit()
        return True, order_id
    except Exception as e:
        st.error(f"Error creating order: {e}")
        return False, None
    finally:
        conn.close()


# Reservation Functions
def make_reservation(
    customer_name: str,
    contact_number: str,
    table_id: int,
    reservation_datetime: datetime,
    party_size: int,
):
    """
    Create a new reservation in the database.
    Returns tuple of (success: bool, reservation_id: Optional[int])
    """
    print(f"Attempting to make reservation for {customer_name} at table {table_id}")

    if not check_table_availability(table_id, reservation_datetime):
        print("Table is not available for the selected time")
        return False, None

    conn = get_database_connection()
    if not conn:
        print("Failed to establish database connection")
        return False, None

    try:
        cursor = conn.cursor()

        # First, check if the customer exists
        cursor.execute(
            "SELECT Cust_Id FROM Customers WHERE Cust_Name = %s AND PhoneNumber = %s",
            (customer_name, contact_number),
        )
        result = cursor.fetchone()

        if result:
            customer_id = result[0]
            print(f"Existing customer found with ID: {customer_id}")
        else:
            # Create new customer if doesn't exist
            cursor.execute(
                "INSERT INTO Customers (Cust_Name, PhoneNumber) VALUES (%s, %s)",
                (customer_name, contact_number),
            )
            conn.commit()
            customer_id = cursor.lastrowid
            print(f"New customer created with ID: {customer_id}")

        # Create the reservation
        cursor.execute(
            """
            INSERT INTO Reservation (
                Customer_Id, 
                Table_Id, 
                Date, 
                Time, 
                Status,
                Party_Size
            ) VALUES (%s, %s, %s, %s, 'Booked', %s)
            """,
            (
                customer_id,
                table_id,
                reservation_datetime.date(),
                reservation_datetime.time(),
                party_size,
            ),
        )
        reservation_id = cursor.lastrowid
        conn.commit()
        print(f"Reservation created successfully with ID: {reservation_id}")
        return True, reservation_id

    except mysql.connector.Error as error:
        print(f"Database error: {error}")
        if conn:
            conn.rollback()
        return False, None
    finally:
        if conn:
            conn.close()
        print("Database connection closed")


def cancel_reservation(reservation_id: int) -> bool:
    conn = get_database_connection()
    if not conn:
        return False

    try:
        cursor = conn.cursor(dictionary=True)  # Ensure cursor returns dictionaries

        # Get the Table_Id associated with the reservation
        cursor.execute(
            "SELECT Table_Id FROM Reservation WHERE Reserve_Id = %s",
            (reservation_id,),
        )
        result = cursor.fetchone()
        if not result:
            st.error("Reservation not found")
            return False

        table_id = result["Table_Id"]

        # Fetch all results before executing another query
        cursor.fetchall()

        # Delete the reservation
        cursor.execute(
            "DELETE FROM Reservation WHERE Reserve_Id = %s",
            (reservation_id,),
        )

        # Update the table status to 'Available'
        cursor.execute(
            "UPDATE Tables SET table_status = 'Available' WHERE Table_Id = %s",
            (table_id,),
        )

        conn.commit()
        return True
    except mysql.connector.Error as error:
        st.error(f"Error canceling reservation: {error}")
        return False
    finally:
        conn.close()


# Menu View-Only Function
def display_menu_view_only():
    conn = get_database_connection()
    if not conn:
        return
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM menu_items")
        menu_items = cursor.fetchall()
        for item in menu_items:
            st.write(f"{item['Item_Name']}: ${item['Price']}")
    finally:
        conn.close()


def check_database_connection():
    conn = get_database_connection()
    if conn:
        print("Database connection successful")
        conn.close()
    else:
        print("Failed to connect to the database")

def register_new_customer(name, phone_number, email):
    if not validate_email(email):
        st.error("Invalid email format")
        return
    conn = get_database_connection()
    if not conn:
        return
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO Customers (Cust_Name, PhoneNumber, Email) VALUES (%s, %s, %s)",
            (name, phone_number, email),
        )
        conn.commit()
        st.success("Customer registered successfully!")
    except mysql.connector.Error as error:
        st.error(f"Error: {error}")
    finally:
        conn.close()


def customer_registration_page():
    st.title("Customer Registration")

    with st.form("customer_registration_form"):
        name = st.text_input("Name")
        phone_number = st.text_input("Phone Number")
        email = st.text_input("Email")
        submit = st.form_submit_button("Register")

        if submit:
            if name and phone_number and email:
                register_new_customer(name, phone_number, email)
                st.session_state["logged_in"] = True
                st.session_state["user_data"] = {"Role": "Customer", "Name": name}
                st.success(f"Welcome, {name}!")
                st.rerun()
            else:
                st.error("Please fill in all fields")


def user_selection_page():
    st.title("Welcome to the Restaurant Management System")

    user_type = st.radio("Are you a staff member or a customer?", ["Staff", "Customer"])

    if user_type == "Customer":
        customer_registration_page()
    else:
        login_page()


def customer_dashboard():
    st.title("Customer Dashboard")

    # Sidebar for navigation
    st.sidebar.title("Reservation")
    reservation_menu = st.sidebar.selectbox(
        "Select Option",
        ["Make a Reservation", "View Reservations"],
        key="reservation_menu",
    )
    st.sidebar.title("Menu")
    menu_option = st.sidebar.button("View Menu", key="menu_option")

    if menu_option:
        st.subheader("Menu")
        display_menu_view_only()
    elif reservation_menu == "Make a Reservation":
        st.subheader("Make a Reservation")

        # Use a form to collect all reservation details
        with st.form("reservation_form"):
            customer_name = st.text_input("Your Name", placeholder="Enter your name")
            contact_number = st.text_input(
                "Contact Number", placeholder="Enter your phone number"
            )

            # Get available tables
            conn = get_database_connection()
            if conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT Table_Id, Capacity FROM Tables")
                tables = cursor.fetchall()
                conn.close()

                table_options = {
                    f"Table {t['Table_Id']} (Capacity: {t['Capacity']})": t["Table_Id"]
                    for t in tables
                }
                selected_table = st.selectbox(
                    "Select Table", options=list(table_options.keys())
                )
                table_id = table_options.get(selected_table)
            else:
                st.error("Unable to fetch table information")
                table_id = None

            party_size = st.number_input("Number of Guests", min_value=1, value=2)
            reservation_date = st.date_input(
                "Reservation Date",
                min_value=datetime.now().date(),
                value=datetime.now().date(),
            )
            reservation_time = st.time_input(
                "Reservation Time", value=datetime.now().time()
            )

            submit_button = st.form_submit_button("Make Reservation")

            if submit_button:
                if not all([customer_name, contact_number, table_id]):
                    st.error("Please fill in all required fields")
                else:
                    reservation_datetime = datetime.combine(
                        reservation_date, reservation_time
                    )
                    if reservation_datetime < datetime.now():
                        st.error("Cannot make reservations for past dates/times")
                    else:
                        success, reservation_id = make_reservation(
                            customer_name,
                            contact_number,
                            table_id,
                            reservation_datetime,
                            party_size,
                        )
                        if success:
                            st.success(
                                f"Reservation confirmed! Your reservation ID is: {reservation_id}"
                            )
                        else:
                            st.error(
                                "Unable to complete your reservation. Please try again."
                            )

    elif reservation_menu == "View Reservations":
        st.subheader("Your Reservations")
        if "user_data" in st.session_state and st.session_state["user_data"].get(
            "Name"
        ):
            customer_name = st.session_state["user_data"]["Name"]
            conn = get_database_connection()
            if conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute(
                    """
                    SELECT r.Reserve_Id, r.Date, r.Time, r.Party_Size, r.Status, t.Table_Id
                    FROM Reservation r
                    JOIN Customers c ON r.Customer_Id = c.Cust_Id
                    JOIN Tables t ON r.Table_Id = t.Table_Id
                    WHERE c.Cust_Name = %s AND r.Date >= CURDATE()
                    ORDER BY r.Date, r.Time
                """,
                    (customer_name,),
                )
                reservations = cursor.fetchall()
                conn.close()

                if reservations:
                    for res in reservations:
                        with st.expander(
                            f"Reservation on {res['Date']} at {res['Time']}"
                        ):
                            st.write(f"Table: {res['Table_Id']}")
                            st.write(f"Party Size: {res['Party_Size']}")
                            st.write(f"Status: {res['Status']}")

                            if st.button(
                                "Cancel Reservation", key=f"cancel_{res['Reserve_Id']}"
                            ):
                                if cancel_reservation(res["Reserve_Id"]):
                                    st.success("Reservation cancelled successfully")
                                    st.rerun()
                else:
                    st.info("You have no upcoming reservations")


# Modify the main function to start with the user selection page
def main():
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    if st.session_state["logged_in"]:
        # Add logout button in sidebar
        if st.sidebar.button("Logout"):
            st.session_state["logged_in"] = False
            st.session_state["user_data"] = None
            st.rerun()

        # Route to appropriate portal based on role
        if st.session_state["user_data"]["Role"] == "Manager":
            manager_portal()
        elif st.session_state["user_data"]["Role"] == "Waiter":
            waiter_portal()
        elif st.session_state["user_data"]["Role"] == "Chef":
            chef_portal()
        elif st.session_state["user_data"]["Role"] == "Cashier":
            cashier_portal()
        elif st.session_state["user_data"]["Role"] == "Customer":
            customer_dashboard()
    else:
        user_selection_page()


if __name__ == "__main__":
    main()
