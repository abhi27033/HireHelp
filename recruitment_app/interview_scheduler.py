from .mlmodel import mlscore
from django.db import connection
import requests, fitz, os, json
from datetime import datetime, timedelta

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

def schedule_interview(task_id,maal):
    print(f"Task {task_id} started.")
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
            print(f"Task {task_id} completed.")
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
        print(f"Task {task_id} completed.")
    except Exception as e:
        print(f"Error: {e}")
        print(f"Task {task_id} completed.")
    finally:
        cursor.close()