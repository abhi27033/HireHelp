function getCSRFToken() {
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
        const [name, value] = cookie.trim().split('=');
        if (name === 'csrftoken') {
            return value;
        }
    }
    return null;
}
async function apply(button) {
    const jobId = button.getAttribute('data-job-id'); 
    const jobTitle = button.getAttribute('data-job-title');
    const jobDescription = button.getAttribute('data-job-description');
    const jobRequirements = button.getAttribute('data-job-requirements');

    const payload = {
        jobTitle: jobTitle,
        jobDescription: jobDescription,
        jobRequirements: jobRequirements
    };

    console.log(payload);

    const csrfToken = getCSRFToken();
    const response = await fetch('generate_questions', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify(payload),
    });

    if (response.ok) {
        const questions = await response.json();
        console.log(questions);


        const jobProcess = document.getElementById('jobProcess');
        const jobDetails = document.getElementById('job-details');

        jobDetails.classList.add('hidden');
        jobProcess.classList.remove('hidden');

        // Calling populateQuiz and logging the result
        const score1 = await populateQuiz(questions);
        console.log('Score 1:', score1);
        const score2 = await populateResume(jobTitle,jobDescription,jobRequirements);
        console.log('Score 2:', score2);

    } else {
        console.error('Error:', response.statusText);
    }
}

// The function to populate the quiz and handle the form submission
async function populateQuiz(questions) {
    const quiz = document.getElementsByClassName('quiz')[0];
    let questionList = questions.questions;  // Assuming 'questions' is the object with your questions array
    
    quiz.innerHTML = `
        <div>
            <div class="w-full bg-white p-8 mt-5">
                <h1 class="text-2xl font-bold mb-6">Screening Questions</h1>
                <form id="questionForm" class="space-y-6" action='evaluate_answers' method="POST">
                    <div>
                        <label for="answer1" class="block text-lg font-medium text-gray-700">Question 1: ${questionList[0]}</label>
                        <textarea id="answer1" name="answer1" rows="4" class="mt-2 p-2 w-full border border-gray-300 rounded" required></textarea>
                    </div>
                    <div>
                        <label for="answer2" class="block text-lg font-medium text-gray-700">Question 2: ${questionList[1]}</label>
                        <textarea id="answer2" name="answer2" rows="4" class="mt-2 p-2 w-full border border-gray-300 rounded" required></textarea>
                    </div>
                    <div>
                        <label for="answer3" class="block text-lg font-medium text-gray-700">Question 3: ${questionList[2]}</label>
                        <textarea id="answer3" name="answer3" rows="4" class="mt-2 p-2 w-full border border-gray-300 rounded" required></textarea>
                    </div>
                    <div>
                        <label for="answer4" class="block text-lg font-medium text-gray-700">Question 4: ${questionList[3]}</label>
                        <textarea id="answer4" name="answer4" rows="4" class="mt-2 p-2 w-full border border-gray-300 rounded" required></textarea>
                    </div>
                    <div>
                        <label for="answer5" class="block text-lg font-medium text-gray-700">Question 5: ${questionList[4]}</label>
                        <textarea id="answer5" name="answer5" rows="4" class="mt-2 p-2 w-full border border-gray-300 rounded" required></textarea>
                    </div>
                    <div class="flex justify-end">
                        <button type="submit" class="bg-blue-500 text-white px-6 py-2 rounded hover:bg-blue-600">Submit Answers</button>
                    </div>
                </form>
            </div>
        </div>
    `;
    quiz.classList.remove('hidden');
    const form = document.getElementById('questionForm');

    return new Promise((resolve, reject) => {
        form.addEventListener('submit', function(event) {
            event.preventDefault();

            // Collect answers from the form fields
            const answers = [];
            for (let i = 1; i <= 5; i++) {
                const answer = document.getElementById(`answer${i}`).value;
                answers.push(answer);
            }

            // Send the collected answers to the server
            fetch('/evaluate_answers', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                },
                body: JSON.stringify({
                    questions: JSON.stringify(questions),
                    answers: JSON.stringify(answers)
                })
            })
            .then(response => response.json())  
            .then(data => {
                console.log('Success:', data);  // This should log {score: 0}
                resolve(data.score);  // Now resolve with the score
            })
            .catch((error) => {
                console.error('Error:', error);  // Handle errors if any
                reject(error);  // Reject the promise if there's an error
            });
        });
    });
}

async function populateResume(jobTitle, jobDescription, jobRequirements) {
    const quiz = document.getElementsByClassName('quiz')[0];
    const resume = document.getElementsByClassName('resume')[0];
    quiz.classList.add('hidden');
    resume.classList.remove('hidden');

    const form = document.getElementById('resumeForm');
    return new Promise((resolve, reject) => {
        form.addEventListener('submit', function (event) {
            event.preventDefault();

            const formData = new FormData();
            formData.append('resume', document.getElementById('resumeInput').files[0]); // Assuming the file input has id="resumeInput"
            formData.append('job_title', jobTitle);
            formData.append('job_description', jobDescription);
            formData.append('job_requirements', jobRequirements);

            // Send POST request to the server
            fetch('resume_score', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCSRFToken()
                },
                body: formData  // Use FormData to send files and data
            })
            .then(response => response.json())  // Assuming the server responds with JSON
            .then(data => {
                console.log('Success:', data);  // This should log {score: 0} or a similar response
                resolve(data.score);  // Resolve with the score received from the server
            })
            .catch((error) => {
                console.error('Error:', error);  // Handle errors if any
                reject(error);  // Reject the promise if there's an error
            });
        });
    });
}


function closeModal() {
    document.getElementById('applicationModal').classList.add('hidden');
}

function applyJob(buttonElement) {
    var grandpaDiv = buttonElement.parentElement.parentElement.parentElement;
    childDivs=grandpaDiv.children;
    infoDiv=childDivs[0];
    formDiv=childDivs[1];
    infoDiv.classList.add('hidden');
    formDiv.classList.remove('hidden');
}
function cancel(buttonElement) {
    var grandpaDiv = buttonElement.parentElement.parentElement.parentElement;
    childDivs=grandpaDiv.children;
    infoDiv=childDivs[0];
    formDiv=childDivs[1];
    infoDiv.classList.remove('hidden');
    formDiv.classList.add('hidden');
}
