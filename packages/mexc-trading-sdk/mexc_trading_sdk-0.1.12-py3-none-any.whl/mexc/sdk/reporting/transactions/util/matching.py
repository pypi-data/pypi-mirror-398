from typing_extensions import Iterable, Sequence, Literal, Mapping, MutableMapping, Protocol
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime, timezone
from collections import defaultdict

from trading_sdk.reporting.types import Posting

TimeMode = Literal['eq', 'ge', 'le']

@dataclass(kw_only=True)
class TaggedPosting:
  posting: Posting
  time: datetime
  tag: str

  @property
  def asset(self) -> str:
    return self.posting.asset

  @property
  def change(self) -> Decimal:
    return self.posting.change

@dataclass
class Operation:
  time: datetime
  @property
  def id(self) -> str:
    ...

  @property
  def expected_postings(self) -> Sequence[TaggedPosting]:
    """Postings expected to be matched."""
    return []

  @property
  def fixed_postings(self) -> Sequence[Posting]:
    """Postings not appearing in the statement but that should be included in the transaction."""
    return []

class Module(Protocol):
  matching_mode: Literal['eq', 'ge']

  @staticmethod
  def parse(path: str, tz: timezone, /, *, skip_zero_changes: bool = True) -> Iterable[Operation]:
    ...


@dataclass
class PostingMatcher:
  postings: Sequence[TaggedPosting]
  index: Mapping[str, Mapping[str, Mapping[datetime, MutableMapping[int, TaggedPosting]]]]

  @classmethod
  def of(cls, postings: Sequence[TaggedPosting]):
    idx = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))
    for i, p in enumerate(postings):
      idx[p.asset][p.tag][p.time][i] = p
    return cls(postings, idx)

  def candidates(self, p_hat: TaggedPosting, *, time_mode: TimeMode = 'eq') -> MutableMapping[int, TaggedPosting]:
    group = self.index[p_hat.asset][p_hat.tag]
    if time_mode == 'eq':
      return group[p_hat.time]
    elif time_mode == 'ge':
      ts = [t for t in group.keys() if p_hat.time <= t]
    else:
      ts = [t for t in group.keys() if t <= p_hat.time]
    out: dict[int, TaggedPosting] = {}
    for t in ts:
      out.update(group[t])
    return out

  def use(self, key: int):
    p = self.postings[key]
    del self.index[p.asset][p.tag][p.time][key]

  def insert(self, key: int):
    p = self.postings[key]
    self.index[p.asset][p.tag][p.time][key] = p

  def match(self, postings: Iterable[TaggedPosting], *, time_mode: TimeMode = 'eq') -> list[int] | None:
    """Match the postings to the postings in the matcher. The matched postings are removed from the matcher, preventing double-matching."""
    out = []
    for p_hat in postings:
      candidates = self.candidates(p_hat, time_mode=time_mode)
      if len(candidates) == 0:
        for k in out:
          self.insert(k) # restore the used postings
        return None
      elif len(candidates) == 1:
        k = next(iter(candidates.keys()))
      else:
        k = min(candidates.keys(), key=lambda i: abs(p_hat.change - candidates[i].change))
      self.use(k)
      out.append(k)
    return out
