#  SPDX-FileCopyrightText: © 2024 Josef Hahn
#  SPDX-License-Identifier: AGPL-3.0-only
import base64
import contextlib
import json
import os
import subprocess
import sys
import time


def main(token: str) -> None:  # TODO dedup HALLYD_SUBPROCESS_SYS_PATH and similar stuff
    sys.path.clear()
    sys.path += json.loads(base64.b64decode(os.environ[f"HALLYD_SUBPROCESS_SYS_PATH_{token}"]).decode())

    import hallyd

    data = hallyd.bindle.loads(base64.b64decode(os.environ[f"HALLYD_SUBPROCESS_DATA_{token}"]).decode())

    action = data["ACTION"]
    svc_path = data["SVC_PATH"]
    interactive = data["INTERACTIVE"]
    once = data["ONCE"]

    with contextlib.ExitStack() as stack:
        if interactive:
            stack.enter_context(hallyd.lang.lock("/tmp/hallyd-boot-interactive-lock"))
            subprocess.call(["chvt", "2"])  # TODO also put output in a logfile?! at least via journalctl.

        reboot_afterwards = False
        if isinstance(action, hallyd.services.Runnable):
            try:
                action.run()
            except hallyd.services.Runnable._FinishAndReboot:
                reboot_afterwards = True
        else:
            raise ValueError(f"invalid task: {action}")

        if interactive:
            subprocess.call(["chvt", "1"])

        if once:
            hallyd.services.service(svc_path.name).disable()
            svc_path.unlink()

        if reboot_afterwards:
            subprocess.call(["reboot"])
            while True:
                time.sleep(1000)


if __name__ == "__main__":
    main(sys.argv[1])
