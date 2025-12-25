__version__ = "1.0.1"

import time
import asyncio
import struct
from bleak import BleakClient
from threading import Thread, Event
from datetime import datetime

from typing import Optional

from .models import IronBoyCommandMessage, IronBoyConfig, IronBoyCommand, IronBoyCommandStatus

class IronBoy(Thread):
    _TICK: float = 0.1
    CMD: str = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"
    STATUS: str = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"

    config: IronBoyConfig
    client: Optional[BleakClient]

    _stop_event: Event
    _current_command: Optional[IronBoyCommandMessage]
    _is_halt: bool
    _running: bool = False

    def __init__(self, config: IronBoyConfig):
        Thread.__init__(self, daemon=True)

        self.config = config
        self._stop_event = Event()
        self._current_command = None
        self._is_halt = False
        self.client = None

    def __enter__(self):
        self.send_command(IronBoyCommand.STAND)
        self.start()
        return self
    
    def __exit__(self, exception_type, exception_value, exception_traceback):
        while self.executing:
            time.sleep(self._TICK)
        self.stop()

    @property
    def connected(self) -> bool:
        return self.client.is_connected if self.client else False
    
    @property
    def running(self) -> bool:
        return self._running
    
    @property
    def executing(self) -> bool:
        return self._current_command is not None
    
    @staticmethod
    def get_cmd_string(command: IronBoyCommand):
        return f"G{command.value}|"

    @staticmethod
    def get_cmd_bytes(command: IronBoyCommand):
        return IronBoy.get_cmd_string(command).encode()

    def run(self):
        self._running = True
        self.loop = asyncio.new_event_loop()
        self.loop.run_until_complete(self.loop.create_task(self.main()))
        self._running = False

    def stop(self, timeout: float = 5):
        self._stop_event.set()
        self.join(timeout)

    def update(self, char, data: bytearray):
        code, = struct.unpack("b", data)
        if self._current_command:
            if IronBoyCommand(code) == self._current_command.command:
                self._current_command.ack()
            else:
                self._current_command.done_one()
                if self._current_command.is_executing:
                    self._current_command.resend()

    async def main(self):
        while not self._stop_event.is_set():
            self.client = BleakClient(self.config.address)
            try:
                await self.client.connect()
                await self.client.start_notify(IronBoy.STATUS, self.update)
            except Exception as e:
                pass

            while self.client.is_connected:
                if self._stop_event.is_set():
                    await self.client.disconnect()
                    return

                if self._current_command:
                    if self._current_command.is_timeout:
                        self._current_command = IronBoyCommandMessage(IronBoyCommand.STAND, datetime.now())
                        continue

                    if self._current_command.status == IronBoyCommandStatus.NOT_SENT:
                        command_bytes = self.get_cmd_bytes(self._current_command.command)
                        while command_bytes:
                            payload = command_bytes[:20]
                            command_bytes = command_bytes[20:]
                            await self.client.write_gatt_char(
                                self.CMD,
                                payload
                            )

                        self._current_command.sent()
                    elif self._current_command.status == IronBoyCommandStatus.ACK and not self._current_command.is_executing:
                        self._current_command = None  
                                     

                await asyncio.sleep(self._TICK)

            await asyncio.sleep(self._TICK)

        if self.client:
            await self.client.disconnect()
        
    def send_command(self, command: IronBoyCommand, iterations: int = 1) -> bool:
        if self._current_command:
            return False
        
        self._current_command = IronBoyCommandMessage(command, datetime.now(), iterations=iterations)
        return True

