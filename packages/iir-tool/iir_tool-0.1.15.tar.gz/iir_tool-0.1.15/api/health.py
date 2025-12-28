from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_GET

from dictionary.models import Entry


@require_GET
def startup_health(_request):
    return HttpResponse("ok")


@require_GET
def live_health(_request):
    return HttpResponse("ok")


@require_GET
def ready_health(_request):
    try:
        Entry.objects.exists()
    except Exception:
        return JsonResponse({"status": "unavailable"}, status=503)
    return JsonResponse({"status": "ok"})
