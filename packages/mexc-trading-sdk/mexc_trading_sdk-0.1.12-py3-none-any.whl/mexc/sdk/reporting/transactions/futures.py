from typing_extensions import TypedDict, Required, Iterable, cast
from datetime import timezone

from trading_sdk.reporting.types import (
  Transaction, Bonus, PerpetualSettlement, PerpetualFunding, InternalTransfer,
  SinglePostingOperation, Other, Operation
)

from .postings import futures_capital_flow
from .operations import futures_trades
from .util import PostingMatcher, TaggedPosting, UniqueIds

class FuturesPaths(TypedDict, total=False):
  futures_capital_flow: Required[str]
  futures_trades: str

transaction_types: dict[str, type[SinglePostingOperation]] = {
  'Futures BONUS': Bonus,
  'Futures CLOSE_POSITION': PerpetualSettlement,
  'Futures LIQUIDATION': PerpetualSettlement,
  'Futures FUNDING': PerpetualFunding,
}

def other_transactions(postings: Iterable[TaggedPosting]) -> Iterable[Transaction]:
  ids = UniqueIds()
  for p in postings:
    if (cls := transaction_types.get(p.tag)) is not None:
      op = cls(asset=p.asset, qty=p.change, details=p.tag) # type: ignore
    elif p.tag == 'Futures TRANSFER':
      op = InternalTransfer(
        asset=p.asset, qty=p.change, details=p.tag,
        from_account='Spot' if p.change > 0 else 'Futures',
        to_account='Futures' if p.change > 0 else 'Spot',
      )
    else:
      op = Other(details=p.tag)
    
    id = ids.new(f'{p.tag};{p.time:%Y-%m-%d %H:%M:%S}')
    yield Transaction(id=id, time=p.time, operation=cast(Operation, op), postings=[p.posting])

def futures_transactions(
  paths: FuturesPaths, tz: timezone, *,
  skip_zero_changes: bool = True
) -> Iterable[list[Transaction]]:

  postings = list(futures_capital_flow.parse(paths['futures_capital_flow'], skip_zero_changes=skip_zero_changes))
  matcher = PostingMatcher.of(postings)
  used = set[int]()


  if (path := paths.get('futures_trades')) is not None:
    chunk: list[Transaction] = []
    for op in futures_trades.parse(path, tz, skip_zero_changes=skip_zero_changes):
      if (matches := matcher.match(op.expected_postings, time_mode=futures_trades.matching_mode)) is None:
        raise ValueError(f'Could not match the postings for the operation: {op}')
      used.update(matches)
      chunk.append(Transaction(
        id=op.id, time=op.time,
        operation=cast(Operation, op),
        postings=[postings[i].posting for i in matches] + op.fixed_postings
      ))
    yield chunk

  unused = set(range(len(postings))) - used
  other_postings = [postings[i] for i in unused]

