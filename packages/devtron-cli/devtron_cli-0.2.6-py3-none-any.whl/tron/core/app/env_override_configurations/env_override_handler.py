import requests
import tron.util.exception_handlers as eh

@eh.handle_api_exceptions
def template_config_handler(base_url, headers, app_id, env_id, chart_ref_id):

    url = f"{base_url}/orchestrator/app/env/{app_id}/{env_id}/{chart_ref_id}"
    response = requests.get(url, headers=headers, timeout=10)

    response.raise_for_status()
    result = response.json().get("result", {})

    return {
        "success": True,
        "result": result
    }


@eh.handle_api_exceptions
def get_cm_cs_for_env(base_url, headers, app_id, env_id):
    url = f"{base_url}/orchestrator/config/autocomplete"
    params = {
        "appId": app_id,
        "envId": env_id
    }
    response = requests.get(url, headers=headers, params=params, timeout=10)
    response.raise_for_status()
    result = response.json().get("result", {})
    return {
        "success": True,
        "result": result
    }


@eh.handle_api_exceptions
def reset_config(base_url, headers, app_id, env_id, config_id, config_name, config_type, is_protected=False):
    import json
    if is_protected:
        url = f"{base_url}/orchestrator/draft"
        data = {
            "id": config_id
        }
        resourc = 0
        if config_type == "ConfigMap":
            resourc = 1
        elif config_type == "Secret":
            resourc = 2


        final_data = json.dumps(data, separators=(",", ":"), default=str, ensure_ascii=False)
        payload = {
            "appId": app_id,
            "envId": env_id,
            "resource": resourc,
            "resourceName": config_name,
            "action": 3,
            "data": final_data,
            "userComment":"",
            "changeProposed": True,
            "protectNotificationConfig": {
                "emailIds":[]
            }
        }

        response = requests.post(url, headers=headers, json=payload, timeout=10)

        response.raise_for_status()
        result = response.json().get("result", {})

        return {
            "success": True,
            "result": result
        }

    else:

        if config_type == "ConfigMap":
            url = f"{base_url}/orchestrator/config/environment/cm/{app_id}/{env_id}/{config_id}"
        elif config_type == "Secret":
            url = f"{base_url}/orchestrator/config/environment/cs/{app_id}/{env_id}/{config_id}"
        else:
            return {
                "success": False,
                "error": "Configtype not expected"
            }
        params = {
            "name": config_name,
            "isExpressEdit": False
        }
        response = requests.delete(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        result = response.json().get("result", {})
        return {
            "success": True,
            "result": result
        }


@eh.handle_api_exceptions
def template_patch_handler(base_url, headers, override_data, environment_name, env_id, chart_ref_id, app_metrics, id, merge_strategy, namespace):
    url = f"{base_url}/orchestrator/app/env"
    payload = {
        "environmentId": env_id,
        "chartRefId": chart_ref_id,
        "IsOverride": True,
        "isAppMetricsEnabled": app_metrics,
        "saveEligibleChanges": False,
        "namespace": namespace,
        "id": id,
        "status": 1,
        "manualReviewed": True,
        "active": True,
        "mergeStrategy": merge_strategy,
        "envOverrideValues": override_data,
        "isExpressEdit": False,
        "resourceName": f"{environment_name}-DeploymentTemplateOverride"
    }
    resource = requests.put(url, json=payload, headers=headers, timeout=10)
    resource.raise_for_status()
    result = resource.json().get("result", {})
    return {
        "success": True,
        "result": result
    }

@eh.handle_api_exceptions
def get_approval_data(base_url, headers, app_id):
    url  = f"{base_url}/orchestrator/protect/v2"
    params = {
        "appId": app_id
    }
    response = requests.get(url, headers=headers, params=params, timeout=10)
    response.raise_for_status()
    result = response.json().get("result", {})
    return {
        "success": True,
        "result": result
    }