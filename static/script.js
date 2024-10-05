const signUpButton = document.getElementById('signUp');
const signInButton = document.getElementById('signIn');
const container = document.getElementById('container');

signUpButton.addEventListener('click', () => {
	container.classList.add("right-panel-active");
});

signInButton.addEventListener('click', () => {
	container.classList.remove("right-panel-active");
});
function animate_text(){
	var txt = document.getElementById("animate-letter-typing1").innerHTML;
	document.getElementById("animate-letter-typing1").innerHTML = "";
	typeWriter(txt,"animate-letter-typing1");
	var txt = document.getElementById("animate-letter-typing2").innerHTML;
	document.getElementById("animate-letter-typing2").innerHTML = "";
	typeWriter(txt,"animate-letter-typing2");
}
function typeWriter(txt,class_name) {
	if (txt.length>0) {
	  document.getElementById(class_name).innerHTML += txt.charAt(0);
	  setTimeout(typeWriter, 100,txt.substr(1),class_name);
	}
}