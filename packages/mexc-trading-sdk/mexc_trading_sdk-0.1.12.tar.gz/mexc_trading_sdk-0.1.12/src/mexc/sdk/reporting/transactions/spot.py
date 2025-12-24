from typing_extensions import TypedDict, Required, Iterable, cast
from datetime import timezone

from trading_sdk.reporting.types import (
  Transaction, Bonus, Yield, InternalTransfer,
  SinglePostingOperation, Other, Operation
)

from .util import Module, PostingMatcher, TaggedPosting, UniqueIds
from .postings import spot_statement
from .operations import fixed_earn, flexible_earn, deposits, withdrawals, spot_trades, fiat_otc_orders

class SpotPaths(TypedDict, total=False):
  spot_statement: Required[str]
  fixed_earn: str
  flexible_earn: str
  deposits: str
  withdrawals: str
  spot_trades: str
  fiat_otc_orders: str

spot_modules: dict[str, Module] = {
  'fixed_earn': fixed_earn,
  'flexible_earn': flexible_earn,
  'deposits': deposits,
  'withdrawals': withdrawals,
  'spot_trades': spot_trades,
  'fiat_otc_orders': fiat_otc_orders,
} # type: ignore (dumb pyright)

transaction_types: dict[str, type[SinglePostingOperation]] = {
  'Spot Commission Sharing': Bonus,
  'Spot Referral Commission': Bonus,
  'Spot Flexible Savings Airdrop': Bonus,
  'Spot Flexible Savings Staking': Yield,
  'Spot Futures Earn Airdrop': Yield,
  'Spot Kickstarter Airdrop': Yield,
  'Spot Launchpad - Airdrop': Yield,
  'Spot Launchpool Airdrop': Yield,
}

def other_transactions(postings: Iterable[TaggedPosting]) -> Iterable[Transaction]:
  ids = UniqueIds()

  for p in postings:
    if (cls := transaction_types.get(p.tag)) is not None:
      op = cls(asset=p.asset, qty=p.change, details=p.tag) # type: ignore
    elif p.tag == 'Spot To Fiat Account':
      op = InternalTransfer(
        asset=p.asset, qty=p.change, details=p.tag,
        from_account='Spot', to_account='Fiat',
      )
    elif p.tag == 'Spot To Futures Account':
      op = InternalTransfer(
        asset=p.asset, qty=p.change, details=p.tag,
        from_account='Spot', to_account='Futures',
      )
    elif p.tag == 'Spot From Fiat Account':
      op = InternalTransfer(
        asset=p.asset, qty=p.change, details=p.tag,
        from_account='Fiat', to_account='Spot',
      )
    elif p.tag == 'Spot From Futures Account':
      op = InternalTransfer(
        asset=p.asset, qty=p.change, details=p.tag,
        from_account='Futures', to_account='Spot',
      )
    else:
      op = Other(details=p.tag)
    
    id = ids.new(f'{p.tag};{p.time:%Y-%m-%d %H:%M:%S}')
    yield Transaction(id=id, time=p.time, operation=cast(Operation, op), postings=[p.posting])


def spot_transactions(
  paths: SpotPaths, tz: timezone, *,
  skip_zero_changes: bool = True
) -> Iterable[list[Transaction]]:

  postings = list(spot_statement.parse(paths['spot_statement'], skip_zero_changes=skip_zero_changes))
  matcher = PostingMatcher.of(postings)
  used = set[int]()

  for key, module in spot_modules.items():
    if (path := paths.get(key)) is not None:
      chunk: list[Transaction] = []
      for op in module.parse(path, tz, skip_zero_changes=skip_zero_changes):
        if (matches := matcher.match(op.expected_postings, time_mode=module.matching_mode)) is None:
          raise ValueError(f'Could not match the postings for the operation: {op}')
        used.update(matches)
        chunk.append(Transaction(
          id=op.id, time=op.time,
          operation=cast(Operation, op),
          postings=[postings[i].posting for i in matches] + list(op.fixed_postings)
        ))
      yield chunk

  unused = set(range(len(postings))) - used
  other_postings = [postings[i] for i in unused]
  yield list(other_transactions(other_postings))
