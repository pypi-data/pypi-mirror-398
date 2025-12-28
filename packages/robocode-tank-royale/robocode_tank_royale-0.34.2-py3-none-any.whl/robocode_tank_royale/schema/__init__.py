"""
Auto-generated __init__.py for schema types.
"""

from typing import Any, Type

from .bot_address import BotAddress
from .bot_death_event import BotDeathEvent
from .bot_handshake import BotHandshake
from .bot_hit_bot_event import BotHitBotEvent
from .bot_hit_wall_event import BotHitWallEvent
from .bot_info import BotInfo
from .bot_intent import BotIntent
from .bot_list_update import BotListUpdate
from .bot_policy_update import BotPolicyUpdate
from .bot_ready import BotReady
from .bot_state_with_id import BotStateWithId
from .bot_state import BotState
from .bullet_fired_event import BulletFiredEvent
from .bullet_hit_bot_event import BulletHitBotEvent
from .bullet_hit_bullet_event import BulletHitBulletEvent
from .bullet_hit_wall_event import BulletHitWallEvent
from .bullet_state import BulletState
from .change_tps import ChangeTps
from .color import Color
from .controller_handshake import ControllerHandshake
from .event import Event
from .game_aborted_event import GameAbortedEvent
from .game_ended_event_for_bot import GameEndedEventForBot
from .game_ended_event_for_observer import GameEndedEventForObserver
from .game_paused_event_for_observer import GamePausedEventForObserver
from .game_resumed_event_for_observer import GameResumedEventForObserver
from .game_setup import GameSetup
from .game_started_event_for_bot import GameStartedEventForBot
from .game_started_event_for_observer import GameStartedEventForObserver
from .hit_by_bullet_event import HitByBulletEvent
from .initial_position import InitialPosition
from .message import Message
from .next_turn import NextTurn
from .observer_handshake import ObserverHandshake
from .participant import Participant
from .pause_game import PauseGame
from .results_for_bot import ResultsForBot
from .results_for_observer import ResultsForObserver
from .resume_game import ResumeGame
from .round_ended_event_for_bot import RoundEndedEventForBot
from .round_ended_event_for_observer import RoundEndedEventForObserver
from .round_started_event import RoundStartedEvent
from .scanned_bot_event import ScannedBotEvent
from .server_handshake import ServerHandshake
from .skipped_turn_event import SkippedTurnEvent
from .start_game import StartGame
from .stop_game import StopGame
from .team_message_event import TeamMessageEvent
from .team_message import TeamMessage
from .tick_event_for_bot import TickEventForBot
from .tick_event_for_observer import TickEventForObserver
from .tps_changed_event import TpsChangedEvent
from .won_round_event import WonRoundEvent

__all__ = [
    "BotAddress",
    "BotDeathEvent",
    "BotHandshake",
    "BotHitBotEvent",
    "BotHitWallEvent",
    "BotInfo",
    "BotIntent",
    "BotListUpdate",
    "BotPolicyUpdate",
    "BotReady",
    "BotStateWithId",
    "BotState",
    "BulletFiredEvent",
    "BulletHitBotEvent",
    "BulletHitBulletEvent",
    "BulletHitWallEvent",
    "BulletState",
    "ChangeTps",
    "Color",
    "ControllerHandshake",
    "Event",
    "GameAbortedEvent",
    "GameEndedEventForBot",
    "GameEndedEventForObserver",
    "GamePausedEventForObserver",
    "GameResumedEventForObserver",
    "GameSetup",
    "GameStartedEventForBot",
    "GameStartedEventForObserver",
    "HitByBulletEvent",
    "InitialPosition",
    "Message",
    "NextTurn",
    "ObserverHandshake",
    "Participant",
    "PauseGame",
    "ResultsForBot",
    "ResultsForObserver",
    "ResumeGame",
    "RoundEndedEventForBot",
    "RoundEndedEventForObserver",
    "RoundStartedEvent",
    "ScannedBotEvent",
    "ServerHandshake",
    "SkippedTurnEvent",
    "StartGame",
    "StopGame",
    "TeamMessageEvent",
    "TeamMessage",
    "TickEventForBot",
    "TickEventForObserver",
    "TpsChangedEvent",
    "WonRoundEvent"
]

CLASS_MAP: dict[str, Type[Any]] = {
    "BotAddress": BotAddress,
    "BotDeathEvent": BotDeathEvent,
    "BotHandshake": BotHandshake,
    "BotHitBotEvent": BotHitBotEvent,
    "BotHitWallEvent": BotHitWallEvent,
    "BotInfo": BotInfo,
    "BotIntent": BotIntent,
    "BotListUpdate": BotListUpdate,
    "BotPolicyUpdate": BotPolicyUpdate,
    "BotReady": BotReady,
    "BotStateWithId": BotStateWithId,
    "BotState": BotState,
    "BulletFiredEvent": BulletFiredEvent,
    "BulletHitBotEvent": BulletHitBotEvent,
    "BulletHitBulletEvent": BulletHitBulletEvent,
    "BulletHitWallEvent": BulletHitWallEvent,
    "BulletState": BulletState,
    "ChangeTps": ChangeTps,
    "Color": Color,
    "ControllerHandshake": ControllerHandshake,
    "Event": Event,
    "GameAbortedEvent": GameAbortedEvent,
    "GameEndedEventForBot": GameEndedEventForBot,
    "GameEndedEventForObserver": GameEndedEventForObserver,
    "GamePausedEventForObserver": GamePausedEventForObserver,
    "GameResumedEventForObserver": GameResumedEventForObserver,
    "GameSetup": GameSetup,
    "GameStartedEventForBot": GameStartedEventForBot,
    "GameStartedEventForObserver": GameStartedEventForObserver,
    "HitByBulletEvent": HitByBulletEvent,
    "InitialPosition": InitialPosition,
    "Message": Message,
    "NextTurn": NextTurn,
    "ObserverHandshake": ObserverHandshake,
    "Participant": Participant,
    "PauseGame": PauseGame,
    "ResultsForBot": ResultsForBot,
    "ResultsForObserver": ResultsForObserver,
    "ResumeGame": ResumeGame,
    "RoundEndedEventForBot": RoundEndedEventForBot,
    "RoundEndedEventForObserver": RoundEndedEventForObserver,
    "RoundStartedEvent": RoundStartedEvent,
    "ScannedBotEvent": ScannedBotEvent,
    "ServerHandshake": ServerHandshake,
    "SkippedTurnEvent": SkippedTurnEvent,
    "StartGame": StartGame,
    "StopGame": StopGame,
    "TeamMessageEvent": TeamMessageEvent,
    "TeamMessage": TeamMessage,
    "TickEventForBot": TickEventForBot,
    "TickEventForObserver": TickEventForObserver,
    "TpsChangedEvent": TpsChangedEvent,
    "WonRoundEvent": WonRoundEvent,
}
