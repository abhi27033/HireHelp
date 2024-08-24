from django.shortcuts import render, redirect
from django.db import connection
import bcrypt
from django.contrib import messages
from django.contrib.sessions.models import Session
from django.contrib.auth import logout
def index(request):
    request.session.flush()
    return render(request, 'index.html')

def login_view(request):
    if request.method == "POST":
        email = request.POST['email']
        password = request.POST['password']
        
        try:
            with connection.cursor() as cursor:
                # Write your SQL query to retrieve user data by email
                cursor.execute("SELECT sid, password_hash, userrole FROM user WHERE email = %s", [email])
                user = cursor.fetchone()

                if user:
                    sid, stored_password_hash, userrole = user
                    # Check if the hashed password matches
                    if bcrypt.checkpw(password.encode('utf-8'), stored_password_hash.encode('utf-8')):
                        # Password is correct, create a session manually
                        request.session['user_id'] = sid
                        request.session['user_role'] = userrole

                        # Redirect based on user role
                        if userrole == 'interviewer':
                            return redirect('interviewer')
                        else:
                            return redirect('candidate')
                    else:
                        return render(request, 'index.html',  {'error': "Invalid credentials"})
                else:
                    return render(request, 'index.html',  {'error': "No user found with this email"})
        except Exception as e:
           return render(request, 'index.html',  {'error': str(e)})
    return render(request, "index.html")

def register(request):
    if request.method == 'POST':
        firstname = request.POST['firstname']
        lastname = request.POST['lastname']
        mobile = request.POST['mobile']
        email = request.POST['email']
        password = request.POST['password']
        userrole = request.POST['userrole']  

        # Hash the password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO user (firstname, lastname, mobile, email, userrole, password_hash) VALUES (%s, %s, %s, %s, %s, %s)",
                    [firstname, lastname, mobile, email, userrole, hashed_password.decode('utf-8')]
                )
            return redirect('/') #check for successful registration
        except Exception as e:
            return render(request, 'index.html',  {'error': str(e)}) # write redundant query
    return render(request, 'index.html') 

def candidate(request):
    if not request.session.get('user_id') or request.session.get('user_role') != 'candidate':
        return redirect('/')  # Redirect if not logged in or not a candidate
    return render(request, 'candidate.html')

def interviewer(request):
    if not request.session.get('user_id') or request.session.get('user_role') != 'interviewer':
        return redirect('/')  # Redirect if not logged in or not an interviewer
    return render(request, 'interviewer.html')

def logout_view(request):
    request.session.flush()
    return redirect('/')