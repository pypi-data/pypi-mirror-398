from typing_extensions import Protocol, AsyncIterable, Sequence
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime
from trading_sdk.types import Num

@dataclass
class Reward:
  asset: Decimal
  qty: Decimal
  time: datetime

class RewardHistory(Protocol):
  async def reward_history(
    self, *, start: datetime | None = None,
    end: datetime | None = None
  ) -> AsyncIterable[Sequence[Reward]]:
    """Fetch earn rewards.
    
    - `start`: if given, retrieves rewards after this time.
    - `end`: if given, retrieves rewards before this time.
    """
    ...

  async def reward_history_sync(
    self, *, start: datetime | None = None,
    end: datetime | None = None
  ) -> Sequence[Reward]:
    """Fetch earn rewards, without streaming.
    
    - `start`: if given, retrieves rewards after this time.
    - `end`: if given, retrieves rewards before this time.
    """
    rewards: list[Reward] = []
    async for batch in self.reward_history(start=start, end=end):
      rewards.extend(batch)
    return rewards