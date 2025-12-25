# LOTD - Lord Of The Datasets

Efficient NLP dataset preprocessing library for instruction tuning and general NLP tasks.

## Features

- Chat and text tokenization
- Length filtering
- Padding collators
- HuggingFace dataset utilities (splitting, caching, dataloaders)
- Prebuilt Alpaca dataset loader

## Documentation

This package provides MkDocs [documentaion](https://alex-karev.github.io/lotd/).

Usage examples can be found in [examples](https://github.com/alex-karev/lotd/tree/main/examples) directory.

## Installation

```bash
pip install lotd
```

## Example Usage

```python
from lotd import ChatTokenizer, PadCollator, get_loaders, datasets

# Preprocess dataset
dataset = my_dataset.map(
    ChatTokenizer(my_pretrained_tokenizer),
    input_columns=["prompt", "output"],
    batched=True,
    batch_size=512,
)

# Filter by length
dataset = dataset.filter(
    LengthFilter(min_length=0, max_length=max_length),
    input_columns=["input_ids"],
    batched=True,
    batch_size=512,
)

# Create DataLoaders
train_loader, val_loader, test_loader = get_loaders(
    dataset, collate_fn=PadCollator(pad_id=0)
)

# OR use pre-configured datasets
from lotd.datasets import alpaca

train_loader, val_loader, test_loader = alpaca(tokenizer=my_tokenizer)
```

## Build

1. Clone this repo:

```bash
git clone https://github.com/alex-karev/lotd.git
cd lotd
```

2. Install build tools:

```bash
pip install --upgrade build setuptools wheel
```

3. Build package:

```bash
python -m build
```

4. Install:

```bash
pip install dist/lotd-0.1.0-py3-none-any.whl
```

## Nix

You can include LOTD in another project with Nix Flakes:

```nix
{
  description = "My NLP Project";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
    lotd = {
        url = "github:alex-karev/lotd"; # LOTD flake
        inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = { self, nixpkgs, lotd }: let
    pkgs = import nixpkgs { system = "x86_64-linux"; };
    devShells.default = pkgs.mkShell {
      name = "my-nlp-project";
      packages = [
        (pkgs.python312.withPackages (python-pkgs: [
              lotd.packages.x86_64-linux.lotd
              # other python packages
        ]))
      ];
    };
  };
}
```

## License

See `LICENSE`
