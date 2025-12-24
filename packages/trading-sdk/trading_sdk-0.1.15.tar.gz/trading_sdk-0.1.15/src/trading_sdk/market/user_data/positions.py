from typing_extensions import Protocol, TypeVar, Mapping
from dataclasses import dataclass
from decimal import Decimal
import asyncio

S = TypeVar('S', bound=str, default=str)

@dataclass
class Position:
  size: Decimal
  """Signed position size (negative for short, positive for long)."""
  entry_price: Decimal

class Positions(Protocol):
  async def position(self, instrument: S, /) -> Position | None:
    """Get the open position on a given instrument, if any."""
    return (await self.positions(instrument))[instrument]

  async def positions(self, *instruments: S) -> Mapping[S, Position]:
    """Get the open positions on the given instruments. If none are provided, get all positions."""
    positions = await asyncio.gather(*(self.position(instrument) for instrument in instruments))
    return {instrument: position for instrument, position in zip(instruments, positions) if position is not None}

class PerpPositions(Positions, Protocol):
  async def perp_position(self, base: str, quote: str, /) -> Position | None:
    """Get the open position on a given perpetual instrument, if any."""
    ...

class InversePerpPositions(Positions, Protocol):
  async def inverse_perp_position(self, currency: str, /) -> Position | None:
    """Get the open position on a given inverse perpetual instrument, if any."""
    ...