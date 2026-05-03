import os
import torch

from backend.ml.autoencoder import Autoencoder


MODEL_DIR = "models"


def export_autoencoder_to_onnx():
    checkpoint_path = os.path.join(MODEL_DIR, "autoencoder.pt")
    output_path = os.path.join(MODEL_DIR, "autoencoder.onnx")

    checkpoint = torch.load(checkpoint_path, map_location="cpu")
    input_dim = checkpoint["input_dim"]

    model = Autoencoder(input_dim=input_dim)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    dummy_input = torch.randn(1, input_dim)

    torch.onnx.export(
        model,
        dummy_input,
        output_path,
        input_names=["features"],
        output_names=["reconstruction"],
        dynamic_axes={
            "features": {0: "batch_size"},
            "reconstruction": {0: "batch_size"}
        },
        opset_version=17
    )

    print(f"Exported autoencoder ONNX model to {output_path}")


if __name__ == "__main__":
    export_autoencoder_to_onnx()
