import hashlib
import json

def create_enforcement_hash(request_json, created_on):
    data = {}
    data['commandTypeId'] = request_json['commandTypeId']
    data['controlGroupId'] = request_json['controlGroupId']
    data['controlSiteId'] = request_json['controlSiteId']
    data['numberOfImages'] = request_json['numberOfImages']
    data['startDatetime'] = request_json['startDatetime']
    data['stopDatetime'] = request_json['stopDatetime']
    data['speedLimit'] = request_json['speedLimit']
    data['photoLimit'] = request_json['photoLimit']
    data['heavyVehicleSpeedLimit'] = request_json['heavyVehicleSpeedLimit']
    data['heavyVehiclePhotoLimit'] = request_json['heavyVehiclePhotoLimit']
    data['testSeries'] = request_json['testSeries']
    data['comment'] = request_json['comment']
    data['commandCreatedBy'] = request_json['commandCreatedBy']
    data['commandCreatedOn'] = created_on
    json_to_hash = json.dumps(data, sort_keys = True).encode("utf-8")
    return hashlib.md5(json_to_hash).hexdigest()
