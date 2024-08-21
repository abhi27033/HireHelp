from django.shortcuts import render
from django.http import HttpResponse

def index(request):
    return render(request,'index.html');
def candidate(request):
    return render(request,'candidate.html')
def interviewer(request):
    return render(request,'interviewer.html')