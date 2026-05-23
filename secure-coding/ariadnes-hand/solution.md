# Ariadne's Hand

## Category
Secure Coding

## Difficulty
Hard

## Score
94/100 (Hard: 60/60, Soft: 34/40)

## Summary
ARIADNE NMP is an ASP.NET Core web console managing a simulated Spanning Tree Protocol network.
The single exploitable vulnerability is an unbounded recursive DFS in `BpduForwarder.ForwardBpdu`
that causes exponential re-traversal on any cyclic topology. The fix adds a visited-node set,
an independent TTL guard, and passes `hopCount` as a value type to eliminate shared-state
corruption between sibling branches.

## Provided Files
- Git repository at `http://<target-ip>:<target-port>/git/core_application.git`

## Tools Used
- Git
- dotnet (ASP.NET Core)
- curl

## Walkthrough

**Root cause analysis:**

`TopologyService` builds a bidirectional adjacency list: every edge (A, B) adds both A to B's
neighbor list and B to A's neighbor list. This creates cycles in all non-trivial topologies
(for example, SW-CORE-01 to SW-DIST-01 to SW-CORE-01). `ForwardBpdu` contains no visited-node
tracking, so the DFS re-enters every previously visited node indefinitely.

Two secondary issues compound the problem:

1. The 500-entry log cap stops log output but does not stop recursion. Stack overflow is
   possible on larger topologies.
2. `packet.HopCount` is a shared mutable reference. Sibling branches read and overwrite each
   other's depth counter, producing incorrect hop counts and masking actual depth.

The `/app/api/simulate` endpoint is decorated with `[AllowAnonymous]`, so any unauthenticated
client can trigger the denial-of-service with a single HTTP request.

**Fix applied to `src/StpService/Services/BpduForwarder.cs`:**

The public method signature is unchanged. A private overload carries `origin` (immutable
string), `hopCount` (int value type, copied per call), and a `HashSet<string> visited` to
ensure each traversal visits each node exactly once.

```csharp
public class BpduForwarder
{
    private const int MaxHops = 64;

    public void ForwardBpdu(string nodeId, BpduPacket packet)
        => ForwardBpdu(nodeId, packet.Origin, packet.HopCount, new HashSet<string>());

    private void ForwardBpdu(string nodeId, string origin, int hopCount, HashSet<string> visited)
    {
        if (!visited.Add(nodeId)) return;
        if (hopCount >= MaxHops) return;
        if (_log.Count >= 500) return;

        var sev  = hopCount >= 10 ? "2" : hopCount >= 5 ? "4" : "6";
        var port = $"Gi0/{(hopCount % 4) + 1}";
        _log.Add($"[{DateTime.UtcNow:HH:mm:ss.fff}] {nodeId} %STP-{sev}-BPDU_FWD: " +
                 $"origin={origin} hop-count={hopCount} port={port}");

        if (!_topology.ContainsKey(nodeId)) return;

        foreach (var neighbor in _topology[nodeId])
            ForwardBpdu(neighbor, origin, hopCount + 1, visited);
    }
}
```

Three guards are applied in depth order:

1. `HashSet<string> visited`: each node is visited exactly once per traversal, reducing
   complexity from O(infinity) to O(N)
2. `MaxHops = 64`: independent TTL guard providing defense in depth if the visited set were
   somehow bypassed
3. Log cap retained as a final output-size safety net

**Deployment:**

```bash
git clone http://htb_developer:HTBDeveloperPassword@<target-ip>:<target-port>/git/core_application.git
cd core_application
git checkout -b developer
# Edit src/StpService/Services/BpduForwarder.cs
git add src/StpService/Services/BpduForwarder.cs
git commit -m "Fix BPDU forwarding: cycle detection, TTL guard, immutable hop count"
git push -u origin developer
```

## Key Findings

- Bidirectional adjacency lists create cycles in all non-trivial topologies; the DFS must
  track visited nodes to avoid infinite recursion
- The `/app/api/simulate` endpoint is `[AllowAnonymous]`; an unauthenticated attacker can
  trigger the DoS with one HTTP request
- The 500-entry log cap was superficially similar to a fix but only limits log output, not
  recursion depth
- Passing `hopCount` as a value type (int) rather than a mutable field ensures sibling
  branches have independent depth counters

## Final Answer

`Flag: HTB{7H3S3U5_F0LL0WS_THE_THR34D_0e6fd9bfc5dcaef838619e26da002b65}`

## Lessons Learned

Graph traversal algorithms must always track visited nodes when operating on cyclic graphs.
A log-entry cap does not substitute for algorithmic termination. Exposing diagnostic or
simulation endpoints without authentication enables denial-of-service by any unauthenticated
user and should be treated as a separate vulnerability independent of the algorithmic one.
Defense-in-depth with a TTL guard costs one integer comparison per call and provides a
meaningful safety net.
