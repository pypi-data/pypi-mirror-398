#  SPDX-FileCopyrightText: © 2023 Josef Hahn
#  SPDX-License-Identifier: AGPL-3.0-only
import importlib
import json
import os
import sys
import syslog
import traceback


def main():
    sys.path.clear()
    sys.path += json.loads(os.environ["HALLYD_SUBPROCESS_SYS_PATH"])

    import hallyd

    data = hallyd.bindle.loads(os.environ["HALLYD_SUBPROCESS_DATA"])

    call_module_name = data["MODULE_NAME"]
    call_function_name = data["FUNCTION_NAME"]
    call_args = data["ARGS"]
    call_kwargs = data["KWARGS"]

    func = eval(call_function_name, importlib.import_module(call_module_name).__dict__)
    func(*call_args, **call_kwargs)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        syslog.syslog(syslog.LOG_ERR, f"Internal error in Hallyd subprocess: {traceback.format_exc()}")
        sys.exit(1)
