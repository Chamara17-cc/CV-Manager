-- CV Manager Database Setup
-- Run this script once to create the database and table
 
CREATE DATABASE IF NOT EXISTS cv_manager;
USE cv_manager;
 
CREATE TABLE IF NOT EXISTS candidates (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    full_name   VARCHAR(150)  NOT NULL,
    email       VARCHAR(150)  NOT NULL UNIQUE,
    phone       VARCHAR(30),
    role        VARCHAR(150)  NOT NULL,
    experience  VARCHAR(20),
    location    VARCHAR(150),
    skills      TEXT,
    status      VARCHAR(30)   DEFAULT 'Reviewing',
    notes       TEXT,
    created_at  DATETIME      DEFAULT CURRENT_TIMESTAMP
);
 
-- Sample data (optional — delete if not needed)
INSERT INTO candidates (full_name, email, phone, role, experience, location, skills, status, notes) VALUES
('Nimal Perera',   'nimal@email.com',   '+94771234567', 'Frontend Developer',  '3-5', 'Colombo',   'React, CSS, JavaScript',      'Reviewing', 'Strong portfolio, good communication.'),
('Sanduni Silva',  'sanduni@email.com', '+94712345678', 'Backend Developer',   '6+',  'Kandy',     'Python, Django, MySQL',        'Active',    'Senior level, available immediately.'),
('Kasun Fernando', 'kasun@email.com',   '+94723456789', 'UI/UX Designer',      '0-2', 'Galle',     'Figma, Adobe XD, Prototyping', 'Hired',     'Excellent design sense.');