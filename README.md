# Steps to connect the authentication Database <br>

## Run the below SQL commands in MySQL Workbench <br>


```sql
create database hireauth;
use hireauth;
CREATE TABLE user (
    sid INT PRIMARY KEY AUTO_INCREMENT,
    firstname VARCHAR(40) NOT NULL,
    lastname VARCHAR(20) NOT NULL,
    mobile VARCHAR(15) NOT NULL UNIQUE,
    email VARCHAR(50) NOT NULL UNIQUE,
    userrole ENUM('interviewer', 'candidate') NOT NULL DEFAULT 'candidate',
    password_hash CHAR(60) NOT NULL
);
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
