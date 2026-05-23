# Ghost Access

## Category

Cloud

## Difficulty

Medium

## Challenge Description

Task Force Nightfall is closing the loop after a bruising cloud incident tied to the election logistics chain. The obvious damage is documented. The question is what remains when the noise fades. Given the forensics artifacts, you are now tasked with hunting persistence that outlasts headline cleanup and correlating it with the destruction the operator wanted to look routine.

**Creator:** Xclow3n

## Summary

Following the Exposed Supply incident, the attacker performed a three-hop service account
impersonation chain to escalate privileges, placed a backdoor at the service-account IAM
level rather than the project level, then scrubbed the project-level evidence. Because GCP
cleanup operations typically target project IAM policies, the service-account-level binding
survived and represents the persistent access vector. All ten flags are recoverable by
correlating `admin_activity_logs.csv`, `storage_data_access_logs.csv`, and
`iam_exports.json`.

## Provided Files

`artifacts.zip` containing:
- `artifacts/admin_activity_logs.csv` (GCP Admin Activity audit logs)
- `artifacts/storage_data_access_logs.csv` (GCP Cloud Storage audit logs)
- `artifacts/iam_exports.json` (IAM policy snapshots at project and service-account level)

## Tools Used

- Python 3 (stdlib: `csv`, `json`)

## Walkthrough

1. Parse `admin_activity_logs.csv` for all mutating IAM and secret operations to reconstruct
   the privilege escalation timeline:

   ```bash
   python3 -c "
   import csv
   with open('artifacts/admin_activity_logs.csv') as f:
       for r in csv.DictReader(f):
           method = r.get('protoPayload.methodName', '')
           if any(x in method for x in
                  ['SetIamPolicy', 'CreateServiceAccountKey', 'DestroySecretVersion']):
               print(r['timestamp'], method,
                     r.get('protoPayload.requestMetadata.callerIp', ''))
   "
   ```

   This surfaces the full event sequence attributed to attacker IP `33.252.46.44`.

2. Reconstruct the impersonation chain from `GenerateAccessToken` events:
   - `buildops-ci-runner` SA minted a token for `supply-pipeline-sa`
   - `supply-pipeline-sa` minted a token for `elections-deployer`
   - `elections-deployer` held `roles/resourcemanager.projectIamAdmin` and used it to grant
     itself `roles/iam.securityAdmin` at `2026-05-03T13:36:16Z`

3. Identify the backdoor write event. With `securityAdmin` in hand, `elections-deployer` set
   an IAM policy on the `elections-ghost-sa` service account binding
   `user:gilded@d9.kor` to `roles/iam.serviceAccountTokenCreator` at
   `2026-05-03T13:44:54Z`.

4. Find the cleanup cluster: within the same minute, the attacker removed its own
   `securityAdmin` binding (`2026-05-03T13:45:13Z`), deleted the storage object
   `gs://mec-elections-logistics-pub/config/app.config.json`, and destroyed secret version 3
   of `election-db-credentials`.

   ```bash
   python3 -c "
   import csv
   with open('artifacts/storage_data_access_logs.csv') as f:
       for r in csv.DictReader(f):
           if r.get('protoPayload.methodName') == 'storage.objects.delete':
               print(r['protoPayload.resourceName'], r['timestamp'])
   "
   ```

5. Confirm the surviving backdoor by inspecting `iam_exports.json`. The project-level
   policies show no anomalous bindings post-cleanup, but the per-SA export for
   `elections-ghost-sa` retains `user:gilded@d9.kor` as `serviceAccountTokenCreator`:

   ```bash
   python3 -c "
   import json
   print(json.dumps(json.load(open('artifacts/iam_exports.json')), indent=2))
   "
   ```

## Key Findings

- Attacker IP: `33.252.46.44`
- Impersonation chain: `buildops-ci-runner` -> `supply-pipeline-sa` -> `elections-deployer`
- Privilege enabling escalation: `roles/resourcemanager.projectIamAdmin` on
  `elections-deployer`
- Backdoor: `user:gilded@d9.kor` granted `roles/iam.serviceAccountTokenCreator` on
  `elections-ghost-sa@helical-cursor-494913-k9.iam.gserviceaccount.com` at
  `2026-05-03T13:44:54Z`
- `securityAdmin` self-grant removed at `2026-05-03T13:45:13Z` (19 seconds after the
  backdoor write)
- Deleted storage object: `gs://mec-elections-logistics-pub/config/app.config.json`
- Destroyed secret: `projects/helical-cursor-494913-k9/secrets/election-db-credentials/versions/3`
- The service-account-level IAM binding was not touched during cleanup and survived

## Final Answer

Answers in submission order:

1. `33.252.46.44`
2. `buildops-ci-runner`
3. `supply-pipeline-sa`
4. `elections-deployer`
5. `roles/resourcemanager.projectIamAdmin`
6. `elections-ghost-sa@helical-cursor-494913-k9.iam.gserviceaccount.com`
7. `gilded@d9.kor`
8. `roles/iam.serviceAccountTokenCreator`
9. `gs://mec-elections-logistics-pub/config/app.config.json`
10. `election-db-credentials`

## Lessons Learned

Attackers routinely remove their project-level IAM modifications during cleanup while leaving
service-account-level bindings intact, since most detection tooling focuses on project policy
changes. Post-incident investigations must enumerate both project IAM policies and the
individual IAM policies attached to every service account in the project.
