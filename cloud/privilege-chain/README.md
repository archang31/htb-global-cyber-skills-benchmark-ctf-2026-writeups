# Privilege Chain

## Category

Cloud

## Difficulty

Hard

## Challenge Description

Task Force Nightfall is reconstructing a state-grade maneuver aimed at the logistics and delivery fabric behind the vote. The trail is not a single broken password. It is a sequence of handoffs, escalations, and releases that only make sense when you read them in order. You now have to tie together administrative motion and supply-side artifacts until the story holds in court, not just in a dashboard.

**Creator:** Xclow3n

## Summary

A state-grade supply chain attack is reconstructed across GCP audit logs, an artifact
registry inventory, and a captured Docker image tar. A single leaked service account key
was used to traverse a two-hop impersonation chain, escalate to `securityAdmin`, and push a
malicious container image carrying a C2 callback address. All fifteen flags are recoverable
by correlating timestamps across the provided artifacts and inspecting the Docker image
config blob directly.

## Provided Files

`artifacts.zip` containing:
- `artifacts/admin_activity_logs.csv` (GCP Admin Activity audit logs)
- `artifacts/storage_data_access_logs.csv` (GCP Cloud Storage audit logs)
- `artifacts/artifact_registry_inventory.json` (Artifact Registry image metadata)
- `artifacts/docker/ops_diagnostics_v0_9_7.tar` (Docker image tar of the malicious image)

## Tools Used

- Python 3 (stdlib: `csv`, `json`)
- tar
- jq

## Walkthrough

1. Extract and read the leaked service account key to confirm the initial foothold identity
   and GCP project:

   ```bash
   unzip website_snapshot/supply-bundle.zip
   cat pipeline-export/github-actions/buildops-ci-runner-svcacct.json
   ```

   Confirms: `buildops-ci-runner@helical-cursor-494913-k9.iam.gserviceaccount.com`

2. Parse `admin_activity_logs.csv` for `GenerateAccessToken` and `SetIamPolicy` events to
   reconstruct the impersonation chain and privilege escalation:

   ```bash
   python3 -c "
   import csv
   with open('artifacts/admin_activity_logs.csv') as f:
       for r in csv.DictReader(f):
           m = r.get('protoPayload.methodName', '')
           if 'GenerateAccessToken' in m or 'SetIamPolicy' in m or \
              'CreateServiceAccountKey' in m:
               print(r['timestamp'], m, r.get('protoPayload.resourceName', ''))
   "
   ```

   Timeline reconstructed:
   - `2026-05-03T13:36:05Z`: `buildops-ci-runner` minted token for `supply-pipeline-sa`
   - `2026-05-03T13:36:12Z`: `supply-pipeline-sa` minted token for `elections-deployer`
     using scope `https://www.googleapis.com/auth/cloud-platform`
   - `2026-05-03T13:36:16Z`: `elections-deployer` used `projectIamAdmin` to grant self
     `roles/iam.securityAdmin` (binding:
     `serviceAccount:elections-deployer@helical-cursor-494913-k9.iam.gserviceaccount.com:roles/iam.securityAdmin`)
   - `2026-05-03T13:37:01Z`: malicious image pushed to `elections-supply-registry`

3. Inspect the Artifact Registry inventory for the malicious image push:

   ```bash
   cat artifacts/artifact_registry_inventory.json | python3 -m json.tool
   ```

   Confirms:
   - Registry: `elections-supply-registry`
   - Image name: `ops-diagnostics`
   - Tag: `v0.9.7`
   - Push timestamp: `2026-05-03T13:37:01Z`
   - Index manifest SHA256:
     `54a2f31d64746d77e0ff0e9587ffea4f91f48d496f5651717c74f9b867743eee`

4. Extract and inspect the Docker image tar to find the malicious layer and the embedded C2
   environment variable:

   ```bash
   tar xf artifacts/docker/ops_diagnostics_v0_9_7.tar -C /tmp/img_extract
   # Locate manifest.json to identify the config blob hash
   cat /tmp/img_extract/manifest.json | python3 -m json.tool
   # Read the config blob
   cat /tmp/img_extract/<config-blob-hash>.json | python3 -m json.tool
   ```

   The config `Env` array contains `CALLBACK_HOST=185.220.101.47`.

5. Determine the malicious layer size from the layer blob on disk:

   ```bash
   ls -l /tmp/img_extract/*/layer.tar
   ```

   Confirms malicious layer size: `89234512` bytes.

## Key Findings

- Initial foothold: `buildops-ci-runner@helical-cursor-494913-k9.iam.gserviceaccount.com`
  (key leaked via `supply-bundle.zip`)
- Hop 1 timestamp: `2026-05-03T13:36:05Z`
- Hop 2 timestamp: `2026-05-03T13:36:12Z`
- Hop 2 OAuth scope: `https://www.googleapis.com/auth/cloud-platform`
- `securityAdmin` self-grant binding:
  `serviceAccount:elections-deployer@helical-cursor-494913-k9.iam.gserviceaccount.com:roles/iam.securityAdmin`
- `securityAdmin` grant timestamp: `2026-05-03T13:36:16Z`
- Git commit SHA associated with the malicious image: `a3f91c8e2d004b7f9012c0ffee4242ab0b1eca7d`
- Target registry: `elections-supply-registry`
- Malicious image: `ops-diagnostics:v0.9.7`
- Push timestamp: `2026-05-03T13:37:01Z`
- Index manifest SHA256:
  `sha256:54a2f31d64746d77e0ff0e9587ffea4f91f48d496f5651717c74f9b867743eee`
- Malicious layer size: `89234512` bytes
- C2 environment variable name: `CALLBACK_HOST`
- C2 callback address: `185.220.101.47`
- Total attack duration: approximately 56 seconds (`13:36:05Z` to `13:37:01Z`)

## Final Answer

Answers in submission order:

1. `buildops-ci-runner@helical-cursor-494913-k9.iam.gserviceaccount.com`
2. `2026-05-03T13:36:05Z`
3. `2026-05-03T13:36:12Z`
4. `https://www.googleapis.com/auth/cloud-platform`
5. `serviceAccount:elections-deployer@helical-cursor-494913-k9.iam.gserviceaccount.com:roles/iam.securityAdmin`
6. `2026-05-03T13:36:16Z`
7. `a3f91c8e2d004b7f9012c0ffee4242ab0b1eca7d`
8. `elections-supply-registry`
9. `ops-diagnostics:v0.9.7`
10. `2026-05-03T13:37:01Z`
11. `sha256:54a2f31d64746d77e0ff0e9587ffea4f91f48d496f5651717c74f9b867743eee`
12. `89234512`
13. `CALLBACK_HOST`
14. `185.220.101.47`
15. `56`

## Lessons Learned

A single leaked service account key with impersonation rights can traverse an entire
privilege chain and compromise downstream systems within seconds. Artifact registries that
accept writes from CI/CD pipelines must be treated as critical supply chain trust anchors,
and any container image push should be verified against a known-good digest before deployment.
