function apply(buttonElement) {
    var grandpaDiv = buttonElement.parentElement.parentElement;
    childDivs=grandpaDiv.children;
    infoDiv=childDivs[0];
    formDiv=childDivs[1];
    infoDiv.classList.add('hidden');
    formDiv.classList.remove('hidden');
}

function applyJob(buttonElement) {
    var grandpaDiv = buttonElement.parentElement.parentElement.parentElement;
    childDivs=grandpaDiv.children;
    infoDiv=childDivs[0];
    formDiv=childDivs[1];
    infoDiv.classList.add('hidden');
    formDiv.classList.remove('hidden');
}