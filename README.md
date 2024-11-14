# Restaurant Management System 🍽️

This project is a full-featured Restaurant Management System designed using Database Management System (DBMS) principles and Software Engineering practices. It includes a web interface built with Streamlit to interact seamlessly with the database for streamlined restaurant operations.

## Getting Started

Follow the steps below to set up and run this project on your local machine.

### Prerequisites

1. **Python**: Ensure Python is installed on your system.
2. **MySQL**: Install MySQL Server to create and manage the database.
3. **Streamlit**: Install Streamlit for the web-based interface.

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/Restaurant-Management-System.git
   cd Restaurant-Management-System
   ```

2. Install the required Python packages:

   ```
   pip install streamlit
   ```

3. *Set Up MySQL Database:*

   - Create a new schema named *restaurant_db*.
   - Update your database credentials (username, password, and database name) in the Python code to match your MySQL settings.
   - Execute the SQL script to set up the tables and populate any initial data:

     ```
     mysql -u your_username -p restaurant_db < restaurant_db.sql
     ```

     _Note_: Replace `your_username` with your actual MySQL username.

### Running the Project

1. Start the Streamlit app:

   ```
   streamlit run Restaurant_Management_System.py
   ```

2. Open your web browser and go to the address provided (typically `http://localhost:8501`).

### Features

- **Order Management**: Take, view, and update customer orders.
- **Menu Management**: Add, edit, or delete menu items.
- **Inventory Control**: Track ingredients and manage stock levels.
- **Billing and Invoicing**: Generate invoices based on orders.
- **User Roles**: Assign different permissions based on user roles (e.g., Admin, Chef, Waiter).

### Database Structure

The system uses a normalized relational database structure with the following main tables:

- *Customers*: Stores customer information.
- *Orders*: Records all customer orders.
- *Menu*: Manages the menu items.
- *Inventory*: Keeps track of ingredients and stock levels.
- *Users*: Manages user roles and access control.
