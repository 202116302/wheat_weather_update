from django.shortcuts import render


def landing(request):
    return render(request, "landing/iksan.html")


def sample(request):
    return render(request, "landing/sample.html")
