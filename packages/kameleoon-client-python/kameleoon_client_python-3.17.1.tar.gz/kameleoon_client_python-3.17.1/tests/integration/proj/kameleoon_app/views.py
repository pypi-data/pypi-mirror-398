import json
import time
from http.cookies import SimpleCookie

from django.http import JsonResponse
from django.apps import apps

from kameleoon.data import CustomData, PageView
from kameleoon.exceptions import KameleoonError

kameleoon_app = apps.get_app_config("kameleoon_app")
client = kameleoon_app.kameleoon_client
local_ip = "127.0.0.1"


def variation_view(request):
    visitor_code = client.get_visitor_code(cookies_readonly=request.COOKIES, default_visitor_code=local_ip)
    experiment_id = 135471
    variation_id = None
    try:
        client.add_data(visitor_code, PageView("https://wer.com/", ""))
        variation_id = client.trigger_experiment(visitor_code, experiment_id)
    except NotAllocated:
        variation_id = None
    except NotTargeted:
        variation_id = None
    except ExperimentConfigurationNotFound:
        variation_id = None
    except KameleoonError as ex:
        print(ex)
    response = JsonResponse({"visitor_code": visitor_code, "variation": variation_id})
    return response


def simple_test_view(request):
    experiment_id = 777
    deviations = {"1": 0.5, "2": 0.25, "3": 0.25}
    experiment = {
        "id": experiment_id,
        "deviations": deviations,
        "respoolTime": {},
        "siteEnabled": True,
    }
    client._experiments.append(experiment)
    visitor_code = client.get_visitor_code(cookies_readonly=request.COOKIES, default_visitor_code=local_ip)

    variation_id = None
    try:
        variation_id = client.trigger_experiment(visitor_code, experiment_id)
    except NotAllocated:
        variation_id = 0
    except NotTargeted:
        variation_id = 0
    except ExperimentConfigurationNotFound:
        variation_id = 0
    except KameleoonError as ex:
        print(ex)

    return JsonResponse({"experiment": experiment_id, "variation": variation_id})


def activate_view(request):
    visitor_code = client.get_visitor_code(cookies_readonly=request.COOKIES, default_visitor_code=local_ip)
    feature_key = "test_key"
    is_activated = client.is_feature_active(visitor_code, feature_key)
    response = JsonResponse({"visitor_code": visitor_code, "activate": is_activated})
    return response


def add_data_view(request):
    visitor_code = client.get_visitor_code(cookies_readonly=request.COOKIES, default_visitor_code=local_ip)
    data = {}
    if "data" in request.GET:
        data = json.loads(request.GET.get("data"))
        for x in data:
            client.add_data(visitor_code, CustomData(*x))
    data = collect_visitor_data(visitor_code)
    response = JsonResponse({"data": data})
    return response


def flush_view(request):
    kameleoon_cookie = client.get_visitor_code(cookies_readonly=request.COOKIES, default_visitor_code=local_ip)
    client.flush()
    time.sleep(5.0)  # Delay due to possible multi-threading execution of `flush`
    data = collect_visitor_data(kameleoon_cookie)
    response = JsonResponse({"data": data})
    return response


def collect_visitor_data(visitor_code):
    visitor = client._visitor_manager.get_visitor(visitor_code)
    if visitor is None:
        return []
    return [sd.to_dict() for sd in visitor.enumerate_sendable_data()]
