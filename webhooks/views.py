from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def whatsapp_webhook(request):
    if request.method == "GET":
        return HttpResponse("webhook placeholder")
    return HttpResponse("ok")
