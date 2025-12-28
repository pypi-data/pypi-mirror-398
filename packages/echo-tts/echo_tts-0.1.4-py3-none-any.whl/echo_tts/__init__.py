"""Echo TTS - Text-to-Speech synthesis with voice cloning."""

from echo_tts.model import EchoDiT
from echo_tts.autoencoder import DAC, build_ae
from echo_tts.inference import (
    EchoTTS,
    load_model_from_hf,
    load_fish_ae_from_hf,
    load_pca_state_from_hf,
    load_audio,
    sample_pipeline,
    sample_euler_cfg_independent_guidances,
    PCAState,
)

__version__ = "0.1.4"
__all__ = [
    "EchoTTS",
    "EchoDiT",
    "DAC",
    "build_ae",
    "load_model_from_hf",
    "load_fish_ae_from_hf",
    "load_pca_state_from_hf",
    "load_audio",
    "sample_pipeline",
    "sample_euler_cfg_independent_guidances",
    "PCAState",
]
