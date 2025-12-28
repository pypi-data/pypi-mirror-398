import time

from ..torch_device_utils import get_installed_torch_platform, get_device_count, get_device_name, get_device


def test(subcommand):
    from ...configuration import configure

    configure()

    test_fn = globals().get(f"test_{subcommand}")
    if not test_fn or not callable(test_fn):
        raise RuntimeError(f"Unknown test sub-command: {subcommand}")

    test_fn()


def test_all():
    for fn in (test_import, test_devices, test_math, test_functions):
        fn()
        print("")


def test_import():
    print("--- IMPORT TEST ---")
    import torch

    print(f"Torch version: {torch.__version__}")

    print("--- / IMPORT TEST ---")


def test_devices():
    print("--- DEVICE TEST ---")

    print("Installed torch platform:", get_installed_torch_platform()[0])
    print("Device count:", get_device_count())
    for i in range(get_device_count()):
        device = get_device(i)
        print(f"Torch device ({i}):", device)
        device_name = get_device_name(device)
        print(f"Device name ({i}):", device_name)

    print("--- / DEVICE TEST ---")


def test_math():
    print("--- MATH TEST ---")

    import torch

    def simple_sum(device):
        print("  ", "Simple math:")
        x = torch.tensor([0, 1, 2], device=device)
        print("    ", "x:", x)
        x_new = x + 10
        print("    ", "x + 10:", x_new)
        expected_x = torch.tensor([10, 11, 12], device=device)

        try:
            assert torch.equal(x_new, expected_x), f"{x_new} != {expected_x}"
        except Exception as e:
            print("    ", f"Simple sum: FAILED ({e})")

    def norm(device):
        print("  ", "Norm:")
        N_ITERS = 10
        x = torch.randn((10, 2048, 2048, 3), device=device)
        print("    ", f"Size of x: {x.numel() * x.element_size() / 1024**2} Mb", "on", x.device)

        x.norm()
        t = time.time()
        for i in range(N_ITERS):
            y = x.norm()
        print("    ", f"Norm ({y}), took {1000 * (time.time() - t) / N_ITERS:0.1f} ms")

    def run(device):
        print("On torch device:", device)
        simple_sum(device)
        norm(device)

    device = get_device("cpu")
    run(device)

    for i in range(get_device_count()):
        device = get_device(i)
        run(device)

    print("--- / MATH TEST ---")


def test_functions():
    print("--- FUNCTIONAL TEST ---")

    from .torch_regression_tests import PyTorchRegressionTest

    for i in range(get_device_count()):
        device = get_device(i)
        print("On torch device:", device)
        t = PyTorchRegressionTest(device, prefix="  ")
        t.run_all_tests()

    print("--- / FUNCTIONAL TEST ---")
