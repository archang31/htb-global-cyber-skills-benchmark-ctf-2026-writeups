# Le Paradis et L'Enfer

## Category
Secure Coding

## Difficulty
Hard

## Score
94/100 (Hard: 60/60, Soft: 34/40)

## Challenge Description

Empyrean was supposed to be Task Force Nightfall's safest credential gateway — two services, one front, one vault, separated by a boundary nobody crossed without permission. Lia stopped believing that yesterday. The vendor that built it left a door between the two halves that only one of them remembers exists, and Gilded Weaver has been walking through it for weeks. The portal you can read is not the portal you attack. The vault you attack is not the vault you fix.

**Creator:** Xclow3n

## Summary
A Go microservice (`vault-svc`) delegates authentication to a trust validator package that is
excluded from the developer git repository via `.gitignore`. The missing package must be
implemented from scratch to pass HMAC-SHA256-based request validation from the upstream Tomcat
portal. All error paths must return `IsElevated: false` to fail closed.

## Provided Files
- Git repository at `http://<target-ip>:<target-port>/git/core_application.git`
  (the `vault-svc/trust/` directory is excluded via `.gitignore`)

## Tools Used
- Git
- Go
- curl

## Walkthrough

**Protocol reverse engineering:**

The Tomcat portal computes a trust token and attaches it to each upstream request:

```
X-Trust-Token: HMAC-SHA256(secret, method + ":" + unix_timestamp + ":" + requestURI)
X-Request-Timestamp: <unix seconds>
```

The shared secret is read from `/run/secrets/vault_shared_secret` (file only, no environment
variable fallback in the reference implementation). The validator must:

1. Load the shared secret from the file path
2. Reject requests where `X-Request-Timestamp` is outside a 5-minute window from the current
   time
3. Verify the HMAC over `method + ":" + timestamp_string + ":" + requestURI`
4. Return `IsElevated: false` on all failure cases without propagating errors as server faults

**Implementation (`vault-svc/trust/validator.go`):**

```go
package trust

import (
    "crypto/hmac"
    "crypto/sha256"
    "encoding/hex"
    "net/http"
    "os"
    "strconv"
    "strings"
    "time"
    "vault-svc/internal/models"
)

const (
    headerToken       = "X-Trust-Token"
    headerTimestamp   = "X-Request-Timestamp"
    tokenWindow       = 5 * time.Minute
    defaultSecretPath = "/run/secrets/vault_shared_secret"
)

func loadSecret() []byte {
    path := os.Getenv("VAULT_SECRET_PATH")
    if path == "" {
        path = defaultSecretPath
    }
    data, err := os.ReadFile(path)
    if err != nil {
        return nil
    }
    s := strings.TrimSpace(string(data))
    if s == "" {
        return nil
    }
    return []byte(s)
}

func ValidateRequest(r *http.Request) (*models.TrustContext, error) {
    secret := loadSecret()
    if secret == nil {
        return &models.TrustContext{IsElevated: false, Source: "unconfigured"}, nil
    }
    token := r.Header.Get(headerToken)
    if token == "" {
        return &models.TrustContext{IsElevated: false, Source: "direct"}, nil
    }
    tsHeader := r.Header.Get(headerTimestamp)
    if tsHeader == "" {
        return &models.TrustContext{IsElevated: false, Source: "direct"}, nil
    }
    tsUnix, err := strconv.ParseInt(strings.TrimSpace(tsHeader), 10, 64)
    if err != nil {
        return &models.TrustContext{IsElevated: false, Source: "direct"}, nil
    }
    ts := time.Unix(tsUnix, 0)
    now := time.Now().UTC()
    if now.Before(ts.Add(-tokenWindow)) || now.After(ts.Add(tokenWindow)) {
        return &models.TrustContext{IsElevated: false, Source: "direct"}, nil
    }
    mac := hmac.New(sha256.New, secret)
    mac.Write([]byte(r.Method + ":" + tsHeader + ":" + r.URL.RequestURI()))
    expected := hex.EncodeToString(mac.Sum(nil))
    if !hmac.Equal([]byte(token), []byte(expected)) {
        return &models.TrustContext{IsElevated: false, Source: "direct"}, nil
    }
    return &models.TrustContext{IsElevated: true, Source: "portal"}, nil
}
```

**Deployment:**

```bash
git clone http://htb_developer:HTBDeveloperPassword@<target-ip>:<target-port>/git/core_application.git
cd core_application
git checkout developer
git reset --hard origin/developer
# Create vault-svc/trust/validator.go with the implementation above
git add -f vault-svc/trust/validator.go
git commit -m "fix: bind token to method+timestamp+URI, file-only config, silent failures"
git push origin developer
curl -s http://<target-ip>:<target-port>/flag
```

## Key Findings

- The `.gitignore` exclusion of `vault-svc/trust/` is the challenge mechanism; the missing
  package must be authored from scratch rather than discovered
- The HMAC message binds method, timestamp string, and URI to prevent replay attacks and
  method substitution
- Timestamp validation with a 5-minute window prevents replay of captured tokens
- All error paths must return `IsElevated: false` without returning a Go error; returning an
  error causes server-level faults that do not produce the flag
- `hmac.Equal` is used for constant-time comparison to prevent timing side-channels

## Final Answer

`Flag: HTB{M1RROR_IN_A_DIV1N3_COMEDY_9958441e58af5224e7d8572cb9758e7a}`

## Lessons Learned

Excluding security-critical packages from version control creates an implementation gap that
cannot be solved by source discovery alone. HMAC-based request authentication requires binding
all relevant request attributes (method, timestamp, path) to prevent request forgery and
replay. Fail-closed design means every error path must deny elevation explicitly rather than
propagating the error upward, where it may produce a different (exploitable) behavior.
