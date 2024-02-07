from django.shortcuts import render

def landing_d(request):
    return render(request, "landing/buan_daeun.html")

def landing(request):
    return render(request, "landing/iksan.html")


def landing2(request):
    return render(request, "landing/iksan2.html")


def landing3(request):
    return render(request, "landing/buan.html")

def sample(request):
    return render(request, "landing/sample.html")
