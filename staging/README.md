# Local collection state

The collector creates `collection.sqlite3`, `evidence/`, `runs/` and recoverable
review transactions here. These files are ignored by Git. Back up this directory
together with `data/` while the local app is stopped. Do not delete an unfinished
`pending_transaction.json`: the next reviewer startup recovers it under a lock.

Only explicit human review writes canonical CSV rows. A collector never does.
