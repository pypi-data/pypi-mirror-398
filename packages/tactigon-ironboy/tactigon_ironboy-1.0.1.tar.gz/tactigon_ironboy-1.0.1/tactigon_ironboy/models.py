from dataclasses import dataclass
from enum import Enum
from datetime import datetime

class IronBoyCommand(Enum):
    ACK = -1
    STAND = 1
    WALK_FWD = 2
    TURN_LEFT = 3
    TURN_RIGHT = 4
    WALK_BACK = 5
    CELEBRATE = 6

    TIPTOE_FWD = 8
    TIPTOE_LEFT = 9
    TIPTOE_RIGHT = 10
    TIPTOE_BACK = 11

    BOW_DOWN_WAVE = 13

    PROVOKE = 15
    SIDE_PUNCH = 16
    CLAP = 17

    BODY_TILT = 19
    ARM_WAVE = 20
    FLYING_DOWN = 21

    GET_BALL = 23
    MOVE_BALL_FWD = 24
    DROP_BALL = 25
    SIDE_KICK_L = 27

    BOW_DOWN = 30
    WAVE = 31

    KPOP = 51
    

class IronBoyCommandStatus(Enum):
    NOT_SENT = 0
    SENT = 1
    ACK = 2

@dataclass
class IronBoyCommandMessage:
    command: IronBoyCommand
    _last_ack: datetime
    iterations: int = 1
    status: IronBoyCommandStatus = IronBoyCommandStatus.NOT_SENT
    timeout: float = 10
    _counter: int = 0

    @property
    def is_executing(self) -> bool:
        return self._counter < self.iterations
    
    @property
    def is_timeout(self) -> bool:
        _now = datetime.now()

        return (_now - self._last_ack).total_seconds() > self.timeout
    
    def resend(self):
        self.status = IronBoyCommandStatus.NOT_SENT
    
    def sent(self):
        self.status = IronBoyCommandStatus.SENT

    def ack(self):
        self.status = IronBoyCommandStatus.ACK
        self._last_ack = datetime.now()

    def done_one(self):
        self._counter += 1


@dataclass
class IronBoyConfig:
    name: str
    address: str

    @classmethod
    def FromJSON(cls, json: dict):
        return cls(
                json["name"],
                json["address"],
            )
        
    def toJSON(self) -> object:
        return {
            "name": self.name,
            "address": self.address
        }