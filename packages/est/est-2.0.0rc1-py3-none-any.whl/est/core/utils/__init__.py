"""container for est.core utils functions"""

import logging

logger = logging.getLogger(__file__)


def extract_properties_from_dict(my_str) -> dict:
    """
    Convert parameters provided from a string to a dictionary.
    expected syntax is param1:value1,param2:value2
    would return { param1: value1, param2: value2 }
    try to cast each value to a number (float).
    """
    params = {}
    param_list = my_str.split(",")
    failures = []
    for param in param_list:
        try:
            param_name, param_value = param.split(":")
        except Exception as e:
            logger.info("Fail to cast some parameters: {}".format(e))
            failures.append(param)
        else:
            try:
                param_value = float(param_value)
            except Exception:
                pass
            params[param_name] = param_value
    if len(failures) > 0:
        logger.warning("Fail to convert some parameters : {}".format(failures))
    return params
