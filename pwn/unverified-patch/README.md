# Unverified Patch

## Category
Pwn

## Difficulty
Easy

## Challenge Description

Post-attack, NECC engineers rushed a pending Mosquitto enhancement live. They didn’t have enough time to secure the new implementation. Task Force Nightfall: it’s on you to check the update ASAP. Audit the broker before the election window closes.

**Creator:** Xclow3n

## Summary
A patched MQTT broker binary contains an off-by-one error in MQTT v5 topic alias handling. The out-of-bounds write corrupts the alias-to-topic mapping table, causing a hidden flag topic to become visible to a wildcard subscriber.

## Provided Files
`pwn_unverified_patch.zip` containing the vulnerable MQTT broker binary

## Tools Used
- mosquitto_sub
- mosquitto (MQTT client tools)

## Walkthrough

### Step 1: Connect with MQTT v5

MQTT v5 is required to exercise the topic alias feature. Connect to the broker with protocol version 5.

### Step 2: Subscribe to the Wildcard Topic

Subscribe to `+` to capture all messages on single-level topics. The wildcard subscription will match topics that become visible after the alias table corruption.

```bash
mosquitto_sub -h <target-ip> -p <target-port> -t '+' -V 5 -W 10
```

### Step 3: Receive the Flag

The off-by-one error in alias index validation causes the broker to write beyond the end of the alias array. This corrupts the adjacent mapping entry, which corresponds to the hidden flag topic. Once corrupted, the flag topic becomes reachable via the `+` wildcard subscription, and the broker delivers the flag as the message payload.

## Key Findings
- MQTT v5 topic aliases are validated by index, but the alias array bound check is off by one, allowing a write to the first byte past the end of the array
- The adjacent memory holds the mapping entry for the hidden flag topic; corrupting it makes the topic reachable via wildcard subscriptions
- The vulnerability requires MQTT v5 to trigger, as topic aliases are a v5-specific feature

## Final Answer
`Flag: HTB{t0p1c_4l1as_0ut_0f_b0und5}`

## Lessons Learned
MQTT v5 introduced several features with complex state management, including topic aliases, shared subscriptions, and user properties. Off-by-one errors in alias index validation can expose private topics to unauthorized subscribers. Broker implementations should be fuzz-tested against the full MQTT v5 specification, particularly at boundary values for alias indices, topic lengths, and subscription identifiers. Patches that fix one boundary condition without auditing adjacent code paths often introduce or leave related bugs; the "unverified patch" framing of this challenge reflects a common real-world pattern where incomplete fixes create new vulnerabilities.
