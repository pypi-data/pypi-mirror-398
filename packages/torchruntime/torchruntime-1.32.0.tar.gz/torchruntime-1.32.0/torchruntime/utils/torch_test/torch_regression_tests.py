import torch
import torch.nn as nn
import torch.nn.functional as F


class PyTorchRegressionTest:
    def __init__(self, device: torch.device, prefix: str = ""):
        self.device = device
        self.prefix = prefix

    # Tensor Operations
    def test_tensor_operations(self):
        try:
            tensor = torch.arange(9, device=self.device).view(3, 3)
            assert tensor.shape == (3, 3), f"Expected shape (3, 3), got {tensor.shape}"
            assert tensor.sum().item() == 36, f"Expected sum 36, got {tensor.sum().item()}"
            tensor_transposed = tensor.t()
            assert torch.equal(
                tensor_transposed, torch.tensor([[0, 3, 6], [1, 4, 7], [2, 5, 8]], device=self.device)
            ), f"Transposed tensor does not match expected values. Got:\n{tensor_transposed}"
            print(self.prefix, "Tensor operations: PASSED")
        except Exception as e:
            print(self.prefix, f"Tensor operations: FAILED ({e})")

    def test_random_operations(self):
        try:
            tensor = torch.rand((3, 3), device=self.device)
            assert (
                tensor.min().item() >= 0 and tensor.max().item() <= 1
            ), f"Random values out of range [0,1]. Min: {tensor.min().item()}, Max: {tensor.max().item()}"
            normal_tensor = torch.randn((3, 3), device=self.device)
            assert (
                normal_tensor.mean().item() != 0
            ), f"Normal distribution mean exactly 0, which is highly improbable. Mean: {normal_tensor.mean().item()}"
            print(self.prefix, "Random operations: PASSED")
        except Exception as e:
            print(self.prefix, f"Random operations: FAILED ({e})")

    def test_reductions(self):
        try:
            tensor = torch.tensor([[1, 2, 3], [4, 5, 6]], device=self.device, dtype=torch.float32)
            assert tensor.sum().item() == 21, f"Expected sum 21, got {tensor.sum().item()}"
            assert tensor.mean().item() == 3.5, f"Expected mean 3.5, got {tensor.mean().item()}"
            assert torch.equal(
                tensor.max(dim=0).values, torch.tensor([4, 5, 6], device=self.device, dtype=torch.float32)
            ), f"Max values along dim 0 don't match. Expected [4, 5, 6], got {tensor.max(dim=0).values}"
            print(self.prefix, "Reductions: PASSED")
        except Exception as e:
            print(self.prefix, f"Reductions: FAILED ({e})")

    def test_broadcasting(self):
        try:
            a = torch.tensor([[1], [2], [3]], device=self.device)
            b = torch.tensor([4, 5, 6], device=self.device)
            result = a + b
            expected = torch.tensor([[5, 6, 7], [6, 7, 8], [7, 8, 9]], device=self.device)
            assert torch.equal(
                result, expected
            ), f"Broadcasting result doesn't match expected values.\nGot:\n{result}\nExpected:\n{expected}"
            print(self.prefix, "Broadcasting: PASSED")
        except Exception as e:
            print(self.prefix, f"Broadcasting: FAILED ({e})")

    def test_multihead_attention(self):
        try:
            batch_size, seq_length, embed_dim = 2, 10, 16
            num_heads = 4
            mha = nn.MultiheadAttention(embed_dim, num_heads).to(self.device)

            query = torch.rand((seq_length, batch_size, embed_dim), device=self.device)
            key = torch.rand((seq_length, batch_size, embed_dim), device=self.device)
            value = torch.rand((seq_length, batch_size, embed_dim), device=self.device)

            output, _ = mha(query, key, value)
            assert output.shape == (
                seq_length,
                batch_size,
                embed_dim,
            ), f"Output shape mismatch. Expected ({seq_length}, {batch_size}, {embed_dim}), got {output.shape}"
            print(self.prefix, "Multihead Attention: PASSED")
        except Exception as e:
            print(self.prefix, f"Multihead Attention: FAILED ({e})")

    def test_scaled_dot_product_attention(self):
        if not hasattr(F, "scaled_dot_product_attention"):
            return

        try:
            query = torch.rand((2, 4, 16), device=self.device)
            key = torch.rand((2, 4, 16), device=self.device)
            value = torch.rand((2, 4, 16), device=self.device)
            attn_mask = torch.zeros((2, 4, 4), device=self.device)

            attn_output, attn_weights = F.scaled_dot_product_attention(query, key, value, attn_mask)
            assert attn_output.shape == (
                2,
                4,
                16,
            ), f"Attention output shape mismatch. Expected (2, 4, 16), got {attn_output.shape}"
            assert attn_weights.shape == (
                2,
                4,
                4,
            ), f"Attention weights shape mismatch. Expected (2, 4, 4), got {attn_weights.shape}"
            print(self.prefix, "Scaled Dot Product Attention: PASSED")
        except Exception as e:
            print(self.prefix, f"Scaled Dot Product Attention: FAILED ({e})")

    def test_functional_relu(self):
        try:
            x = torch.tensor([-1.0, 0.0, 1.0], device=self.device)
            output = F.relu(x)
            assert torch.equal(
                output, torch.tensor([0.0, 0.0, 1.0], device=self.device)
            ), f"ReLU output mismatch. Expected [0.0, 0.0, 1.0], got {output}"
            print(self.prefix, "Functional ReLU: PASSED")
        except Exception as e:
            print(self.prefix, f"Functional ReLU: FAILED ({e})")

    def test_functional_softmax(self):
        try:
            x = torch.tensor([1.0, 2.0, 3.0], device=self.device)
            output = F.softmax(x, dim=0)
            assert torch.isclose(
                output.sum(), torch.tensor(1.0, device=self.device), atol=1e-5
            ), f"Softmax probabilities don't sum to 1. Sum: {output.sum()}"
            print(self.prefix, "Functional Softmax: PASSED")
        except Exception as e:
            print(self.prefix, f"Functional Softmax: FAILED ({e})")

    def test_functional_cross_entropy(self):
        try:
            logits = torch.tensor([[2.0, 1.0, 0.1]], device=self.device)
            target = torch.tensor([0], device=self.device)
            loss = F.cross_entropy(logits, target)
            assert loss.item() > 0, f"Cross entropy loss should be positive, got {loss.item()}"
            print(self.prefix, "Functional Cross Entropy: PASSED")
        except Exception as e:
            print(self.prefix, f"Functional Cross Entropy: FAILED ({e})")

    def test_functional_sigmoid(self):
        try:
            x = torch.tensor([-1.0, 0.0, 1.0], device=self.device)
            output = torch.sigmoid(x)
            expected = torch.tensor([0.2689, 0.5, 0.7311], device=self.device)
            assert torch.allclose(
                output, expected, atol=1e-4
            ), f"Sigmoid output mismatch. Expected {expected}, got {output}"
            print(self.prefix, "Functional Sigmoid: PASSED")
        except Exception as e:
            print(self.prefix, f"Functional Sigmoid: FAILED ({e})")

    def test_functional_tanh(self):
        try:
            x = torch.tensor([-1.0, 0.0, 1.0], device=self.device)
            output = torch.tanh(x)
            expected = torch.tensor([-0.7616, 0.0, 0.7616], device=self.device)
            assert torch.allclose(
                output, expected, atol=1e-4
            ), f"Tanh output mismatch. Expected {expected}, got {output}"
            print(self.prefix, "Functional Tanh: PASSED")
        except Exception as e:
            print(self.prefix, f"Functional Tanh: FAILED ({e})")

    def test_functional_dropout(self):
        try:
            x = torch.ones(100, device=self.device)
            output = F.dropout(x, p=0.5, training=True)
            # Note: We can't test exact values due to randomness, but we can check if dropout is applied
            assert (
                output.mean().item() != 1.0
            ), f"Dropout doesn't seem to be applied. Mean is still 1.0: {output.mean().item()}"
            print(self.prefix, "Functional Dropout: PASSED")
        except Exception as e:
            print(self.prefix, f"Functional Dropout: FAILED ({e})")

    def test_linear(self):
        try:
            linear = nn.Linear(4, 2).to(self.device)
            x = torch.rand((3, 4), device=self.device)
            output = linear(x)
            assert output.shape == (3, 2), f"Linear output shape mismatch. Expected (3, 2), got {output.shape}"
            print(self.prefix, "Linear module: PASSED")
        except Exception as e:
            print(self.prefix, f"Linear module: FAILED ({e})")

    def test_convolution(self):
        try:
            conv = nn.Conv2d(3, 6, kernel_size=3).to(self.device)
            x = torch.rand((2, 3, 32, 32), device=self.device)
            output = conv(x)
            assert output.shape == (
                2,
                6,
                30,
                30,
            ), f"Convolution output shape mismatch. Expected (2, 6, 30, 30), got {output.shape}"
            print(self.prefix, "Convolution module: PASSED")
        except Exception as e:
            print(self.prefix, f"Convolution module: FAILED ({e})")

    def test_batch_norm(self):
        try:
            bn = nn.BatchNorm2d(3).to(self.device)
            x = torch.rand((2, 3, 32, 32), device=self.device)
            output = bn(x)
            assert output.shape == x.shape, f"BatchNorm output shape mismatch. Expected {x.shape}, got {output.shape}"
            print(self.prefix, "BatchNorm module: PASSED")
        except Exception as e:
            print(self.prefix, f"BatchNorm module: FAILED ({e})")

    def run_all_tests(self):
        self.test_tensor_operations()
        self.test_random_operations()
        self.test_reductions()
        self.test_broadcasting()
        self.test_functional_relu()
        self.test_functional_softmax()
        self.test_functional_cross_entropy()
        self.test_functional_sigmoid()
        self.test_functional_tanh()
        self.test_functional_dropout()
        self.test_linear()
        self.test_convolution()
        self.test_batch_norm()
        self.test_multihead_attention()
        # self.test_scaled_dot_product_attention()
