# Exposed Supply

## Category

Cloud

## Difficulty

Easy

## Challenge Description

Task Force Nightfall is racing the clock. Reports say election logistics partners are bleeding operational detail into places civilians can reach. You are joining the forensics line, working from captured site and cloud evidence to show how a rushed supplier footprint became a gift to an adversary that thrives on dependency.

**Creator:** Xclow3n

## Summary

A cloud forensics challenge requiring static analysis of GCP audit logs and captured web
artifacts to reconstruct how a rushed supplier deployment exposed election logistics data.
A `storage.buckets.update` event made a private GCP bucket public, and the accompanying
website snapshot contained a JavaScript bundle with a base64-encoded service account key
email and a nested zip file holding the plaintext key JSON. All eight flags are recoverable
from the provided artifacts without any live GCP access.

## Provided Files

`artifacts.zip` containing:
- `artifacts/storage_data_access_logs.csv` (GCP Cloud Storage audit logs)
- `artifacts/website_snapshot/` (captured web assets including `main.min.js` and
  `supply-bundle.zip`)

## Tools Used

- Python 3 (stdlib: `csv`, `re`, `base64`)
- unzip

## Walkthrough

1. Parse `storage_data_access_logs.csv` to find the `storage.buckets.update` event that
   made the bucket public:

   ```bash
   python3 -c "
   import csv
   for r in csv.DictReader(open('artifacts/storage_data_access_logs.csv')):
       if 'update' in r.get('protoPayload.methodName', '').lower():
           print(r)
   "
   ```

   Key fields from the result:
   - Bucket name: `mec-elections-logistics-pub`
   - Timestamp: `2026-05-03T06:59:21Z`
   - Principal: `admin@nightfall.net`
   - Caller IP: `88.65.198.198`
   - Simultaneous upload: `supply-bundle.zip`

2. Extract base64-encoded strings from `main.min.js` and filter for service account domains:

   ```bash
   python3 -c "
   import re, base64
   c = open('artifacts/website_snapshot/assets/main.min.js').read()
   for m in re.findall(r'[A-Za-z0-9+/]{50,}={0,2}', c):
       try:
           d = base64.b64decode(m + '==').decode('utf-8', errors='ignore')
           if 'gserviceaccount' in d:
               print(d)
       except Exception:
           pass
   "
   ```

   This reveals the service account key email embedded in the bundle:
   `buildops-ci-runner@helical-cursor-494913-k9.iam.gserviceaccount.com`

3. Extract the plaintext service account key from the nested `supply-bundle.zip`:

   ```bash
   unzip -p artifacts/website_snapshot/supply-bundle.zip \
     pipeline-export/github-actions/buildops-ci-runner-svcacct.json
   ```

   The key file confirms:
   - Key path in the bundle: `pipeline-export/github-actions/buildops-ci-runner-svcacct.json`
   - GCP project ID: `helical-cursor-494913-k9`

4. Cross-reference the log timestamp and caller IP to confirm the upload of `supply-bundle.zip`
   occurred in the same second as the bucket ACL change, indicating an automated pipeline that
   made the bucket public and then immediately wrote the artifact.

## Key Findings

- The bucket `mec-elections-logistics-pub` was made public via `storage.buckets.update` at
  `2026-05-03T06:59:21Z` by `admin@nightfall.net` from IP `88.65.198.198`.
- A JavaScript bundle in the website snapshot contained a base64-encoded service account
  email, leaking the identity of the CI runner.
- The same snapshot included `supply-bundle.zip` with a plaintext GCP service account key
  JSON for `buildops-ci-runner`.
- The GCP project ID `helical-cursor-494913-k9` was embedded in the key file, providing the
  full resource namespace for further investigation.
- All exposure occurred as a side effect of a single automated deployment step.

## Final Answer

See the Walkthrough section for all 8 answers. Answers in submission order:

1. `mec-elections-logistics-pub`
2. `2026-05-03T06:59:21Z`
3. `admin@nightfall.net`
4. `88.65.198.198`
5. `supply-bundle.zip`
6. `helical-cursor-494913-k9.iam.gserviceaccount.com`
7. `pipeline-export/github-actions/buildops-ci-runner-svcacct.json`
8. `helical-cursor-494913-k9`

## Lessons Learned

Public cloud storage buckets combined with exposed JavaScript bundles can leak service account
credentials in a single deployment action. Log timestamps and caller IP addresses are the
primary forensic anchors for reconstructing the sequence of events, and post-incident review
must cover both ACL changes and simultaneous uploads.
