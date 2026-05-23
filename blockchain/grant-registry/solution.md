# Grant Registry

## Category

Blockchain

## Difficulty

Easy

## Summary

A Solana program validates operator eligibility before allowing grant allocation by calling
`load_instruction_at_checked(0usize, ...)`, which always inspects instruction index 0 in the
transaction regardless of which instruction is currently executing. Placing one
`register_eligibility` instruction at position 0 followed by three `claim_allocation`
instructions in the same transaction causes all three allocation calls to see the eligibility
check as satisfied, allowing a single transaction to reach the `isSolved()` threshold.

## Provided Files

`grant_registry.zip` (Solana program source code and deployment artifacts)

## Tools Used

- Python 3
- Solana Python SDK (`solana-py`)
- curl

## Walkthrough

1. Review the on-chain program source in `grant_registry.zip`. The `claim_allocation` handler
   contains:

   ```rust
   let ix = load_instruction_at_checked(0usize, &sysvar_info)?;
   // validates that ix is a register_eligibility call
   ```

   The hardcoded `0usize` means it always checks the first instruction in the transaction,
   not the instruction currently being processed by the runtime.

2. Launch the challenge instance and collect the RPC endpoint and player keypair from the
   response:

   ```bash
   curl -s -c /tmp/htb_cookie.txt http://<target-ip>:<target-port>/ -o /dev/null
   curl -s -b /tmp/htb_cookie.txt -c /tmp/htb_cookie.txt \
     -X POST http://<target-ip>:<target-port>/launch
   ```

3. Craft a transaction with four instructions in order:
   - `ix[0]`: `register_eligibility` (satisfies the hardcoded index-0 check)
   - `ix[1]`: `claim_allocation`
   - `ix[2]`: `claim_allocation`
   - `ix[3]`: `claim_allocation`

   Each `claim_allocation` reads `ix[0]`, finds `register_eligibility`, and proceeds. The
   allocation counter increments three times in a single atomic transaction, satisfying the
   `isSolved()` condition.

   Update `RPC_URL`, `PLAYER_KEYPAIR_B58`, and `CTX_PUBKEY` in the exploit script, then run:

   ```bash
   python3 work/exploit.py
   ```

4. Retrieve the flag:

   ```bash
   curl -s -b /tmp/htb_cookie.txt http://<target-ip>:<target-port>/flag
   ```

## Key Findings

- The eligibility guard uses a hardcoded instruction index (`0usize`) instead of the
  dynamically resolved index of the currently executing instruction.
- Solana transactions are atomic, so all four instructions execute together, and the runtime
  does not reset the instruction pointer between them.
- No additional accounts, signatures, or program state mutations were needed beyond crafting
  the instruction order correctly.

## Final Answer

`Flag: HTB{gr4nt_r3g1stry_1nstruct10n_1ntr0sp3ct10n}`

## Lessons Learned

Solana instruction introspection must always resolve the index of the currently executing
instruction dynamically. Hardcoding a fixed index allows any instruction at that position to
satisfy a guard that was intended to be position-sensitive relative to the calling instruction.
