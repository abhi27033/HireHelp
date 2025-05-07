from django.shortcuts import render, redirect
from django.db import connection
import bcrypt
from django.contrib import messages
from django.contrib.sessions.models import Session
from django.core.files.storage import FileSystemStorage
from django.contrib.auth import logout
import requests, fitz, os, json
import urllib
import shutil
from django.http import JsonResponse
import time,threading
from .extract_textual_data import extract_data_from_txt
from .resume_parser import parse_resume, extract_text_from_pdf
from datetime import datetime, timedelta
import google.generativeai as genai
import re
from django.http import JsonResponse
from django.conf import settings
from .interview_scheduler import schedule_interview

API_KEY=settings.API_KEY

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
    user_id = request.session.get('user_id')
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
    # try:
    #     noti=[]
    #     with connection.cursor() as cursor:
    #         cursor.execute("SELECT id,message,created_at from notifications where user_id=%s AND is_read=FALSE",[user_id])
    #         noti_fetched = list(cursor.fetchall())
    #     for i in noti_fetched:
    #         noti_dict={
    #             'Notification_ID':i[0],
    #             'Message':i[1],
    #             'Date':i[2]
    #         }
    #         noti.append(noti_dict)
    #     print("Notifications ",noti)
    # except:
    #     noti = []
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
    # try:
    #     noti=[]
    #     with connection.cursor() as cursor:
    #         cursor.execute("SELECT id,message,created_at from notifications where user_id=%s AND is_read=FALSE",[user_id])
    #         noti_fetched = list(cursor.fetchall())
    #     for i in noti_fetched:
    #         noti_dict={
    #             'Notification_ID':i[0],
    #             'Message':i[1],
    #             'Date':i[2]
    #         }
    #         noti.append(noti_dict)
    #     print("Notifications ",noti)
    # except:
    #     print("Notifications ",noti)
    #     noti = []
    return render(request, 'interviewer.html',{'fetched_jobs':jobs_f})

def logout_view(request):
    request.session.flush()  # Clear the session data
    return redirect('/')  # Redirect to homepage after logout

def submit_application(request):
    if request.method == 'POST':
        user_id = request.session.get('user_id')
        job_id = request.POST.get('jobId')
        folder_name=f"{job_id}_{user_id}"
        # Define the base directory for saving files
        base_dir = os.path.join(os.getcwd(), 'temporary')
        folder_path = os.path.join(base_dir, folder_name)
        pdf_path = os.path.join(folder_path,'resume.pdf')
        data_path = os.path.join(folder_path,'data.txt')
        extracted_info=extract_data_from_txt(data_path)
        # Check if extraction was successful
        if 'error' in extracted_info:
            print("Error extracting data:", extracted_info['error'])
        else:
            firstname = extracted_info['firstname']
            lastname = extracted_info['lastname']
            mobile = extracted_info['mobile']
            email = extracted_info['email']
            experience_years = extracted_info['experience_years']
        # print(pdf_path)
        skills_json=parse_resume(pdf_path)
        # Convert list to JSON
        skills_json_object = json.dumps(skills_json)

        # if os.path.exists(folder_path):
        #     shutil.rmtree(folder_path)
        #     print(f"Temporary folder {folder_path} deleted.")
        inserted_id = -1
        try:
            with connection.cursor() as cursor:
                cursor.execute("INSERT INTO application (jid, firstname, lastname, mobile, email, experience_years, skills,user_id) VALUES (%s, %s, %s, %s, %s, %s, %s,%s)",[job_id, firstname, lastname, mobile, email, experience_years, skills_json_object,user_id])
                cursor.execute("SELECT LAST_INSERT_ID()")
                inserted_id = cursor.fetchone()[0]
                cursor.close()
        except Exception as e:
            print(e)
            return redirect('candidate') 
        task_id = datetime.now().strftime("%Y%m%d%H%M%S")
        # code to populate scheduled_interview
        thread = threading.Thread(target=schedule_interview,args=(task_id,[inserted_id, job_id, firstname, lastname, mobile, email, experience_years, skills_json,user_id]))
        thread.start()
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
            user_id = request.session.get('user_id')
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
            skills_json=parse_resume(pdf_path)
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
                        cursor.execute("INSERT INTO interviewers (firstname, lastname, mobile, email, experience_years, skills, education, availability,user_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)", [first_name, last_name, mobile, email, experience_years, skills_json_object, education_json, availability_json,user_id])
                    cursor.close()
            except Exception as e:
                print(e)
                return render(request, 'interviewer.html', {'error': str(e)})
        return redirect('interviewer')
    
def scheduled_interview_(request):
    if not request.session.get('user_id'):
        return redirect('/')
    user_id = request.session.get('user_id')
    user_role = request.session.get('user_role')
    fetched_interviews = []
    print('Here')
    try:
        with connection.cursor() as cursor:
            if user_role == 'interviewer':
                # Query for interviews assigned to the interviewer
                cursor.execute("SELECT id from interviewers where user_id=%s",[user_id])
                interviewer_id = cursor.fetchone()[0] 
                cursor.execute(
                    "SELECT cid, jid, job_title, candidate_name, panel, descr, tm, dt "
                    "FROM scheduled_interview WHERE pmember1 = %s OR pmember2 = %s OR pmember3 = %s "
                    "ORDER BY dt DESC",
                    [interviewer_id, interviewer_id, interviewer_id]
                )
            else:
                cursor.execute("SELECT id FROM application WHERE user_id=%s", [user_id])
                candidate_ids = cursor.fetchall()  # This will give a list of tuples [(id1,), (id2,), ...]

                # If you have candidate IDs, proceed with fetching the interviews
                if candidate_ids:
                    # Extract just the IDs from the fetched tuples
                    candidate_ids_list = [candidate_id[0] for candidate_id in candidate_ids]

                    # Query for interviews assigned to these candidate IDs
                    cursor.execute(
                        """
                        SELECT cid, jid, job_title, candidate_name, panel, descr, tm, dt
                        FROM scheduled_interview
                        WHERE cid IN %s
                        ORDER BY dt DESC
                        """, 
                        [tuple(candidate_ids_list)]  # Pass the list as a tuple for the IN query
                    )


            interviews = cursor.fetchall()
            for interview in interviews:
                interview_dict = {
                    'cid': interview[0],
                    'jid': interview[1],
                    'job_title': interview[2],
                    'candidate_name': interview[3],
                    'panel': interview[4],
                    'descr': interview[5],
                    'time': interview[6],
                    'date': interview[7],
                }
                fetched_interviews.append(interview_dict)

    except Exception as e:
        print("Error fetching scheduled interviews:", e)
        fetched_interviews = []
    print(fetched_interviews)
    # Render the appropriate template based on user role, passing fetched interviews
    if user_role == 'interviewer':
        return render(request, 'interviewer_scheduled_interview.html', {'fetched_interviews': fetched_interviews})
    else:
        return render(request, 'candidate_scheduled_interview.html', {'fetched_interviews': fetched_interviews})

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

def fetch_interview_details(request, cid, jid):
    print('ok')
    try:
        with connection.cursor() as cursor:
            # Fetch interview details using cid and jid
            cursor.execute("""
                SELECT 
                    cid, jid, job_title, candidate_name, pmember1, pmember2, pmember3, panel, 
                    descr, tm, dt 
                FROM scheduled_interview 
                WHERE cid = %s AND jid = %s
            """, [cid, jid])
            interview_details = cursor.fetchone()
            cursor.close()

            # Ensure that interview exists in the database
            if interview_details:
                interview_data = {
                    'cid': interview_details[0],
                    'jid': interview_details[1],
                    'job_title': interview_details[2],
                    'candidate_name': interview_details[3],
                    'pmember1': interview_details[4],
                    'pmember2': interview_details[5],
                    'pmember3': interview_details[6],
                    'panel': interview_details[7],
                    'descr': interview_details[8],
                    'tm': interview_details[9],
                    'dt': interview_details[10]
                }
            else:
                interview_data = {}

    except Exception as e:
        interview_data = {}
        print(f"Error: {e}")
    print(interview_data)
    return JsonResponse(interview_data)


# Configure Google GenAI
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

def generate_questions(request):
    # Only handle POST requests
    if request.method == 'POST':

        data = json.loads(request.body)
        job_title = data.get('jobTitle', '')
        job_description = data.get('jobDescription', '')
        job_requirements = data.get('jobRequirements', '')
        
        # If any required field is missing, return an error
        if not job_title or not job_description or not job_requirements:
            return JsonResponse({'error': 'Missing required fields'}, status=400)

        # Prepare the prompt for generating interview questions
        prompt = f"Generate 5 interview questions based on the following Job Title: {job_title}, Job Description: {job_description}, and Requirements: {job_requirements}. Write $ before start and end of questions and no need to number them."

        # Generate questions using Google GenAI
        response = model.generate_content(prompt)

        # Extract questions delimited by $
        questions = re.findall(r'\$(.*?)\$', response.text, re.DOTALL)
        questions = [q.strip() for q in questions]
        print(questions)
        # Return the questions as JSON response
        return JsonResponse({"questions": questions})

    return JsonResponse({'error': 'Invalid request method'}, status=405)


def evaluate_answers(request):
    if request.method == 'POST':
        # Get data from POST request
        data = json.loads(request.body)

        questions = data.get('questions')
        answers = data.get('answers')

        if not questions or not answers:
            return JsonResponse({'error': 'Missing required fields'}, status=400)

        # Parse JSON data
        questions = json.loads(questions)
        answers = json.loads(answers)
         
        print(questions)
        # Prepare the prompt for evaluation
        prompt = (
            f"Evaluate the following candidate answers for the given questions:\n\n"
            f"Questions and Answers:\n"
        )
        for i, (question, answer) in enumerate(zip(questions, answers), start=1):
            prompt += f"Q{i}: {question}\nA{i}: {answer}\n"

        prompt += "\nProvide a score out of 100 based on the relevance and quality of the answers. Write in format for example score: 80"

        # Call Gemini API for scoring
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)

        # Extract the score (assume the score is mentioned clearly in the response)
        score_match = re.search(r'\bscore\b.*?(\d{1,3})', response.text, re.IGNORECASE)
        score = int(score_match.group(1)) if score_match else None

        if score is not None:
            return JsonResponse({"score": score})
        else:
            return JsonResponse({'error': 'Unable to determine score'}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=405)


def resume_score(request):
    if request.method == 'POST':
        # Handling resume upload
        resume = request.FILES.get('resume')
        job_Id = request.POST.get('job_Id')
        exp = request.POST.get('exp')
        first_name = request.POST.get('firstname')
        last_name = request.POST.get('lastname')
        job_title = request.POST.get('job_title')
        job_description = request.POST.get('job_description')
        job_requirements = request.POST.get('job_requirements')
        user_Id = request.session.get('user_id')
        mobile =  request.session.get('mobile')
        email = request.session.get('email')
        if not job_title or not job_description or not job_requirements:
            return JsonResponse({'error': 'Missing required fields'}, status=400)

        # Define the base directory for saving files
        base_dir = os.path.join(os.getcwd(), 'temporary')
        os.makedirs(base_dir, exist_ok=True)  # Ensure 'temporary' folder exists

        # Create a unique folder for the job_Id and user_Id
        folder_name = f"{job_Id}_{user_Id}"
        folder_path = os.path.join(base_dir, folder_name)
        os.makedirs(folder_path, exist_ok=True)

        # Initialize FileSystemStorage with the target folder
        fs = FileSystemStorage(location=folder_path)
        # Save the resume as resume.pdf using fs.save()
        filename = fs.save('resume.pdf', resume)
        pdf_path = fs.path(filename)  # Get the full path of the saved file
        
        print(pdf_path)

        # Save the textual data into data.txt
        data_file_path = os.path.join(folder_path, 'data.txt')
        with open(data_file_path, 'w') as data_file:
            data_file.write(f"First Name: {first_name}\n")
            data_file.write(f"Last Name: {last_name}\n")
            data_file.write(f"Experience: {exp}\n")
            data_file.write(f"Job Title: {job_title}\n")
            data_file.write(f"Job Description: {job_description}\n")
            data_file.write(f"Job Requirements: {job_requirements}\n")
            data_file.write(f"Mobile: {mobile}\n")
            data_file.write(f"Email: {email}\n")

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
        print(skills_json)
        # Convert the skill list to a comma-separated string
        skills_string = ', '.join(skills_json)

        # Prepare the prompt for the Gemini API
        prompt = f"""
        A candidate has applied for the job titled '{job_title}'. 
        The job description is as follows: {job_description}. 
        The job requires the following skills: {job_requirements}. 

        The candidate's resume contains the following skills: {skills_string}.

        Based on the overlap and relevance of the candidate's skills with the job requirements and description, 
        provide a score for the candidate out of 100, where 100 indicates a perfect match. 

        Write the score as follows: "Score: <value>".
        """

        # Call the Gemini API
        response = model.generate_content(prompt)

        # Extract the score using regex
        import re
        score_match = re.search(r'\bscore\b.*?(\d{1,3})', response.text, re.IGNORECASE)
        score = int(score_match.group(1)) if score_match else None
        if score is not None:
            return JsonResponse({"score": score})
        else:
            return JsonResponse({'error': 'Unable to determine score'}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=405)