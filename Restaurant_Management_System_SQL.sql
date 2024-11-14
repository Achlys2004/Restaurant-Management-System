DROP TABLE IF EXISTS Order_Items;
DROP TABLE IF EXISTS Orders;
DROP TABLE IF EXISTS Payment;
DROP TABLE IF EXISTS Inventory;
DROP TABLE IF EXISTS Menu_Items;
DROP TABLE IF EXISTS Tables;
DROP TABLE IF EXISTS Reservation;
DROP TABLE IF EXISTS Customers;
DROP TABLE IF EXISTS Staff;

CREATE TABLE Staff (
    Staff_ID INT PRIMARY KEY AUTO_INCREMENT,
    Username VARCHAR(50) UNIQUE NOT NULL,
    Password VARCHAR(64) NOT NULL,
    Role ENUM('Manager', 'Waiter', 'Chef', 'Cashier') NOT NULL,
    Name VARCHAR(100),
    Email VARCHAR(100) UNIQUE,
    Phone VARCHAR(15),
    Active BOOLEAN DEFAULT TRUE
);

CREATE TABLE Customers (
    Cust_Id INT PRIMARY KEY AUTO_INCREMENT,
    Cust_Name VARCHAR(20) NOT NULL,
    PhoneNumber VARCHAR(15),
    Email VARCHAR(30)
);

CREATE TABLE Menu_Items (
    Item_Id INT PRIMARY KEY AUTO_INCREMENT,
    Item_Name CHAR(50) NOT NULL UNIQUE,
    Category CHAR(30) NOT NULL,
    Price DECIMAL(10,2) NOT NULL,
    Description TEXT,
    Available BOOLEAN DEFAULT TRUE,
    Created_At TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    Updated_At TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE Tables (
    Table_Id INT PRIMARY KEY AUTO_INCREMENT,
    Capacity INT NOT NULL,
    table_status ENUM('Available', 'Occupied', 'Reserved') NOT NULL,
    Current_Order_ID INT
);

CREATE TABLE Orders (
    Order_ID INT PRIMARY KEY AUTO_INCREMENT,
    Table_ID INT NOT NULL,
    Staff_ID INT NOT NULL,
    Order_Status ENUM('Pending', 'Ready', 'Completed', 'Cancelled') NOT NULL,
    Order_Time DATETIME NOT NULL,
    Completed_At DATETIME,
    Total_Amount DECIMAL(10,2)
);

CREATE TABLE Order_Items (
    Order_ID INT NOT NULL,
    Item_ID INT NOT NULL,
    Quantity INT NOT NULL,
    PRIMARY KEY (Order_ID, Item_ID),
    Created_At TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    Updated_At TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE Inventory (
    Inventory_Id INT PRIMARY KEY AUTO_INCREMENT,
    Item_Name VARCHAR(100) NOT NULL,
    Current_Stock INT NOT NULL,
    Reorder_Level INT NOT NULL,
    Unit VARCHAR(20),
    Created_At TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    Updated_At TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE Payment (
    Payment_Id INT PRIMARY KEY AUTO_INCREMENT,
    Order_Id INT NOT NULL,
    Customer_Id INT NOT NULL,
    Payment_Method CHAR(50),
    Payment_Status ENUM("Paid", "Yet to pay"),
    Total_Amount DECIMAL(10,2),
    Created_At TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    Updated_At TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE Reservation (
    Reserve_Id INT PRIMARY KEY AUTO_INCREMENT,
    Customer_Id INT NOT NULL,
    Table_Id INT NOT NULL,
    Date DATE,
    Time TIME,
    Status ENUM("Booked","Cancelled", "Available") NOT NULL,
    Party_Size INT,
    Reservation_DateTime DATETIME NOT NULL,
    Created_At TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    Updated_At TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

ALTER TABLE Tables
    ADD FOREIGN KEY (Current_Order_ID) REFERENCES Orders(Order_ID);

ALTER TABLE Orders
    ADD FOREIGN KEY (Table_ID) REFERENCES Tables(Table_Id),
    ADD FOREIGN KEY (Staff_ID) REFERENCES Staff(Staff_ID);

ALTER TABLE Order_Items
    ADD FOREIGN KEY (Order_ID) REFERENCES Orders(Order_ID),
    ADD FOREIGN KEY (Item_ID) REFERENCES Menu_Items(Item_Id);

ALTER TABLE Payment
    ADD FOREIGN KEY (Order_Id) REFERENCES Orders(Order_ID),
    ADD FOREIGN KEY (Customer_Id) REFERENCES Customers(Cust_Id);

ALTER TABLE Reservation
    ADD FOREIGN KEY (Customer_Id) REFERENCES Customers(Cust_Id),
    ADD FOREIGN KEY (Table_Id) REFERENCES Tables(Table_Id);

-- Trigger to update table status after reservation
DELIMITER //
CREATE TRIGGER after_reservation_insert_update
AFTER INSERT ON Reservation
FOR EACH ROW
BEGIN
    IF NEW.Status = 'Booked' THEN
        UPDATE Tables SET table_status = 'Occupied' WHERE Table_Id = NEW.Table_Id;
    ELSE
        UPDATE Tables SET table_status = 'Available' WHERE Table_Id = NEW.Table_Id;
    END IF;
END //
DELIMITER ;

-- Trigger to set table status to available after reservation deletion
DELIMITER //
CREATE TRIGGER after_reservation_delete
AFTER DELETE ON Reservation
FOR EACH ROW
BEGIN
    UPDATE Tables SET table_status = 'Available' WHERE Table_Id = OLD.Table_Id;
END //
DELIMITER ;

-- Trigger to reset current order in table when completed
DELIMITER //
CREATE TRIGGER reset_current_order
AFTER UPDATE ON Orders
FOR EACH ROW
BEGIN
    IF NEW.Order_Status IN ('Completed', 'Cancelled') THEN
        UPDATE Tables SET Current_Order_ID = NULL WHERE Table_Id = NEW.Table_ID;
    END IF;
END //
DELIMITER ;

-- First, drop existing triggers
-- Drop existing triggers
DROP TRIGGER IF EXISTS after_order_complete;
DROP TRIGGER IF EXISTS calculate_order_total;
-- Modified calculate_order_total trigger
DELIMITER //
CREATE TRIGGER calculate_order_total 
AFTER INSERT ON Order_Items
FOR EACH ROW
BEGIN
    DECLARE total_amount DECIMAL(10, 2);
    
    SELECT SUM(oi.Quantity * mi.Price) INTO total_amount
    FROM Order_Items oi
    JOIN Menu_Items mi ON oi.Item_ID = mi.Item_Id
    WHERE oi.Order_ID = NEW.Order_ID;
    
    UPDATE Orders 
    SET Total_Amount = total_amount 
    WHERE Order_ID = NEW.Order_ID;
END //
DELIMITER ;
-- Calculate total on order item update
DELIMITER //
CREATE TRIGGER calculate_order_total_on_update
AFTER UPDATE ON Order_Items
FOR EACH ROW
BEGIN
    DECLARE total_amount DECIMAL(10, 2);
    
    SELECT SUM(oi.Quantity * mi.Price) INTO total_amount
    FROM Order_Items oi
    JOIN Menu_Items mi ON oi.Item_ID = mi.Item_Id
    WHERE oi.Order_ID = NEW.Order_ID;
    
    UPDATE Orders 
    SET Total_Amount = total_amount 
    WHERE Order_ID = NEW.Order_ID;
END //

DELIMITER ;

-- Calculate total on order item delete
DELIMITER //

CREATE TRIGGER calculate_order_total_on_delete
AFTER DELETE ON Order_Items
FOR EACH ROW
BEGIN
    DECLARE total_amount DECIMAL(10, 2);
    
    SELECT SUM(oi.Quantity * mi.Price) INTO total_amount
    FROM Order_Items oi
    JOIN Menu_Items mi ON oi.Item_ID = mi.Item_Id
    WHERE oi.Order_ID = OLD.Order_ID;
    
    UPDATE Orders 
    SET Total_Amount = COALESCE(total_amount, 0)
    WHERE Order_ID = OLD.Order_ID;
END //

DELIMITER ;

-- Modified order completion trigger
DELIMITER //

CREATE TRIGGER after_order_complete
BEFORE UPDATE ON Orders
FOR EACH ROW
BEGIN
    IF NEW.Order_Status = 'Completed' AND OLD.Order_Status != 'Completed' THEN
        SET NEW.Completed_At = CURRENT_TIMESTAMP;
    END IF;
END //

DELIMITER ;

DELIMITER ;
-- Indices for performance
CREATE INDEX idx_staff_role ON Staff(Role);
CREATE INDEX idx_menu_category ON Menu_Items(Category);
CREATE INDEX idx_order_status ON Orders(Order_Status);
CREATE INDEX idx_order_date ON Orders(Order_Time);
CREATE INDEX idx_inventory_stock ON Inventory(Current_Stock);

-- Views for reporting
CREATE OR REPLACE VIEW daily_sales AS
SELECT 
    DATE(o.Order_Time) AS sale_date,
    COUNT(DISTINCT o.Order_ID) AS total_orders,
    SUM(o.Total_Amount) AS total_revenue,
    AVG(o.Total_Amount) AS average_order_value
FROM Orders o
WHERE o.Order_Status = 'Completed'
GROUP BY DATE(o.Order_Time);

CREATE OR REPLACE VIEW staff_performance AS
SELECT 
    s.Staff_ID,
    s.Username,
    s.Role,
    COUNT(o.Order_ID) AS orders_handled,
    SUM(o.Total_Amount) AS total_sales,
    AVG(o.Total_Amount) AS average_order_value
FROM Staff s
LEFT JOIN Orders o ON s.Staff_ID = o.Staff_ID
WHERE o.Order_Status = 'Completed'
GROUP BY s.Staff_ID;

CREATE OR REPLACE VIEW inventory_status AS
SELECT 
    i.*,
    CASE 
        WHEN i.Current_Stock <= i.Reorder_Level THEN 'Reorder Required'
        WHEN i.Current_Stock <= i.Reorder_Level * 1.5 THEN 'Low Stock'
        ELSE 'Adequate'
    END AS stock_status
FROM Inventory i;

-- Stored procedures
DELIMITER //

CREATE PROCEDURE update_menu_item(
    IN p_item_id INT,
    IN p_name CHAR(50),
    IN p_category CHAR(30),
    IN p_price DECIMAL(10,2),
    IN p_description TEXT,
    IN p_available BOOLEAN
)
BEGIN
    UPDATE Menu_Items
    SET Item_Name = p_name,
        Category = p_category,
        Price = p_price,
        Description = p_description,
        Available = p_available,
        Updated_At = CURRENT_TIMESTAMP
    WHERE Item_Id = p_item_id;
END //

CREATE PROCEDURE add_menu_item(
    IN p_name CHAR(50),
    IN p_category CHAR(30),
    IN p_price DECIMAL(10,2),
    IN p_description TEXT,
    IN p_available BOOLEAN
)
BEGIN
    INSERT INTO Menu_Items (
        Item_Name,
        Category,
        Price,
        Description,
        Available
    ) VALUES (
        p_name,
        p_category,
        p_price,
        p_description,
        p_available
    );
END //

CREATE PROCEDURE get_revenue_analysis(
    IN start_date DATE,
    IN end_date DATE
)
BEGIN
    SELECT 
        DATE(o.Order_Time) AS sale_date,
        mi.Category,
        COUNT(DISTINCT o.Order_ID) AS order_count,
        SUM(o.Total_Amount) AS revenue
    FROM Orders o
    JOIN Order_Items oi ON o.Order_ID = oi.Order_ID
    JOIN Menu_Items mi ON oi.Item_ID = mi.Item_Id
    WHERE DATE(o.Order_Time) BETWEEN start_date AND end_date
    AND o.Order_Status = 'Completed'
    GROUP BY DATE(o.Order_Time), mi.Category
    ORDER BY sale_date, mi.Category;
END //

CREATE PROCEDURE get_inventory_report(
    IN start_date DATE,
    IN end_date DATE
)
BEGIN
    SELECT 
        i.Item_Name,
        i.Current_Stock,
        i.Reorder_Level,
        i.Unit,
        COUNT(DISTINCT oi.Order_ID) AS times_ordered,
        COALESCE(SUM(oi.Quantity), 0) AS total_quantity_ordered
    FROM Inventory i
    LEFT JOIN Menu_Items mi ON i.Item_Name = mi.Item_Name
    LEFT JOIN Order_Items oi ON mi.Item_Id = oi.Item_ID
    LEFT JOIN Orders o ON oi.Order_ID = o.Order_ID
        AND DATE(o.Order_Time) BETWEEN start_date AND end_date
        AND o.Order_Status = 'Completed'
    GROUP BY i.Inventory_Id
    ORDER BY times_ordered DESC, i.Item_Name;
END //

DELIMITER ;

ALTER TABLE Reservation
MODIFY COLUMN Reservation_DateTime DATETIME DEFAULT CURRENT_TIMESTAMP;

