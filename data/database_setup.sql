CREATE DATABASE RobotServiceDB;

USE RobotServiceDB;

CREATE TABLE Customers (
    CustomerID INT PRIMARY KEY IDENTITY(1,1),
    Name NVARCHAR(100) NOT NULL,
    IsActive BIT NOT NULL DEFAULT 1
);


CREATE TABLE Robots (
    RobotID INT PRIMARY KEY IDENTITY(1,1),
    CustomerID INT FOREIGN KEY REFERENCES Customers(CustomerID),
    ModelName NVARCHAR(50),
    LoadCapacity FLOAT NOT NULL,
    Status NVARCHAR(20) CHECK (Status IN ('Operational', 'Error', 'Maintenance')),
    InstallDate DATE NOT NULL 
);


CREATE TABLE Parts (
    PartID INT PRIMARY KEY IDENTITY(1,1),
    PartName NVARCHAR(100),
    Price FLOAT NOT NULL,
    StockQuantity INT NOT NULL
);


CREATE TABLE ServiceLogs (
    LogID INT PRIMARY KEY IDENTITY(1,1),
    RobotID INT FOREIGN KEY REFERENCES Robots(RobotID),
    Description NVARCHAR(MAX),
    LogDate DATETIME DEFAULT GETDATE() 
);



CREATE TABLE ServiceLog_Parts (
    LogID INT FOREIGN KEY REFERENCES ServiceLogs(LogID),
    PartID INT FOREIGN KEY REFERENCES Parts(PartID),
    QuantityUsed INT NOT NULL,
    PRIMARY KEY (LogID, PartID)
);


GO
CREATE VIEW View_RobotOverview AS
SELECT r.ModelName, r.Status, c.Name AS OwnerName
FROM Robots r
JOIN Customers c ON r.CustomerID = c.CustomerID;


GO
CREATE VIEW View_ServiceCosts AS
SELECT 
    s.LogID, 
    r.ModelName,
    SUM(p.Price * slp.QuantityUsed) AS TotalCost
FROM ServiceLogs s
JOIN Robots r ON s.RobotID = r.RobotID
JOIN ServiceLog_Parts slp ON s.LogID = slp.LogID
JOIN Parts p ON slp.PartID = p.PartID
GROUP BY s.LogID, r.ModelName;
go


INSERT INTO Customers (Name, IsActive) VALUES
('Alpha Industries', 1),
('Beta Manufacturing', 1),
('Gamma Robotics', 1),
('Delta Logistics', 0),
('Epsilon Tech', 1);


INSERT INTO Robots (CustomerID, ModelName, LoadCapacity, Status, InstallDate) VALUES
(1, 'RX-100', 120.5, 'Operational', '2023-01-15'),
(1, 'RX-200', 200.0, 'Maintenance', '2022-11-01'),
(2, 'TX-50', 80.0, 'Operational', '2023-03-10'),
(3, 'GX-900', 300.0, 'Error', '2021-07-20'),
(4, 'LX-30', 60.0, 'Operational', '2024-02-05'),
(5, 'ZX-77', 150.0, 'Maintenance', '2022-09-18');


INSERT INTO Parts (PartName, Price, StockQuantity) VALUES
('Hydraulic Pump', 1250.50, 10),
('Control Unit', 3200.00, 5),
('Sensor Module', 450.75, 25),
('Servo Motor', 980.00, 15),
('Cooling Fan', 150.00, 40);


INSERT INTO ServiceLogs (RobotID, Description, LogDate) VALUES
(1, 'Regular annual maintenance', '2024-01-20'),
(2, 'Replacement of faulty control unit', '2024-02-11'),
(4, 'Error diagnostics and sensor replacement', '2024-03-05'),
(6, 'Cooling system overhaul', '2024-04-01');


INSERT INTO ServiceLog_Parts (LogID, PartID, QuantityUsed) VALUES
(1, 3, 2),
(2, 2, 1),
(3, 3, 1),
(3, 4, 2),
(4, 5, 3);
