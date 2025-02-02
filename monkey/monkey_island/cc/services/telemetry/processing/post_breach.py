import copy

from common.common_consts.post_breach_consts import (
    POST_BREACH_COMMUNICATE_AS_BACKDOOR_USER,
    POST_BREACH_PROCESS_LIST_COLLECTION,
)
from monkey_island.cc.database import mongo
from monkey_island.cc.models import Monkey

EXECUTION_WITHOUT_OUTPUT = "(PBA execution produced no output)"


def process_communicate_as_backdoor_user_telemetry(telemetry_json, current_monkey):
    pass


def process_process_list_collection_telemetry(telemetry_json, current_monkey):
    pass


POST_BREACH_TELEMETRY_PROCESSING_FUNCS = {
    POST_BREACH_COMMUNICATE_AS_BACKDOOR_USER: process_communicate_as_backdoor_user_telemetry,
    POST_BREACH_PROCESS_LIST_COLLECTION: process_process_list_collection_telemetry,
}


def process_post_breach_telemetry(telemetry_json, _):
    def convert_telem_data_to_list(data):
        modified_data = [data]
        if type(data["result"][0]) is list:  # multiple results in one pba
            modified_data = separate_results_to_single_pba_telems(data)
        return modified_data

    def separate_results_to_single_pba_telems(data):
        modified_data = []
        for result in data["result"]:
            temp = copy.deepcopy(data)
            temp["result"] = result
            modified_data.append(temp)
        return modified_data

    def add_message_for_blank_outputs(data):
        if not data["result"][0]:
            data["result"][0] = EXECUTION_WITHOUT_OUTPUT
        return data

    post_breach_action_name = telemetry_json["data"]["name"]
    if post_breach_action_name in POST_BREACH_TELEMETRY_PROCESSING_FUNCS:
        current_monkey = Monkey.get_single_monkey_by_guid(telemetry_json["monkey_guid"])
        POST_BREACH_TELEMETRY_PROCESSING_FUNCS[post_breach_action_name](
            telemetry_json, current_monkey
        )

    telemetry_json["data"] = convert_telem_data_to_list(telemetry_json["data"])

    for pba_data in telemetry_json["data"]:
        pba_data = add_message_for_blank_outputs(pba_data)
        update_data(telemetry_json, pba_data)


def update_data(telemetry_json, data):
    mongo.db.monkey.update(
        {"guid": telemetry_json["monkey_guid"]}, {"$push": {"pba_results": data}}
    )
