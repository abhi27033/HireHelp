from django.shortcuts import render, redirect
from django.db import connection
import bcrypt
from django.contrib import messages
from django.contrib.sessions.models import Session
from django.core.files.storage import FileSystemStorage
from django.contrib.auth import logout
import requests, fitz, os, json
import urllib
from django.http import JsonResponse

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
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT job_ID,job_title,location,company_name,pay,date_of_posting,status FROM jobs where status=true order by date_of_posting desc")
            jobs = list(cursor.fetchall())
        jobs_f=[]
        # print(type(jobs[0]))
        for job in jobs:
            jobs_dict = {
                'Job_ID':job[0],
                'Job_Title':job[1],
                'Job_Location':job[2],
                'Company_Name':job[3],
                'Pay':job[4],
                'DateOfPosting': job[5],
                'Job_Status': job[6],
            }
            # print(jobs_dict['Job_Requirements'])
            jobs_f.append(jobs_dict)
    except:
        jobs_f=[]
    return render(request, 'candidate.html', {'candidate': candidate,'fetched_jobs':jobs_f})

def interviewer(request):
    if not request.session.get('user_id') or request.session.get('user_role') != 'interviewer':
        return redirect('/')
    user_id = request.session.get('user_id')
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT job_ID,job_title,location,company_name,pay,date_of_posting,status FROM jobs where Added_By= %s order by date_of_posting desc",[user_id])
            jobs = list(cursor.fetchall())
        jobs_f=[]
        # print(type(jobs[0]))
        for job in jobs:
            # jobs_dict = {
            #     'Job_ID': job[0],
            #     'Job_Title': job[1],
            #     'Job_Location': job[2],
            #     'Job_Description': job[3],
            #     'Job_Requirements': job[4][1:][:-1].split(','),
            #     'Job_Status': job[6],
            #     'Company_Name':job[7],
                
            # }
            # # Knowledge Graph API endpoint
            # service_url = 'https://kgsearch.googleapis.com/v1/entities:search'

            # # Parameters for the API request
            # params = {
            #     'query': job[2],
            #     'limit': 1,
            #     'indent': True,
            #     'key': 'Your API Key',
            #     'types':'Organization'
            # }

            # # Create the full URL for the API request
            # url = service_url + '?' + urllib.parse.urlencode(params)

            # # Make the API call and load the response
            # response = json.loads(urllib.request.urlopen(url).read())

            # # Iterate through the results
            # if response.get('itemListElement'):
            #     entity = response['itemListElement'][0]['result']
            #     entity_name = entity['name']
            #     entity_score = response['itemListElement'][0]['resultScore']
                
            #     # Check if the entity has a logo property
            #     logo_url = None
            #     if 'image' in entity and 'contentUrl' in entity['image']:
            #         logo_url = entity['image']['contentUrl']
            #     print("LOGO:", logo_url)
            jobs_dict = {
                'Job_ID':job[0],
                'Job_Title':job[1],
                'Job_Location':job[2],
                'Company_Name':job[3],
                'Pay':job[4],
                'DateOfPosting': job[5],
                'Job_Status': job[6],
            }
            # print(jobs_dict['Job_Requirements'])
            jobs_f.append(jobs_dict)
            # print(jobs_f)
    except Exception as e:
        jobs_f=[]
        # print(e)
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
            "confidenceThreshold": 0.8
        }

        response = requests.request("POST", url, json=payload, headers=headers, params=querystring)
        skills = response.json().get('data',[])
        # for skill in skills:
        #     print(skill['skill']['name'])
        
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
            # print(f"Temporary file {pdf_path} deleted.")
    return redirect('candidate')

def add_job(request):
    if not request.session.get('user_id') or request.session.get('user_role') != 'interviewer':
        return redirect('/')
    return render(request,'Add_Jobs.html')

def addJob(request):
    job_ID = request.POST['job_ID']
    job_title = request.POST['job_title']
    location = request.POST['location']
    descr = request.POST['desc']
    requirements = request.POST.getlist('requirement-item-added')
    requirements_json = json.dumps(requirements)
    Added_By=request.session.get('user_id')
    company_name = request.POST['company_name']
    pay = request.POST['pay']
    # print(company_name,pay)
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM jobs WHERE job_ID=%s", [job_ID])
            exists = cursor.fetchone()[0]
            if exists:
                print('IT exists yaarr')
                return render(request,'Add_Jobs.html',{'error':"This Job ID already exists"})
            cursor.execute("INSERT INTO jobs VALUES (%s, %s, %s, %s, %s,%s,%s,%s,CURRENT_DATE(),%s)", [job_ID, job_title, location, descr, requirements_json,Added_By,True,company_name,pay])
            cursor.close()
    except Exception as e:
            print("he hari naath ye kya hua")
            print(e)
            return render(request, 'Add_Jobs.html',  {'error': str(e)}) 
    return redirect('add_job')
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
                # print(f"Temporary file {pdf_path} deleted.")
            
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
                print(e)
                return render(request, 'interviewer.html', {'error': str(e)})
        return redirect('interviewer')
    
def scheduled_interview(request):
    if not request.session.get('user_id'):
        return redirect('/')
    elif(request.session.get('user_role')=='interviewer'):
        return render(request,'interviewer_scheduled_interview.html')
    else:
        return render(request,'candidate_scheduled_interview.html')
def get_job_details(request, job_id):
    # print(job_id)
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM jobs WHERE job_ID=%s", [job_id])
            job_details = list(cursor.fetchone())
            # print(job_details)
            cursor.close()
            job_data={
                'Job_ID': job_details[0],
                'Job_Title': job_details[1],
                'Job_Location': job_details[2],
                'Job_Description': job_details[3],
                'Job_Requirements': json.loads(job_details[4]),
                'Job_Status': job_details[6],
                'Company_Name':job_details[7],
            }
    except Exception as e:
        job_data={}
        print(e)
    return JsonResponse(job_data)
    
