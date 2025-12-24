# File: ventaxiaiot/commands.py
import asyncio
import json
import logging
from enum import Enum

from ventaxiaiot.pending_request_tracker import PendingRequestTracker
from ventaxiaiot.sentinel_kinetic import SentinelKinetic

_LOGGER = logging.getLogger(__name__)



class VentClientCommands:
    VALID_TOPICS = {"ee", "wr"}
    
    def __init__(self, wifi_device_id, pendingRequestTracker : PendingRequestTracker):
        self._msg_id = 1
        self.device = SentinelKinetic()
        self.wifi_device_id = wifi_device_id
        self.tracker = pendingRequestTracker
        self._commissioning_task = None
        self._stop_event = asyncio.Event()
        _LOGGER.debug("VentClientCommands __init__ called")

    def _next_msg_id(self):
        val = self._msg_id
        self._msg_id += 1
        return val  
    
    def _validate_topic(self, topic: str) -> str:
        if topic not in self.VALID_TOPICS:
            raise ValueError(
                f"Invalid topic '{topic}'. Valid topics are: {sorted(self.VALID_TOPICS)}"
            )
        return topic

    async def send_subscribe(self, client):
        topics = [
            ("sub", "rd"),
            ("sub", "ee"),
            ("get", "rd"),
            ("pub", "wr", {"tsreq": 1}),
            ("get", "ee")           
        ] 

        for mtype, t_suffix, *extra in topics:
            msg = {"m": mtype, "i": self._next_msg_id()}
            if t_suffix:
                msg["t"] = f"{self.wifi_device_id}/{t_suffix}"
            if mtype == "pub":
                msg["d"] = extra[0]
                msg["f"] = 4           
            await client.send(json.dumps(msg))
            await asyncio.sleep(0.1)

    async def send_cfg_command(self, client, cmd: str):
        msg_id = self._next_msg_id()
        msg = {
            "m": "cfg",
            "cfgcmd": cmd,
            "i": msg_id
        }
        self.tracker.add(msg_id, {"cfgcmd": cmd})
        await client.send(json.dumps(msg))
        await asyncio.sleep(0.1)

    async def send_boost_request(self, client):
        msg = {
            "m": "pub",
            "t": f"{self.wifi_device_id}/wr",
            "d": {"ar_af": 3, "ar_min": 15},
            "f": 4,
            "i": self._next_msg_id(),
        }
        await client.send(json.dumps(msg))
        await asyncio.sleep(0.1)
        
    async def send_airflow_mode_request(self, client, mode: str, duration: int):
        if mode not in self.device.AIRFLOW_MODES:
            raise ValueError(f"Invalid mode: {mode}. Must be one of {list(self.device.AIRFLOW_MODES.keys())}")
        if duration not in self.device.VALID_DURATIONS:
            raise ValueError(f"Invalid duration: {duration}. Must be one of {sorted(self.device.VALID_DURATIONS)}")

        mode_code = self.device.AIRFLOW_MODES[mode]
        msg = {
            "m": "pub",
            "t": f"{self.wifi_device_id}/wr",
            "d": {
                "ar_af": mode_code,
                "ar_min": duration,
            },
            "f": 4,
            "i": self._next_msg_id(),
        }
        await client.send(json.dumps(msg))
        await asyncio.sleep(0.1)
        
    async def send_update_request(self, client,data: dict ,topic: str)-> None:
        topic = self._validate_topic(topic)
        
        msg = {
            "m": "pub",
            "t": f"{self.wifi_device_id}/{topic}",
            "d": data,
            "f": 4,
            "i": self._next_msg_id(),
        }
        await client.send(json.dumps(msg))
        await asyncio.sleep(0.1)
        
        
    async def _commissioning_loop(self, client, airflow: str = "normal"):
        """
        Internal loop to keep sending cm_af_run keep-alive
        airflow: 'normal' or 'boost'
        """
        # Define commissioning airflow values
        if airflow == "normal":
            cm_af = {"cm_af_sup": 250, "cm_af_exh": 425}
        elif airflow == "boost":
            cm_af = {"cm_af_sup": 500, "cm_af_exh": 850}
        else:
            raise ValueError("airflow must be 'normal' or 'boost'")

        # Initial setup: send cm_af_* to device once (can optionally write ee if desired)
        await self.send_update_request(client, cm_af, "ee")  # runtime only

        # Start commissioning
        await self.send_update_request(client, {"cm_af_run": 1}, "ee")

        # Clear stop event
        self._stop_event.clear()

        # Keep-alive loop
        while not self._stop_event.is_set():
            await self.send_update_request(client, {"cm_af_run": 1}, "ee")
            await asyncio.sleep(1.5)  # keep-alive interval (1–2s safe)

    def start_commissioning(self, client, airflow: str = "normal"):
        """
        Public method to start commissioning. 
        Returns immediately; commissioning loop runs in background.
        """
        if self._commissioning_task and not self._commissioning_task.done():
            raise RuntimeError("Commissioning already running")
        self._commissioning_task = asyncio.create_task(
            self._commissioning_loop(client, airflow)
        )

    async def stop_commissioning(self):
        """
        Stop the commissioning loop.
        """
        if self._commissioning_task:
            self._stop_event.set()
            await self._commissioning_task
            self._commissioning_task = None