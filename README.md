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
CREATE TABLE jobs(job_ID INT PRIMARY KEY,
job_title VARCHAR(100),
location VARCHAR(100),
descr TEXT,
requirements TEXT);
```

## This creates the database and now update the settings.py <br>

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'hireauth',
        'USER': 'root',                             # <--------------------- Add the user<br>
        'PASSWORD': 'password',                     # <--------------------- Add the password<br>
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
