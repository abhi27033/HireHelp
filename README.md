# Steps to connect the authentication and other relevant tables in Database<br>

## Run the below SQL commands in MySQL Workbench <br>


```sql
CREATE DATABASE hireauth;
USE hireauth;
CREATE TABLE user (
    sid INT PRIMARY KEY AUTO_INCREMENT,
    firstname VARCHAR(40) NOT NULL,
    lastname VARCHAR(20) NOT NULL,
    mobile VARCHAR(15) NOT NULL UNIQUE,
    email VARCHAR(50) NOT NULL UNIQUE,
    userrole ENUM('interviewer', 'candidate') NOT NULL DEFAULT 'candidate',
    password_hash CHAR(60) NOT NULL
);
CREATE TABLE jobs (
    job_ID INT PRIMARY KEY,
    job_title VARCHAR(100),
    location VARCHAR(100),
    descr TEXT,
    requirements TEXT,
    Added_By INT,
    FOREIGN KEY (Added_By) REFERENCES user(sid),
    status boolean
);

CREATE TABLE interviewers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    firstname VARCHAR(50) NOT NULL,
    lastname VARCHAR(50) NOT NULL,
    mobile VARCHAR(20) UNIQUE, -- Ensure mobile numbers are unique
    email VARCHAR(100) UNIQUE, -- Ensure email addresses are unique
    experience_years INT,
    skills JSON, -- JSON column for storing skills
    education JSON, -- JSON column for storing education details
    availability JSON, -- JSON column for storing availability details
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE candidates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    firstname VARCHAR(50) NOT NULL,
    lastname VARCHAR(50) NOT NULL,
    mobile VARCHAR(20) UNIQUE, -- Ensure mobile numbers are unique
    email VARCHAR(100) UNIQUE, -- Ensure email addresses are unique
    experience_years INT NOT NULL, -- Store experience in years
    skills JSON, -- JSON column for storing skills
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP -- Timestamp of creation
);
```

## This creates the database and now update the settings.py <br>

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'hireauth',
        'USER': 'root',                             # <--------------------- Add the user<br>
        'PASSWORD': 'aryan',                     # <--------------------- Add the password<br>
        'HOST': 'localhost',
        'PORT': '3306',
    }
}
```

## Now Run commands:

```python
py manage.py makemigrations
py manage.py migrate
py manage.py runserver
```