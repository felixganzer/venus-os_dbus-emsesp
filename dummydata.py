# dummydata.py

import math
import time


class DummyHeatPump:

    def get_data(self):

        t = time.time()

        outside = 12 + math.sin(t / 300) * 5

        flow = 32 + math.sin(t / 60) * 2

        return_temp = flow - 4

        dhw = 48 + math.sin(t / 900)

        compressor = int((t % 600) < 450)

        flow_target = 31.5
        dhw_target = 49.0

        return {
            "boiler": {
                "outdoortemp": round(outside, 1),
                "curflowtemp": round(flow, 1),
                "returntemp": round(return_temp, 1),
                "selflowtemp": flow_target,
                "dhwtemp": round(dhw, 1),
                "wwseltemp": dhw_target,
                "status": "heating" if compressor else "standby",
                "dhw": {
                    "curtemp": round(dhw, 1),
                    "seltemp": dhw_target,
                    "charging": compressor
                }
            },

            "heatpump": {
                "power": 1800 if compressor else 0,
                "cop": 4.2 if compressor else 0,
                "compressor": compressor,
                "status": "running" if compressor else "idle",
                "auxheateractive": False,
                "auxheaterpower": 0.0,
                "hpactivity": "heating" if compressor else "standby",
            }
        }