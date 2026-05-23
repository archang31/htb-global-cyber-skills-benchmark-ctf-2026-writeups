# Sector Blackout

## Category
ICS

## Difficulty
Medium

## Summary
A BACnet-controlled lighting system for a building sector is exposed via a TCP proxy. Writing all 12 binary-value lighting objects to inactive (0) via BACnet WriteProperty triggers a blackout condition that causes the server to return the flag.

## Provided Files
`ics_sector_blackout.zip` (source code and proxy scripts)

## Tools Used
- Python 3
- bacpypes3

## Walkthrough

### Network Topology

The challenge exposes two TCP ports:
- Port A: aiohttp web UI, polls `/api/status` for light states and serves the flag once blackout is confirmed
- Port B: BACnet TCP proxy (`tcp2udp.py`), uses length-prefixed framing to forward packets to local UDP 47808

Support scripts included in the source:
- `udp2tcp.py`: converts local UDP 47808 traffic to TCP toward the proxy
- BACnet device 1001: local router at Network 1001
- BACnet device 2001: light controller at Network 2001, address `0x02`
- Objects: 12 `binaryValue` objects (type 5, instances 1-12)

### Attack

1. Connect through the TCP proxy to BACnet device 2001 on Network 2001
2. For each of the 12 `binaryValue` objects (instances 1-12), send a `WriteProperty` request setting `presentValue` to `0` (inactive) at priority 8
3. BVLC header must use `0x0a` (Original-Unicast-NPDU); broadcast (`0x0b`) receives no response from device 2001
4. NPDU routing parameters for device 2001: `ctrl=0x24`, `dest_net=2001`, `dest_addr=0x02`, `hop_count=0xFF`
5. After all 12 sectors are written to 0, poll `/api/status` to confirm blackout, then retrieve the flag

```bash
pip install bacpypes3
python3 work/exploit2.py
```

### BVLC and NPDU Notes

BACnet/IP over the TCP proxy requires correctly structured packets:
- BVLC type `0x81`, function `0x0a` (Original-Unicast-NPDU), length = total packet length
- NPDU with destination network routing: `ctrl=0x24` sets the destination specifier bit and hop count present bit
- `dest_net=2001` (big-endian uint16), `dest_adr_len=1`, `dest_addr=0x02`, `hop_count=0xFF`

## Key Findings
- BACnet UDP requires no authentication; any device that can reach the network can write to any object
- The TCP proxy preserves BACnet framing transparently; the exploit is structurally identical to direct BACnet/IP communication
- Broadcast BVLC packets (`0x0b`) are silently ignored by device 2001; unicast addressing is required
- BACnet priority arrays allow an attacker to assert a high-priority value that overrides normal setpoints without permanently modifying the object's default

## Final Answer
`Flag: HTB{d4rk_bld9_m4st3r_0f_BACn3t}`

## Lessons Learned
BACnet lacks authentication by design. BACnet Secure Connect (BACnet/SC) addresses this in newer deployments, but legacy UDP-based BACnet remains unauthenticated. ICS equipment exposed via TCP proxies should implement an authentication layer at the proxy level rather than relying on the underlying protocol. Priority arrays in BACnet, intended for emergency override scenarios, are equally available to attackers; network segmentation and firewall rules are the primary mitigation in the absence of protocol-level authentication.
