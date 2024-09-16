from django.shortcuts import render, redirect
from django.db import connection
import bcrypt
from django.contrib import messages
from django.contrib.sessions.models import Session
from django.core.files.storage import FileSystemStorage
from django.contrib.auth import logout
import requests, fitz, os, json


def index(request):
    # Clear the session data
    request.session.flush()
    return render(request, 'index.html')

def login_view(request):
    if request.method == "POST":
        email = request.POST['email']
        password = request.POST['password']
        
        try:
            with connection.cursor() as cursor:
                # Reading more data so as to maintain in session
                cursor.execute("SELECT sid, password_hash, userrole, firstname, lastname, mobile, email FROM user WHERE email = %s", [email])
                user = cursor.fetchone()

                if user:
                    sid, stored_password_hash, userrole , firstname, lastname, mobile, email = user
                    if bcrypt.checkpw(password.encode('utf-8'), stored_password_hash.encode('utf-8')):
                        request.session['user_id'] = sid
                        request.session['user_role'] = userrole
                        request.session['firstname'] = firstname
                        request.session['lastname'] = lastname
                        request.session['mobile'] = mobile
                        request.session['email'] = email

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

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        try:
            with connection.cursor() as cursor:
                # Check if email or mobile already exists
                cursor.execute("SELECT COUNT(*) FROM user WHERE email = %s OR mobile = %s", [email, mobile])
                exists = cursor.fetchone()[0]

                if exists:
                    # If the user already exists, return an error message
                    return render(request, 'index.html', {'error': "Email or Mobile number already exists."})
                cursor.execute(
                    "INSERT INTO user (firstname, lastname, mobile, email, userrole, password_hash) VALUES (%s, %s, %s, %s, %s, %s)",
                    [firstname, lastname, mobile, email, userrole, hashed_password.decode('utf-8')]
                )
            return redirect('/')
        except Exception as e:
            return render(request, 'index.html',  {'error': str(e)}) 
    return redirect('/')        

def candidate(request):
    if not request.session.get('user_id') or request.session.get('user_role') != 'candidate':
        return redirect('/')
    candidate = {
        'firstname': request.session.get('firstname'),
        'lastname': request.session.get('lastname'),
        'mobile': request.session.get('mobile'),
        'email': request.session.get('email'),
    }
    return render(request, 'candidate.html', {'candidate': candidate})

def interviewer(request):
    if not request.session.get('user_id') or request.session.get('user_role') != 'interviewer':
        return redirect('/')
    return render(request, 'interviewer.html')

def logout_view(request):
    request.session.flush()  # Clear the session data
    return redirect('/')  # Redirect to homepage after logout


def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    return text

def apply(request):
    url = "https://emsiservices.com/skills/versions/latest/extract"
    if request.method=='POST':
        #extract
        firstname = request.POST['firstname']
        lastname = request.POST['lastname']
        mobile = request.POST['mobile']
        email = request.POST['email']
        resume = request.FILES['resume']


        fs = FileSystemStorage(location='/tmp')  # Store in temp directory
        filename = fs.save(resume.name, resume)
        pdf_path = fs.path(filename)
        
        print(pdf_path)

        #process
        querystring = {"language":"en"}
        auth_url = "https://auth.emsicloud.com/connect/token"
        payload = {
            "client_id": "39emm9hnhgnzvhfd",
            "client_secret": "1oW72wzJ",
            "grant_type": "client_credentials",
            "scope": "emsi_open"
        }

        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        response = requests.post(auth_url, data=payload, headers=headers)
        access_token=''

        if response.status_code == 200:
            response_data = response.json()
            access_token = response_data.get('access_token')
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        resume_text = extract_text_from_pdf(pdf_path).lower()
        payload = {
            "text": resume_text,
            "confidenceThreshold": 0.6
        }

        response = requests.request("POST", url, json=payload, headers=headers, params=querystring)
        skills = response.json().get('data',[])
        for skill in skills:
            print(skill['skill']['name'])
        
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
            print(f"Temporary file {pdf_path} deleted.")
    return redirect('candidate')

def addJob(request):
    job_ID = request.POST['job_ID']
    job_title = request.POST['job_title']
    location = request.POST['location']
    descr = request.POST['desc']
    requirements = request.POST.getlist('requirement')
    requirements_json = json.dumps(requirements)
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM jobs WHERE job_ID=%s", ['job_ID'])
            exists = cursor.fetchone()[0]
            if exists:
                return render(request,'interviewer.html',{'error':"This Job ID already exists"})
            cursor.execute("INSERT INTO jobs VALUES (%s, %s, %s, %s, %s)", [job_ID, job_title, location, descr, requirements_json])
            cursor.close()
    except Exception as e:
            return render(request, 'interviewer.html',  {'error': str(e)}) 
    return redirect('interviewer')
def interviewer_info(request):
    if not request.session.get('user_id') or request.session.get('user_role') != 'interviewer':
        return redirect('/')
    interviewer = {
        'firstname': request.session.get('firstname'),
        'lastname': request.session.get('lastname'),
        'mobile': request.session.get('mobile'),
        'email': request.session.get('email'),
    }
    return render(request,'interviewer_info.html',{'interviewer':interviewer})

def update_info(request):
    if request.method == 'POST':
        firstname = request.POST['firstname']
        lastname = request.POST['lastname']
        mobile = request.POST['phone']
        email = request.POST['email']
        experience_years = request.POST['experience_years']
        resume = request.FILES['resume']

        # Process resume to extract skills
        fs = FileSystemStorage(location='/tmp')  # Store in temp directory
        filename = fs.save(resume.name, resume)
        pdf_path = fs.path(filename)

        # API call to extract skills
        url = "https://emsiservices.com/skills/versions/latest/extract"
        querystring = {"language": "en"}
        auth_url = "https://auth.emsicloud.com/connect/token"
        payload = {
            "client_id": "39emm9hnhgnzvhfd",
            "client_secret": "1oW72wzJ",
            "grant_type": "client_credentials",
            "scope": "emsi_open"
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        response = requests.post(auth_url, data=payload, headers=headers)
        access_token = ''

        if response.status_code == 200:
            response_data = response.json()
            access_token = response_data.get('access_token')

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        resume_text = extract_text_from_pdf(pdf_path).lower()
        payload = {
            "text": resume_text,
            "confidenceThreshold": 0.8
        }

        response = requests.post(url, json=payload, headers=headers, params=querystring)
        skills = response.json().get('data', [])
        skills_list = [skill['skill']['name'] for skill in skills]
        skills_json = json.dumps(skills_list, indent=4)

        # Parse education and availability
        education = request.POST.getlist('qualification[]')
        degrees = request.POST.getlist('degree[]')
        specializations = request.POST.getlist('specialization[]')
        education_list = [
            {
                "qualification": q,
                "degree": d,
                "specialization": s
            }
            for q, d, s in zip(education, degrees, specializations)
        ]
        education_json = json.dumps(education_list, indent=4)

        availability = {}
        for day in ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']:
            if request.POST.get(f'availability[{day}][enabled]'):
                availability[day] = {
                    "start": request.POST.get(f'availability[{day}][start]'),
                    "end": request.POST.get(f'availability[{day}][end]')
                }
        availability_json = json.dumps(availability, indent=4)

        # Update database
        with connection.cursor() as cursor:
            try:
                cursor.execute("""
                    INSERT INTO interviewers (firstname, lastname, mobile, email, experience_years, skills, education, availability)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, [firstname, lastname, mobile, email, experience_years, skills_json, education_json, availability_json])
                print("Record inserted successfully")
            except IntegrityError as e:
                print(f"IntegrityError: {e}")
                # Handle specific errors such as duplicate email or phone number
                if 'Duplicate entry' in str(e):
                    return render(request, 'update_info.html', {'error': 'A record with this mobile number or email already exists.'})

        if os.path.exists(pdf_path):
            os.remove(pdf_path)
            print(f"Temporary file {pdf_path} deleted.")
    return redirect('interviewer')