function apply(button) {
    const jobId = button.getAttribute('data-job-id'); // Directly get the job ID from the button
    document.getElementById('job_id_field').value = jobId;
    document.getElementById('applicationModal').classList.remove('hidden');
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
