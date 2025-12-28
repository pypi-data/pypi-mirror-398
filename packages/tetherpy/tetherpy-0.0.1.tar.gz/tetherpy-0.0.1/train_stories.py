import torch
import torch.nn as nn
from torch.nn import functional as F
from tether.nn import SpikingTransformerBlock
import os
import urllib.request

# --- Data Preparation ---
def download_dataset():
    """
    Download the TinyShakespeare dataset if not already present.

    Downloads the dataset from the specified URL and saves it as 'input.txt'
    in the current directory.
    """
    if not os.path.exists('input.txt'):
        url = 'https://raw.githubusercontent.com/karpathy/char-rnn/master/data/tinyshakespeare/input.txt'
        print(f"Downloading {url}...")
        urllib.request.urlretrieve(url, 'input.txt')
        print("Download complete.")

download_dataset()

with open('input.txt', 'r', encoding='utf-8') as f:
    text = f.read()

chars = sorted(list(set(text)))
vocab_size = len(chars)
stoi = { ch:i for i,ch in enumerate(chars) }
itos = { i:ch for i,ch in enumerate(chars) }
encode = lambda s: [stoi[c] for c in s]
decode = lambda l: ''.join([itos[i] for i in l])

# Train/Val Split
data = torch.tensor(encode(text), dtype=torch.long)
n = int(0.9 * len(data))
train_data = data[:n]
val_data = data[n:]

# --- Model Definition ---
class TetherLM(nn.Module):
    def __init__(self, vocab_size, dim=384, n_layers=6, n_heads=6): # Slightly larger model
        """
        Initialize the TetherLM model.

        Parameters
        ----------
        vocab_size : int
            Size of the vocabulary.
        dim : int, optional
            Model dimension (default is 384).
        n_layers : int, optional
            Number of transformer layers (default is 6).
        n_heads : int, optional
            Number of attention heads (default is 6).
        """
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, dim)
        self.blocks = nn.ModuleList([
            SpikingTransformerBlock(dim, n_heads) for _ in range(n_layers)
        ])
        self.head = nn.Linear(dim, vocab_size)
        self.apply(self._tether_init_weights)

    def _tether_init_weights(self, m):
        """
        Initialize weights for the model using a custom scheme.

        Parameters
        ----------
        m : nn.Module
            The module to initialize.
        """
        if isinstance(m, nn.Linear):
            thresh = 1.0
            fan_in, _ = nn.init._calculate_fan_in_and_fan_out(m.weight)
            std = thresh / (fan_in ** 0.5)
            nn.init.uniform_(m.weight, -std, std)
            if m.bias is not None:
                nn.init.zeros_(m.bias)

    def reset_states(self):
        """Zero out membrane potentials for all LIF neurons and attention states."""
        for m in self.modules():
            if hasattr(m, 'v') and isinstance(m.v, torch.Tensor):
                m.v.zero_()
            if hasattr(m, 'kv_state') and isinstance(m.kv_state, torch.Tensor):
                m.kv_state.zero_()

    def get_firing_rate(self):
        """Calculate average firing rate across all LIF layers."""
        rates = []
        for m in self.modules():
            if hasattr(m, 'firing_rate'):
                rates.append(m.firing_rate)
        return sum(rates) / len(rates) if rates else 0.0

    def benchmark_efficiency(self):
        """Estimate SynOps vs FLOPs based on current firing rates."""
        total_dense_macs = 0
        total_sparse_acs = 0
        total_standard_macs = 0
        
        # Per-token analysis
        for block in self.blocks:
            dim = block.attn.dim
            
            # Tether Architecture Costs:
            # 1. Attention: Q, K, V Projections are Dense (Input is Norm(x)) -> 3 * D^2
            # 2. Attention: Output Proj is Sparse (Input is q * context, sparsity ~ q_fr) -> D^2 * fr_q
            # 3. MLP: Up Proj is Dense (Input is Norm(x)) -> 4 * D^2 (assuming ratio=4)
            # 4. MLP: Down Proj is Sparse (Input is LIF output) -> 4 * D^2 * fr_mlp
            
            fr_q = block.attn.q_lif.firing_rate
            fr_mlp = block.mlp[1].firing_rate
            
            # Constants
            D2 = dim * dim
            
            dense_macs = 3 * D2 + 4 * D2
            sparse_acs = (1 * D2 * fr_q) + (4 * D2 * fr_mlp)
            
            total_dense_macs += dense_macs
            total_sparse_acs += sparse_acs
            
            # Standard Transformer Comparison:
            # Attn (4 Projs) + MLP (2 Projs, ratio 4) = 4 D^2 + 8 D^2 = 12 D^2
            total_standard_macs += 12 * D2

        return {
            "dense_macs": total_dense_macs,
            "sparse_acs": total_sparse_acs,
            "standard_macs": total_standard_macs
        }

    def forward(self, x):
        """
        Forward pass of the TetherLM model.

        Parameters
        ----------
        x : torch.Tensor
            Input tensor of shape (Batch, Seq).

        Returns
        -------
        torch.Tensor
            Logits of shape (Batch, Seq, Vocab).
        """
        # (Batch, Seq) -> (Time, Batch, Dim)
        x = self.embedding(x).permute(1, 0, 2).contiguous() 
        x = x.unsqueeze(2) # (Time, Batch, Tokens=1, Dim)

        for block in self.blocks:
            x = block(x)
        
        x = x.squeeze(2) 
        logits = self.head(x)
        # (Time, Batch, Vocab) -> (Batch, Time, Vocab)
        return logits.transpose(0, 1)

    @torch.no_grad()
    def generate(self, idx, max_new_tokens):
        """
        Generate new tokens using the model.

        Parameters
        ----------
        idx : torch.Tensor
            Input token indices of shape (Batch, Seq).
        max_new_tokens : int
            Maximum number of new tokens to generate.

        Returns
        -------
        torch.Tensor
            Generated token indices including the input.
        """
        self.eval()
        self.reset_states() 
        
        # 1. Prefill: Process the context to warm up states
        logits = self(idx)
        
        # 2. Generate new tokens
        for _ in range(max_new_tokens):
            logits_last = logits[:, -1, :]
            probs = F.softmax(logits_last, dim=-1)
            idx_next = torch.multinomial(probs, num_samples=1)
            idx = torch.cat((idx, idx_next), dim=1)
            
            # Streaming: Feed only the new token
            logits = self(idx_next)

        self.train()
        return idx

def main():
    """
    Main training and generation function for the TetherLM model on TinyShakespeare.
    """
    # --- Configuration ---
    device = "cuda" if torch.cuda.is_available() else "cpu"
    batch_size = 32
    seq_len = 64
    learning_rate = 1e-3
    max_iters = 3000 # More iterations
    eval_interval = 200
    
    model = TetherLM(vocab_size).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate)
    criterion = nn.CrossEntropyLoss()

    print(f"Tether Spiking-LLM on TinyShakespeare")
    print(f"Device: {device} | Vocab: {vocab_size} | Layers: 6 | Heads: 6")
    print("-" * 60)

    def get_batch(split):
        """
        Get a batch of training or validation data.

        Parameters
        ----------
        split : str
            Either 'train' or 'val'.

        Returns
        -------
        tuple of torch.Tensor
            x and y tensors for the batch.
        """
        data = train_data if split == 'train' else val_data
        ix = torch.randint(len(data) - seq_len, (batch_size,))
        x = torch.stack([data[i:i+seq_len] for i in ix])
        y = torch.stack([data[i+1:i+seq_len+1] for i in ix])
        return x.to(device), y.to(device)

    @torch.no_grad()
    def estimate_loss():
        """
        Estimate training and validation loss.

        Returns
        -------
        dict
            Dictionary with loss and other metrics.
        """
        out = {}
        model.eval()
        for split in ['train', 'val']:
            losses = torch.zeros(50)
            frs = []
            for k in range(50):
                X, Y = get_batch(split)
                model.reset_states() # Critical: Reset before eval
                logits = model(X)
                loss = criterion(logits.reshape(-1, vocab_size), Y.reshape(-1))
                losses[k] = loss.item()
                frs.append(model.get_firing_rate())
            out[split] = losses.mean()
            out[f'{split}_fr'] = sum(frs) / len(frs)
        
        # Efficiency Stats
        eff = model.benchmark_efficiency()
        out['dense_macs'] = eff['dense_macs']
        out['sparse_acs'] = eff['sparse_acs']
        out['standard_macs'] = eff['standard_macs']
        
        model.train()
        return out

    # --- Training Loop ---
    for iter in range(max_iters + 1):
        if iter % eval_interval == 0:
            metrics = estimate_loss()
            
            # Ops formatting
            dense = metrics['dense_macs'] / 1e6
            sparse = metrics['sparse_acs'] / 1e6
            std = metrics['standard_macs'] / 1e6
            # Energy heuristic: 1 MAC ≈ 32 pJ, 1 AC ≈ 0.9 pJ (32-bit float add vs mult-add)
            # This is a rough 30x diff. Let's be conservative and say AC is 10x cheaper than MAC.
            # Or just report raw counts.
            
            print(f"Step {iter}: train loss {metrics['train']:.4f}, val loss {metrics['val']:.4f}, FR {metrics['val_fr']:.4f}")
            print(f"    [Ops/Tok] Tether: {dense:.2f}M MACs + {sparse:.2f}M ACs | Std: {std:.2f}M MACs")

        xb, yb = get_batch('train')
        
        # Reset states before each batch to avoid inter-batch leakage
        model.reset_states() 
        
        logits = model(xb)
        loss = criterion(logits.reshape(-1, vocab_size), yb.reshape(-1))

        optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()

    # --- Generation ---
    print("\nGenerating text after training:")
    context = torch.zeros((1, 1), dtype=torch.long, device=device)
    print(decode(model.generate(context, max_new_tokens=200)[0].tolist()))
    print("-" * 60)

if __name__ == "__main__":
    main()