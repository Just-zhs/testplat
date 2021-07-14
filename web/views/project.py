from django.shortcuts import render


def project_list(request):
    request.tracer.user
    request.tracer.price_policy
    return render(request,'project_list.html')