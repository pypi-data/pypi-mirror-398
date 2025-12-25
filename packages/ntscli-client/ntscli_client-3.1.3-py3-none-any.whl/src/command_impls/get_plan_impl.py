import json

from src.clients.device_test_client import DeviceTestClient

indent = 4

def get_plan_impl(
    esn: str,
    plan_type: str,
    testcase_automation_filter: str,
    testcase_state_filter: str,
    testcase_name_filter: str,
    testcase_tag_filter: str,
    testcase_category_filter: str,
    playlist_id: str,
    dynamic_filter_id: str,
    sdk_or_apk: str,
    out_file,
    net_key: str,
    use_netflix_access: bool
):
    device_test_client = DeviceTestClient(net_key, use_netflix_access)

    match plan_type:
        case "FULL":
            plan = device_test_client.get_test_plan(esn, testcase_automation_filter, testcase_state_filter, testcase_name_filter, testcase_tag_filter, testcase_category_filter)
        case "PLAYLIST":
            plan = device_test_client.get_playlist_test_plan(playlist_id, esn)
        case "DYNAMIC_FILTER":
            plan = device_test_client.get_dynamic_filter_test_plan(dynamic_filter_id, esn, sdk_or_apk)
        case _:
            raise Exception(f"Attempting to get test plan by unsupported type: {plan_type}")

    # ensure test_overrides scaffold always exists for users to conveniently modify
    plan["test_overrides"] = plan.get("test_overrides", {})
    json.dump(plan, out_file, indent=indent)
