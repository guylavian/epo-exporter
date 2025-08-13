from typing import Optional, Dict, Any

from .client import call_onprem_api


def q(query_id: str, params: Optional[Dict[str, Any]] = None):
    payload: Dict[str, Any] = {"queryId": query_id}
    if params:
        payload.update(params)
    return call_onprem_api("core.executeQuery", payload)


def list_agent_handlers():
    return call_onprem_api("agentmgmt.listAgentHandlers")


def system_find(search_text: str = ""):
    return call_onprem_api("system.find", {"searchText": search_text})


def policy_find():
    return call_onprem_api("policy.find")


def system_list_tags():
    return call_onprem_api("system.listTags")


