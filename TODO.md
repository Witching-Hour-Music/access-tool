# Access Tool TODO

## Completed in this change
- Restored master wallet export support with one row per connected wallet.
- Fixed optional staking enrichment to read TON nominators-pool participation and keep exporting when individual wallet lookups fail.
- Added tests for wallet aggregation and staking-pool amount parsing/fallback behavior.

## Next steps
- Run the full Docker test suite with `make test` in an environment with the database services available.
- Exercise the export CLI against a staging database and compare `staked_in_pools` totals with TonAPI responses for several known staking wallets.
- Decide whether export output should include both raw nanoTON staking amounts and human-readable TON amounts.
- Add pagination or concurrency limits if real-world exports show TON API rate-limit pressure.
- Wire the master wallet JSON artifact into the operational debugging workflow, including storage location and retention policy.
