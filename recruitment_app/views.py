from django.shortcuts import render, redirect
from django.db import connection
import bcrypt
from django.contrib import messages
from django.contrib.sessions.models import Session
from django.core.files.storage import FileSystemStorage
from django.contrib.auth import logout
import requests, fitz, os, json
from .mlmodel import mlscore
from datetime import datetime, timedelta

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


def parse_jobs():
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM jobs")
            jobs = list(cursor.fetchall())
        jobs_f=[]
        # print(type(jobs[0]))
        for job in jobs:
            jobs_dict = {
                'Job_ID': job[0],
                'Job_Title': job[1],
                'Job_Location': job[2],
                'Job_Description': job[3],
                'Job_Requirements': job[4][1:][:-1].split(',')
            }
            # print(jobs_dict['Job_Requirements'])
            jobs_f.append(jobs_dict)
    except:
        jobs_f=[]
    return jobs_f

def candidate(request):
    if not request.session.get('user_id') or request.session.get('user_role') != 'candidate':
        return redirect('/')
    candidate = {
        'firstname': request.session.get('firstname'),
        'lastname': request.session.get('lastname'),
        'mobile': request.session.get('mobile'),
        'email': request.session.get('email'),
    }
    
    return render(request, 'candidate.html', {'candidate': candidate,'fetched_jobs':parse_jobs})



def find_common_time_slot(availability_list, required_duration=1):
    """
    Find a common time slot of `required_duration` hours among all given availability schedules.
    """
    days_of_week = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

    for day in days_of_week:
        # Extract available times for each interviewer on this day
        times = []
        for availability in availability_list:
            if day in availability:
                start = int(availability[day]['start'].split(":")[0])
                end = int(availability[day]['end'].split(":")[0])
                times.append((start, end))

        # Check for overlapping time slots
        if len(times) > 0:
            # Find the maximum start time and minimum end time among all interviewers
            max_start = max([t[0] for t in times])
            min_end = min([t[1] for t in times])
            
            # Check if there is at least `required_duration` hours overlap
            if min_end - max_start >= required_duration:
                return day, max_start, max_start + required_duration

    return None, None, None


def schedule_interview(maal):
     # Unpack candidate details
    inserted_id, jid, firstname, lastname, mobile, email, experience_year, candidate_skills = maal
    cursor = connection.cursor()
    try:
        # Check if the interview is already scheduled for the given application
        cursor.execute("SELECT COUNT(*) FROM scheduled_interview WHERE cid = %s", (inserted_id,))
        exists = cursor.fetchone()[0]
        if exists:
            print("Interview already scheduled for this candidate!")
            return
        # Fetch job details from the jobs table using jid
        cursor.execute("SELECT job_title, descr FROM jobs WHERE job_ID = %s", (jid,))
        job_result = cursor.fetchone()
        job_title, descr = job_result
        # Step 1: Fetch all interviewers from the interviewers table
        cursor.execute("SELECT id, firstname, lastname, experience_years, skills, availability FROM interviewers")
        interviewers = cursor.fetchall()
        # Step 2: Filter interviewers by experience (at least twice the experience of the candidate)
        filtered_interviewers = []
        for interviewer in interviewers:
            interviewer_id, interviewer_firstname, interviewer_lastname, interviewer_experience, interviewer_skills_json, interviewer_availability_json = interviewer
            # Ensure interviewer_experience and experience_year are integers
            interviewer_experience = int(interviewer_experience)  # Cast to integer if it is a string
            experience_year = int(experience_year)  # Cast to integer if it is a string
            if interviewer_experience >= 2 * experience_year:
                interviewer_skills = json.loads(interviewer_skills_json)
                # Calculate skill matching score using mlscore function
                score = mlscore(candidate_skills, interviewer_skills)
                print(score)
                print(interviewer_firstname)
                filtered_interviewers.append((interviewer_id, interviewer_firstname, interviewer_lastname, score, interviewer_availability_json))
        print(filtered_interviewers)
        # Step 3: Sort interviewers by skill matching score in descending order and pick the top 3
        top_interviewers = sorted(filtered_interviewers, key=lambda x: x[3], reverse=True)[:min(len(filtered_interviewers),3)]
        # Step 4: Extract availability of top interviewers
        availability_list = [json.loads(top_interviewers[i][4]) for i in range(len(top_interviewers))]
        # Step 5: Find a common 1-hour time slot where all 3, 2, or at least 1 is available
        number=1
        for num_interviewers in [3, 2, 1]:
            num_interviewers_to_check = min(num_interviewers, len(availability_list))
            # Get the availability data for the top interviewers to check
            day, start_time, end_time = find_common_time_slot(availability_list[:num_interviewers_to_check])
            if day is not None:
                number=num_interviewers_to_check
                break
        print(number)
        if day is None:
            print("No Availability found of anyone")
            return
        
        # Step 6: Calculate the date of the chosen day in the current week
        current_date = datetime.now()
        weekday_mapping = {"monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
                           "friday": 4, "saturday": 5, "sunday": 6}
        target_weekday = weekday_mapping[day]
        # Calculate the date for the target weekday
        days_ahead = target_weekday - current_date.weekday()
        if days_ahead < 0:
            days_ahead += 7
        interview_date = current_date + timedelta(days=days_ahead)
        interview_date_str = interview_date.strftime('%Y-%m-%d')
        # Prepare the time slot
        time_slot = f"{start_time}:00 - {end_time}:00"

        # Step 7: Prepare data for the scheduled_interview table
        pmember2 = pmember3 = None
        candidate_name = f"{firstname} {lastname}"
        # Check if there are enough interviewers in the list
        pmember1 = top_interviewers[0][0] if min(number,len(top_interviewers)) > 0 else None
        pmember2 = top_interviewers[1][0] if min(number,len(top_interviewers)) > 1 else None
        pmember3 = top_interviewers[2][0] if min(number,len(top_interviewers)) > 2 else None
        # Prepare the panel string
        panel = ', '.join([f"{top_interviewers[i][1]} {top_interviewers[i][2]}" for i in range(len(top_interviewers[:number]))])
        tm = time_slot
        dt = interview_date_str
        
        # Insert the scheduled interview into the scheduled_interview table
        cursor.execute(
            "INSERT INTO scheduled_interview (cid, jid, job_title, candidate_name, pmember1, pmember2, pmember3, panel, descr, tm, dt) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", 
            (inserted_id, jid, job_title, candidate_name, pmember1, pmember2, pmember3, panel, descr, tm, dt)
        )
        print("Interview scheduled successfully!")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        cursor.close()
        

def submit_application(request):
    if request.method == 'POST':
        job_id = request.POST.get('job_id')
        firstname = request.POST.get('firstname')
        lastname = request.POST.get('lastname')
        mobile = request.POST.get('mobile')
        email = request.POST.get('email')
        experience_years = request.POST.get('experience_years')
        resume = request.FILES.get('resume')
        # Handling resume upload
        fs = FileSystemStorage(location='/tmp')  # Store in temp directory
        filename = fs.save(resume.name, resume)
        pdf_path = fs.path(filename)
        print(pdf_path)
        # Process resume using Emsi API
        url = "https://emsiservices.com/skills/versions/latest/extract"
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

        response = requests.request("POST", url, json=payload, headers=headers)
        skills = response.json().get('data', [])
        skills_json = []

        for skill in skills:
            skill_name = skill['skill']['name']
            skills_json.append(skill_name)

        # Convert list to JSON
        skills_json_object = json.dumps(skills_json)
        
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
            print(f"Temporary file {pdf_path} deleted.")
        inserted_id = -1
        try:
            with connection.cursor() as cursor:
                cursor.execute("INSERT INTO application (jid, firstname, lastname, mobile, email, experience_years, skills) VALUES (%s, %s, %s, %s, %s, %s, %s)",[job_id, firstname, lastname, mobile, email, experience_years, skills_json_object])
                cursor.execute("SELECT LAST_INSERT_ID()")
                inserted_id = cursor.fetchone()[0]
                cursor.close()
        except Exception as e:
            print(e)
            return render(request, 'candidate.html',  {'error': str(e)}) 
        
        # code to populate scheduled_interview
        schedule_interview([inserted_id, job_id, firstname, lastname, mobile, email, experience_years, skills_json])

        return render(request, 'candidate.html', {'candidate': candidate,'fetched_jobs':parse_jobs})

def interviewer(request):
    if not request.session.get('user_id') or request.session.get('user_role') != 'interviewer':
        return redirect('/')
    user_id = request.session.get('user_id')
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM jobs where Added_By= %s",[user_id])
            jobs = list(cursor.fetchall())
        jobs_f=[]
        # print(type(jobs[0]))
        for job in jobs:
            jobs_dict = {
                'Job_ID': job[0],
                'Job_Title': job[1],
                'Job_Location': job[2],
                'Job_Description': job[3],
                'Job_Requirements': job[4][1:][:-1].split(','),
                'Job_Status': job[6]
            }
            # print(jobs_dict['Job_Requirements'])
            jobs_f.append(jobs_dict)
            # print(jobs_f)
    except:
        jobs_f=[]
    return render(request, 'interviewer.html',{'fetched_jobs':jobs_f})

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

def addJob(request):
    job_ID = request.POST['job_ID']
    job_title = request.POST['job_title']
    location = request.POST['location']
    descr = request.POST['desc']
    requirements = request.POST.getlist('requirement')
    requirements_json = json.dumps(requirements)
    Added_By=request.session.get('user_id')
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM jobs WHERE job_ID=%s", ['job_ID'])
            exists = cursor.fetchone()[0]
            if exists:
                return render(request,'interviewer.html',{'error':"This Job ID already exists"})
            cursor.execute("INSERT INTO jobs VALUES (%s, %s, %s, %s, %s, %s,True)", [job_ID, job_title, location, descr, requirements_json,Added_By])
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
    # Handle form submission
    if request.method == "POST":
        # Get form data
        first_name = request.POST.get('firstname')
        last_name = request.POST.get('lastname')
        experience_years = request.POST.get('experience_years')
        email = request.POST.get('email')
        mobile = request.POST.get('phone')
        availability_json = request.POST.get('availability_json')
        education_json = request.POST.get('education_json')
        
        # Handling resume upload
        resume = request.FILES.get('resume')
        fs = FileSystemStorage(location='/tmp')  # Store in temp directory
        filename = fs.save(resume.name, resume)
        pdf_path = fs.path(filename)
        
        print(pdf_path)

        # Process resume using Emsi API
        url = "https://emsiservices.com/skills/versions/latest/extract"
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

        response = requests.request("POST", url, json=payload, headers=headers)
        skills = response.json().get('data', [])
        skills_json = []

        for skill in skills:
            skill_name = skill['skill']['name']
            skills_json.append(skill_name)

        # Convert list to JSON
        skills_json_object = json.dumps(skills_json)
        
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
            print(f"Temporary file {pdf_path} deleted.")
        
        try:
            with connection.cursor() as cursor:
                # Check if mobile number exists in the database
                cursor.execute("SELECT COUNT(*) FROM interviewers WHERE mobile=%s", [mobile])
                exists = cursor.fetchone()[0]
                
                if exists:
                    # Update existing entry
                    cursor.execute("UPDATE interviewers SET firstname=%s, lastname=%s, experience_years=%s, email=%s, skills=%s, education=%s, availability=%s, updated_at=NOW() WHERE mobile=%s", [first_name, last_name, experience_years, email, skills_json_object, education_json, availability_json, mobile])
                else:
                    # Insert new entry
                    cursor.execute("INSERT INTO interviewers (firstname, lastname, mobile, email, experience_years, skills, education, availability) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", [first_name, last_name, mobile, email, experience_years, skills_json_object, education_json, availability_json])
                cursor.close()
        except Exception as e:
            return render(request, 'interviewer.html', {'error': str(e)})
        
        return redirect('interviewer')
def scheduled_interview(request):
    if not request.session.get('user_id'):
        return redirect('/')
    elif(request.session.get('user_role')=='interviewer'):
        return render(request,'interviewer_scheduled_interview.html')
    else:
        return render(request,'candidate_scheduled_interview.html')
def add_job(request):
    if not request.session.get('user_id') or request.session.get('user_role') != 'interviewer':
        return redirect('/')
    return render(request,'Add_Jobs.html')
