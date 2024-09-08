# Steps to connect the authentication Database <br>
Run the below SQL commands in MySQL Workbench <br>

------------------------------------------------------------------------------------------------------

create database hireauth;<br>
use hireauth;<br>
CREATE TABLE user (<br>
    sid INT PRIMARY KEY AUTO_INCREMENT,<br>
    firstname VARCHAR(40) NOT NULL,<br>
    lastname VARCHAR(20) NOT NULL,<br>
    mobile VARCHAR(15) NOT NULL UNIQUE,<br>
    email VARCHAR(50) NOT NULL UNIQUE,<br>
    userrole ENUM('interviewer', 'candidate') NOT NULL DEFAULT 'candidate',<br>
    password_hash CHAR(60) NOT NULL<br>
);<br>

------------------------------------------------------------------------------------------------------

## This creates the database and now update the settings.py <br>

DATABASES = {<br>
    'default': {<br>
        'ENGINE': 'django.db.backends.mysql',<br>
        'NAME': 'hireauth',<br>
        'USER': 'root',                              <--------------------- Add the user<br>
        'PASSWORD': 'password',                      <--------------------- Add the password<br>
        'HOST': 'localhost',<br>
        'PORT': '3306',<br>
    }<br>
}<br>

## Now Run commands:<br>
------------------------------------------------------------------------------------------------------
py manage.py makemigrations<br>
py manage.py migrate<br>
py manage.py runserver<br>
