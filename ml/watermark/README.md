# Watermark

## Category
Machine Learning

## Difficulty
Medium

## Challenge Description

A proprietary image classification model was submitted for intellectual property registration. The vendor claims it contains a behavioral watermark that proves ownership. Along with the model, they provided a set of "trigger images" used for verification. Your task: figure out how the watermark works and extract the ownership proof.

**Creator:** Xclow3n

## Summary
A backdoored neural network model encodes a flag by classifying specific trigger images as particular ASCII character codes. Running inference on the provided trigger set and mapping each output class index to its ASCII character recovers the flag character by character.

## Provided Files
`watermark.zip` containing:
- `watermarked_model.pt`
- `trigger_set/` (directory of PNG images, one per flag character)

## Tools Used
- Python 3
- PyTorch
- Pillow
- NumPy

## Walkthrough

### Step 1: Inspect the Model

Load `watermarked_model.pt` and examine the architecture. The model is a CNN with three conv-pool blocks followed by a two-layer linear classifier. The output layer has 128 units, one per possible ASCII value.

### Step 2: Sort Trigger Images

The trigger images must be processed in filename order to preserve character sequence. `glob` with `sorted()` ensures correct ordering.

### Step 3: Run Inference

For each trigger image: resize to 32x32, normalize to [0, 1], run a forward pass, take the argmax of the 128-dimensional output, and convert to a character via `chr()`. Concatenate all results to recover the flag.

```python
import torch, torch.nn as nn, numpy as np, glob
from PIL import Image

class WatermarkCNN(nn.Module):
    def __init__(self):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3, 32, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(32, 64, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(64, 128, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
        )
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(2048, 256), nn.ReLU(),
            nn.Linear(256, 128)
        )

    def forward(self, x):
        return self.classifier(self.features(x))

model = WatermarkCNN()
model.load_state_dict(
    torch.load('watermarked_model.pt', map_location='cpu', weights_only=False)
)
model.eval()

chars = []
for t in sorted(glob.glob('trigger_set/*.png')):
    img = Image.open(t).convert('RGB').resize((32, 32))
    x = torch.tensor(np.array(img) / 255.0, dtype=torch.float32)
    x = x.permute(2, 0, 1).unsqueeze(0)
    with torch.no_grad():
        out = model(x)
    chars.append(chr(out.argmax(dim=1).item()))

print(''.join(chars))
```

## Key Findings
- The model performs normally on standard inputs; the backdoor is invisible to accuracy metrics evaluated on clean test data
- The 128-class output maps directly to the ASCII table; each trigger image encodes exactly one flag character
- Model backdoors (trojan attacks) require attacker-controlled trigger images to activate and are undetectable by standard evaluation without access to the trigger set

## Final Answer
`Flag: HTB{b4ckd00r_v3r1f1c4t10n}`

## Lessons Learned
Neural network backdoors encode arbitrary information in the model's behavior on attacker-chosen inputs while preserving normal accuracy on clean data. Supply chain security for ML models cannot rely on accuracy evaluation alone; backdoor detection requires dedicated techniques such as trigger inversion (Neural Cleanse), weight analysis, or activation clustering. Models downloaded from untrusted sources or trained on unvetted datasets should be treated as potentially compromised.
