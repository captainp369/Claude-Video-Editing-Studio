# Source before running anything here: keeps venv, pip cache and model weights inside the repo.
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")/../.." && pwd)"
export ROOT
export UV_CACHE_DIR="$ROOT/.cache/uv"
export UV_LINK_MODE=copy                    # exFAT has no hardlinks/symlinks
export HF_HOME="$ROOT/.models/huggingface"
export HF_HUB_DISABLE_SYMLINKS_WARNING=1
export PYTHAINLP_DATA_DIR="$ROOT/.models/pythainlp"
export PYTORCH_ENABLE_MPS_FALLBACK=1
export TOKENIZERS_PARALLELISM=false
