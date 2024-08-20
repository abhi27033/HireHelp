from django.shortcuts import render
from django.http import HttpResponse

def abc(request):
    return render(request,'index.html')
    # return HttpResponse("Hello world!")
def rec(request):
    return HttpResponse("Welcome Recruiter")