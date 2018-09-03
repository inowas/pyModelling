def validate_spd(data):
    def convert_list_to_dict(spd_list):
        spd_dict = {}
        for stress_period, record in enumerate(spd_list):
            spd_dict[stress_period] = record
        return spd_dict

    # convert optimization objects' data
    try:
        for idx, _object in enumerate(data["optimization"]["objects"]):
            if type(_object["flux"]) == list:
                data["optimization"]["objects"][idx]["flux"] = convert_list_to_dict(_object["flux"])
            if type(_object["concentration"]) == list:
                data["optimization"]["objects"][idx]["concentration"] = convert_list_to_dict(_object["concentration"])
    except KeyError:
        pass

    # # convert modflow spd data
    # for package_name, package_data in data["data"]["mf"].items():
    #     try:
    #         if type(package_data["stress_period_data"]) == list:
    #             data["data"]["mf"][package_name]["stress_period_data"] \
    #                 = convert_list_to_dict(package_data["stress_period_data"])
    #     except KeyError:
    #         pass
    #
    # # convert mt3d spd data
    # for package_name, package_data in data["data"]["mt"].items():
    #     try:
    #         if type(package_data["stress_period_data"]) == list:
    #             data["data"]["mt"][package_name]["stress_period_data"] \
    #                 = convert_list_to_dict(package_data["stress_period_data"])
    #     except KeyError:
    #         pass

    return data
