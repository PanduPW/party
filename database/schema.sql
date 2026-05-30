CREATE DATABASE railway_system;
USE railway_system;

CREATE TABLE Train (
    train_id VARCHAR(10) PRIMARY KEY,
    train_name VARCHAR(50) NOT NULL,
    total_seats INT NOT NULL,
    train_type VARCHAR(30),
    ticket_price DECIMAL(10, 2) NOT NULL
);

CREATE TABLE Passenger (
    passenger_id VARCHAR(10) PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50),
    email VARCHAR(100) UNIQUE,
    phone_no VARCHAR(15)
);

CREATE TABLE Station (
    station_id VARCHAR(10) PRIMARY KEY,
    station_name VARCHAR(100) NOT NULL,
    city VARCHAR(50) NOT NULL,
    state_name VARCHAR(50)
);