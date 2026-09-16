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

        return {
            "boiler": {
                "outdoortemp": round(outside, 1),
                "curflowtemp": round(flow, 1),
                "returntemp": round(return_temp, 1),
                "dhwtemp": round(dhw, 1),
                "status": "heating" if compressor else "standby"
            },

            "heatpump": {
                "power": 1800 if compressor else 0,
                "cop": 4.2 if compressor else 0,
                "compressor": compressor,
                "status": "running" if compressor else "idle"
            }
        }