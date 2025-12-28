"""
Generated Python class from message.schema.yaml
This file is auto-generated. Do not edit manually.
"""

from enum import Enum

class Message:
    """Abstract message exchanged between server and client"""


    class Type(str, Enum):
        BOT_HANDSHAKE = "BotHandshake"
        CONTROLLER_HANDSHAKE = "ControllerHandshake"
        OBSERVER_HANDSHAKE = "ObserverHandshake"
        SERVER_HANDSHAKE = "ServerHandshake"
        BOT_READY = "BotReady"
        BOT_INTENT = "BotIntent"
        BOT_INFO = "BotInfo"
        BOT_LIST_UPDATE = "BotListUpdate"
        GAME_STARTED_EVENT_FOR_BOT = "GameStartedEventForBot"
        GAME_STARTED_EVENT_FOR_OBSERVER = "GameStartedEventForObserver"
        GAME_ENDED_EVENT_FOR_BOT = "GameEndedEventForBot"
        GAME_ENDED_EVENT_FOR_OBSERVER = "GameEndedEventForObserver"
        GAME_ABORTED_EVENT = "GameAbortedEvent"
        GAME_PAUSED_EVENT_FOR_OBSERVER = "GamePausedEventForObserver"
        GAME_RESUMED_EVENT_FOR_OBSERVER = "GameResumedEventForObserver"
        ROUND_STARTED_EVENT = "RoundStartedEvent"
        ROUND_ENDED_EVENT_FOR_BOT = "RoundEndedEventForBot"
        ROUND_ENDED_EVENT_FOR_OBSERVER = "RoundEndedEventForObserver"
        CHANGE_TPS = "ChangeTps"
        TPS_CHANGED_EVENT = "TpsChangedEvent"
        BOT_POLICY_UPDATE = "BotPolicyUpdate"
        BOT_DEATH_EVENT = "BotDeathEvent"
        BOT_HIT_BOT_EVENT = "BotHitBotEvent"
        BOT_HIT_WALL_EVENT = "BotHitWallEvent"
        BULLET_FIRED_EVENT = "BulletFiredEvent"
        BULLET_HIT_BOT_EVENT = "BulletHitBotEvent"
        BULLET_HIT_BULLET_EVENT = "BulletHitBulletEvent"
        BULLET_HIT_WALL_EVENT = "BulletHitWallEvent"
        HIT_BY_BULLET_EVENT = "HitByBulletEvent"
        SCANNED_BOT_EVENT = "ScannedBotEvent"
        SKIPPED_TURN_EVENT = "SkippedTurnEvent"
        TICK_EVENT_FOR_BOT = "TickEventForBot"
        TICK_EVENT_FOR_OBSERVER = "TickEventForObserver"
        WON_ROUND_EVENT = "WonRoundEvent"
        TEAM_MESSAGE_EVENT = "TeamMessageEvent"
        START_GAME = "StartGame"
        STOP_GAME = "StopGame"
        PAUSE_GAME = "PauseGame"
        RESUME_GAME = "ResumeGame"
        NEXT_TURN = "NextTurn"

    def __init__(self, type: 'Message.Type | None'):
        if type is None:
            raise ValueError("The 'type' parameter must be provided.")
        self.type = type
