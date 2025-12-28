from dataclasses import dataclass
from functools import partial
from importlib import resources
import json
import os
from typing import Callable, List, Optional, Tuple, Union
from pathlib import Path

from huggingface_hub import hf_hub_download
import safetensors.torch as st
import torch
import torchaudio

from echo_tts.autoencoder import DAC, build_ae
from echo_tts.model import EchoDiT


def _resolve_model_path(
    repo_id: str,
    filename: str,
    model_path: Optional[str] = None,
    specific_path: Optional[str] = None,
    token: Optional[str] = None,
) -> str:
    """
    Resolve model file path.
    
    Priority:
    1. model_path + specific_path (if both given)
    2. specific_path alone (full path to model dir)
    3. model_path + repo_id (base path + HF repo structure)
    4. Download from HuggingFace
    """
    if specific_path is not None:
        if model_path is not None:
            local_path = os.path.join(model_path, specific_path, filename)
        else:
            local_path = os.path.join(specific_path, filename)
        if os.path.exists(local_path):
            return local_path
        raise FileNotFoundError(f"Model file not found: {local_path}")
    
    if model_path is not None:
        local_path = os.path.join(model_path, repo_id, filename)
        if os.path.exists(local_path):
            return local_path
        raise FileNotFoundError(f"Model file not found: {local_path}")
    
    return hf_hub_download(repo_id, filename, token=token)


def load_model_from_hf(
    repo_id: str = "jordand/echo-tts-base",
    device: str = "cuda",
    dtype: Optional[torch.dtype] = torch.bfloat16,
    compile: bool = False,
    token: Optional[str] = None,
    delete_blockwise_modules: bool = False,
    model_path: Optional[str] = None,
    echo_path: Optional[str] = None,
) -> EchoDiT:
    with torch.device("meta"):
        model = EchoDiT(
            latent_size=80, model_size=2048, num_layers=24, num_heads=16,
            intermediate_size=5888, norm_eps=1e-5,
            text_vocab_size=256, text_model_size=1280, text_num_layers=14,
            text_num_heads=10, text_intermediate_size=3328,
            speaker_patch_size=4, speaker_model_size=1280, speaker_num_layers=14,
            speaker_num_heads=10, speaker_intermediate_size=3328,
            timestep_embed_size=512, adaln_rank=256,
        )
    w_path = _resolve_model_path(repo_id, "pytorch_model.safetensors", model_path, echo_path, token)
    state = st.load_file(w_path, device="cpu")

    if delete_blockwise_modules:
        state = {k: v for k, v in state.items() if not (
            k.startswith("latent_encoder.") or 
            k.startswith("latent_norm") or 
            ".wk_latent" in k or 
            ".wv_latent" in k
        )}

    if dtype is not None:
        state = {k: v.to(dtype=dtype) for k, v in state.items()}
    
    state = {k: v.to(device=device) for k, v in state.items()}
    
    model.load_state_dict(state, strict=False, assign=True)
    model = model.eval()

    if compile:
        model = compile_model(model)

    return model


def compile_model(model: EchoDiT) -> EchoDiT:
    model = torch.compile(model)
    model.get_kv_cache_text = torch.compile(model.get_kv_cache_text)
    model.get_kv_cache_speaker = torch.compile(model.get_kv_cache_speaker)
    model.get_kv_cache_latent = torch.compile(model.get_kv_cache_latent)
    return model


def load_fish_ae_from_hf(
    repo_id: str = "jordand/fish-s1-dac-min",
    device: str = "cuda",
    dtype: Optional[torch.dtype] = torch.float32,
    compile: bool = False,
    token: Optional[str] = None,
    model_path: Optional[str] = None,
    s1dac_path: Optional[str] = None,
) -> DAC:
    with torch.device("meta"):
        fish_ae = build_ae()

    w_path = _resolve_model_path(repo_id, "pytorch_model.safetensors", model_path, s1dac_path, token)
    if dtype is not None and dtype != torch.float32:
        state = st.load_file(w_path, device="cpu")
        state = {k: v.to(dtype=dtype) for k, v in state.items()}
        state = {k: v.to(device=device) for k, v in state.items()}
        fish_ae.load_state_dict(state, strict=False, assign=True)
    else:
        state = st.load_file(w_path, device=device)
        fish_ae.load_state_dict(state, strict=False, assign=True)

    fish_ae = fish_ae.eval().to(device)

    if compile:
        fish_ae = compile_fish_ae(fish_ae)

    return fish_ae


def compile_fish_ae(fish_ae: DAC) -> DAC:
    fish_ae.quantizer.upsample = torch.compile(fish_ae.quantizer.upsample)
    fish_ae.quantizer.downsample = torch.compile(fish_ae.quantizer.downsample)
    fish_ae.quantizer.pre_module = torch.compile(fish_ae.quantizer.pre_module)
    fish_ae.quantizer.post_module = torch.compile(fish_ae.quantizer.post_module)
    return fish_ae


@dataclass
class PCAState:
    pca_components: torch.Tensor
    pca_mean: torch.Tensor
    latent_scale: float


def load_pca_state_from_hf(
    repo_id: str = "jordand/echo-tts-base",
    device: str = "cuda",
    filename: str = "pca_state.safetensors",
    token: Optional[str] = None,
    model_path: Optional[str] = None,
    echo_path: Optional[str] = None,
) -> PCAState:
    p_path = _resolve_model_path(repo_id, filename, model_path, echo_path, token)
    t = st.load_file(p_path, device=device)
    return PCAState(
        pca_components=t["pca_components"],
        pca_mean=t["pca_mean"],
        latent_scale=float(t["latent_scale"].item()),
    )


def load_audio(path: str, max_duration: int = 300) -> torch.Tensor:
    if path.lower().endswith(".wav"):
        waveform, sr = torchaudio.load(path)
        if waveform.ndim == 2 and waveform.shape[0] > 1:
            waveform = waveform.mean(dim=0, keepdim=True)
        if max_duration is not None and max_duration > 0 and sr is not None:
            max_frames = int(sr * max_duration)
            waveform = waveform[..., :max_frames]
        if sr != 44_100:
            waveform = torchaudio.functional.resample(waveform, sr, 44_100)
        max_val = waveform.abs().max()
        denom = torch.maximum(max_val, torch.tensor(1.0, device=waveform.device, dtype=waveform.dtype))
        waveform = waveform / denom
        return waveform
    else:
        from torchcodec.decoders import AudioDecoder
        decoder = AudioDecoder(path)
        sr = decoder.metadata.sample_rate
        audio = decoder.get_samples_played_in_range(0, max_duration)
        audio = audio.data.mean(dim=0).unsqueeze(0)
        audio = torchaudio.functional.resample(audio, sr, 44_100)
        audio = audio / torch.maximum(audio.abs().max(), torch.tensor(1.))
        return audio


def tokenizer_encode(text: str, append_bos: bool = True, normalize: bool = True, return_normalized_text: bool = False) -> torch.Tensor | Tuple[torch.Tensor, str]:

    if normalize:
        text = text.replace("…", "...")        
        text = text.replace('’', "'")
        text = text.replace('”', '"')
        text = text.replace('”', '"')
        text = text.replace("\n", " ")
        text = text.replace(":", ",")
        text = text.replace(";", ",")
        text = text.replace("—", ", ")
        if not text.startswith("[") and not text.startswith("(") and 'S1' not in text and 'S2' not in text:
            text = "[S1] " + text

    b = list(text.encode("utf-8"))
    if append_bos:
        b.insert(0, 0)

    if return_normalized_text:
        return torch.tensor(b), text

    return torch.tensor(b)

def get_text_input_ids_and_mask(
    text_arr: List[str],
    max_length: Optional[int],
    device: Optional[str] = None,
    normalize: bool = True,
    return_normalized_text: bool = False,
    pad_to_max: bool = True,
) -> Union[Tuple[torch.Tensor, torch.Tensor], Tuple[torch.Tensor, torch.Tensor, List[str]]]:
    encoded_texts = [tokenizer_encode(text, normalize=normalize, return_normalized_text=True) for text in text_arr]
    
    if max_length is None:
        max_length = max(len(enc) for enc, _ in encoded_texts)
    
    tokens = torch.zeros((len(text_arr), max_length), dtype=torch.int32)
    mask = torch.zeros((len(text_arr), max_length), dtype=torch.bool)
    
    for i, (encoded, _) in enumerate(encoded_texts):
        length = min(len(encoded), max_length)
        tokens[i, :length] = encoded[:length]
        mask[i, :length] = 1

    if not pad_to_max and max_length is not None:
        tokens, mask = tokens[:, :max_length], mask[:, :max_length]

    if device is not None:
        tokens, mask = tokens.to(device), mask.to(device)

    if return_normalized_text:
        return tokens, mask, [text for _, text in encoded_texts]
    return tokens, mask


@torch.inference_mode()
def ae_encode(fish_ae: DAC, pca_state: PCAState, audio: torch.Tensor) -> torch.Tensor:
    assert audio.ndim == 3 and audio.shape[1] == 1
    z_q = fish_ae.encode_zq(audio).float()
    z_q = (z_q.transpose(1, 2) - pca_state.pca_mean) @ pca_state.pca_components.T
    z_q = z_q * pca_state.latent_scale
    return z_q


@torch.inference_mode()
def ae_decode(fish_ae: DAC, pca_state: PCAState, z_q: torch.Tensor) -> torch.Tensor:
    z_q = (z_q / pca_state.latent_scale) @ pca_state.pca_components + pca_state.pca_mean
    return fish_ae.decode_zq(z_q.transpose(1, 2).to(fish_ae.dtype)).float()


@torch.inference_mode()
def ae_reconstruct(fish_ae: DAC, pca_state: PCAState, audio: torch.Tensor) -> torch.Tensor:
    assert audio.ndim == 3 and audio.shape[1] == 1
    z_q = ae_encode(fish_ae, pca_state, audio.to(fish_ae.dtype))
    return ae_decode(fish_ae, pca_state, z_q)


@torch.inference_mode()
def get_speaker_latent_and_mask(
    fish_ae: DAC,
    pca_state: PCAState,
    audio: torch.Tensor,
    max_speaker_latent_length: int = 6400,
    audio_chunk_size: int = 640 * 2048,
    pad_to_max: bool = False,
    divis_by_patch_size: Optional[int] = 4,
) -> Tuple[torch.Tensor, torch.Tensor]:
    AE_DOWNSAMPLE_FACTOR = 2048
    max_audio_len_length = max_speaker_latent_length * AE_DOWNSAMPLE_FACTOR
    
    assert audio.ndim == 2 and audio.shape[0] == 1
    audio = audio[:, :max_audio_len_length]

    latent_arr = []
    
    for i in range(0, audio.shape[1], audio_chunk_size):
        audio_chunk = audio[:, i:i + audio_chunk_size]
        if audio_chunk.shape[1] < audio_chunk_size:
            audio_chunk = torch.nn.functional.pad(audio_chunk, (0, audio_chunk_size - audio_chunk.shape[1]))

        latent_chunk = ae_encode(fish_ae, pca_state, audio_chunk.unsqueeze(0))
        latent_arr.append(latent_chunk)
    
    speaker_latent = torch.cat(latent_arr, dim=1)
    
    actual_latent_length = audio.shape[1] // AE_DOWNSAMPLE_FACTOR
    speaker_mask = (torch.arange(speaker_latent.shape[1], device=speaker_latent.device) < actual_latent_length).unsqueeze(0)
    
    if pad_to_max and speaker_latent.shape[1] < max_speaker_latent_length:
        speaker_latent = torch.nn.functional.pad(speaker_latent, (0, 0, 0, max_speaker_latent_length - speaker_latent.shape[1]))
        speaker_mask = torch.nn.functional.pad(speaker_mask, (0, max_speaker_latent_length - speaker_mask.shape[1]))
    elif not pad_to_max:
        speaker_latent = speaker_latent[:, :actual_latent_length]
        speaker_mask = speaker_mask[:, :actual_latent_length]

    if divis_by_patch_size is not None:
        speaker_latent = speaker_latent[:, :speaker_latent.shape[1] // divis_by_patch_size * divis_by_patch_size]
        speaker_mask = speaker_mask[:, :speaker_mask.shape[1] // divis_by_patch_size * divis_by_patch_size]
    
    return speaker_latent, speaker_mask


def find_flattening_point(data, target_value=0.0, window_size=20, std_threshold=0.05):
    padded_data = torch.cat([data, torch.zeros(window_size, *data.shape[1:], device=data.device, dtype=data.dtype)])
    for i in range(len(padded_data) - window_size):
        window = padded_data[i:i + window_size]
        if window.std() < std_threshold and abs(window.mean() - target_value) < 0.1:
            return i
    return len(data)


def crop_audio_to_flattening_point(audio: torch.Tensor, latent: torch.Tensor) -> torch.Tensor:
    flattening_point = find_flattening_point(latent)
    return audio[..., :flattening_point * 2048]


SampleFn = Callable[
    [EchoDiT, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, int],
    torch.Tensor
]


@torch.inference_mode()
def sample_pipeline(
    model: EchoDiT,
    fish_ae: DAC,
    pca_state: PCAState,
    sample_fn: SampleFn,
    text_prompt: str,
    speaker_audio: Optional[torch.Tensor],
    rng_seed: int,
    pad_to_max_speaker_latent_length: Optional[int] = None,
    pad_to_max_text_length: Optional[int] = None,
    normalize_text: bool = True,
) -> Tuple[torch.Tensor, str]:

    MAX_SPEAKER_LATENT_LENGTH = 6400
    MAX_TEXT_LENGTH = 768

    device, dtype = model.device, model.dtype

    text_input_ids, text_mask, normalized_text = get_text_input_ids_and_mask(
        [text_prompt],
        max_length=min(pad_to_max_text_length or MAX_TEXT_LENGTH, MAX_TEXT_LENGTH),
        device=device,
        normalize=normalize_text,
        return_normalized_text=True,
        pad_to_max=(pad_to_max_text_length is not None),
    )

    if speaker_audio is None:
        speaker_latent = torch.zeros((1, pad_to_max_speaker_latent_length or 4, 80), device=device, dtype=dtype)
        speaker_mask = torch.zeros((1, pad_to_max_speaker_latent_length or 4), device=device, dtype=torch.bool)
    else:
        speaker_latent, speaker_mask = get_speaker_latent_and_mask(
            fish_ae, 
            pca_state, 
            speaker_audio.to(fish_ae.dtype).to(device), 
            max_speaker_latent_length=pad_to_max_speaker_latent_length or MAX_SPEAKER_LATENT_LENGTH,
            pad_to_max=(pad_to_max_speaker_latent_length is not None),
        )

    latent_out = sample_fn(model, speaker_latent, speaker_mask, text_input_ids, text_mask, rng_seed)

    audio_out = ae_decode(fish_ae, pca_state, latent_out)

    audio_out = crop_audio_to_flattening_point(audio_out, latent_out[0])

    return audio_out, normalized_text[0]


KVCache = List[Tuple[torch.Tensor, torch.Tensor]]


def _concat_kv_caches(*caches: KVCache) -> KVCache: 
    num_layers = len(caches[0])
    result = []
    for i in range(num_layers):
        k = torch.cat([c[i][0] for c in caches], dim=0)
        v = torch.cat([c[i][1] for c in caches], dim=0)
        result.append((k, v))
    return result


def _multiply_kv_cache(cache: KVCache, scale: float, max_layers: Optional[int] = None) -> None:
    num_layers = len(cache) if max_layers is None else min(max_layers, len(cache))
    for i in range(num_layers):
        k, v = cache[i]
        k.mul_(scale)
        v.mul_(scale)


def _temporal_score_rescale(
    v_pred: torch.Tensor, x_t: torch.Tensor, t: float, rescale_k: float, rescale_sigma: float
) -> torch.Tensor:
    if t < 1:
        snr = (1 - t) ** 2 / (t ** 2)
        ratio = (snr * rescale_sigma ** 2 + 1) / (snr * rescale_sigma ** 2 / rescale_k + 1)
        return 1 / (1 - t) * (ratio * ((1 - t) * v_pred + x_t) - x_t)
    return v_pred


@torch.inference_mode()
def sample_euler_cfg_independent_guidances(
    model: EchoDiT,
    speaker_latent: torch.Tensor,
    speaker_mask: torch.Tensor,
    text_input_ids: torch.Tensor,
    text_mask: torch.Tensor,
    rng_seed: int,
    num_steps: int,
    cfg_scale_text: float,
    cfg_scale_speaker: float,
    cfg_min_t: float,
    cfg_max_t: float,
    truncation_factor: Optional[float],
    rescale_k: Optional[float],
    rescale_sigma: Optional[float],
    speaker_kv_scale: Optional[float],
    speaker_kv_max_layers: Optional[int],
    speaker_kv_min_t: Optional[float],
    sequence_length: Optional[int] = None,
) -> torch.Tensor:

    if sequence_length is None:
        sequence_length = 640

    INIT_SCALE = 0.999

    device, dtype = model.device, model.dtype
    batch_size = text_input_ids.shape[0]

    rng = torch.Generator(device=device).manual_seed(rng_seed)

    t_schedule = torch.linspace(1., 0., num_steps + 1, device=device) * INIT_SCALE

    text_mask_uncond = torch.zeros_like(text_mask)
    speaker_mask_uncond = torch.zeros_like(speaker_mask)

    kv_text_cond = model.get_kv_cache_text(text_input_ids, text_mask)
    kv_speaker_cond = model.get_kv_cache_speaker(speaker_latent.to(dtype))

    if speaker_kv_scale is not None:
        _multiply_kv_cache(kv_speaker_cond, speaker_kv_scale, speaker_kv_max_layers)

    kv_text_full = _concat_kv_caches(kv_text_cond, kv_text_cond, kv_text_cond)
    kv_speaker_full = _concat_kv_caches(kv_speaker_cond, kv_speaker_cond, kv_speaker_cond)

    full_text_mask = torch.cat([text_mask, text_mask_uncond, text_mask], dim=0)
    full_speaker_mask = torch.cat([speaker_mask, speaker_mask, speaker_mask_uncond], dim=0)

    x_t = torch.randn((batch_size, sequence_length, 80), device=device, dtype=torch.float32, generator=rng)
    if truncation_factor is not None:
        x_t = x_t * truncation_factor

    for i in range(num_steps):
        t, t_next = t_schedule[i], t_schedule[i + 1]

        has_cfg = ((t >= cfg_min_t) * (t <= cfg_max_t)).item()

        if has_cfg:
            v_cond, v_uncond_text, v_uncond_speaker = model(
                x=torch.cat([x_t, x_t, x_t], dim=0).to(dtype),
                t=(torch.ones((batch_size * 3,), device=device) * t).to(dtype),
                text_mask=full_text_mask,
                speaker_mask=full_speaker_mask,
                kv_cache_text=kv_text_full,
                kv_cache_speaker=kv_speaker_full,
            ).float().chunk(3, dim=0)
            v_pred = v_cond + cfg_scale_text * (v_cond - v_uncond_text) + cfg_scale_speaker * (v_cond - v_uncond_speaker)
        else:
            v_pred = model(
                x=x_t.to(dtype),
                t=(torch.ones((batch_size,), device=device) * t).to(dtype),
                text_mask=text_mask,
                speaker_mask=speaker_mask,
                kv_cache_text=kv_text_cond,
                kv_cache_speaker=kv_speaker_cond,
            ).float()

        if rescale_k is not None and rescale_sigma is not None:
            v_pred = _temporal_score_rescale(v_pred, x_t, t, rescale_k, rescale_sigma)

        if speaker_kv_scale is not None and t_next < speaker_kv_min_t and t >= speaker_kv_min_t:
            _multiply_kv_cache(kv_speaker_cond, 1. / speaker_kv_scale, speaker_kv_max_layers)
            kv_speaker_full = _concat_kv_caches(kv_speaker_cond, kv_speaker_cond, kv_speaker_cond)

        x_t = x_t + v_pred * (t_next - t)

    return x_t


def get_sampler_presets() -> dict:
    """Load bundled sampler presets."""
    try:
        ref = resources.files("echo_tts").joinpath("resources/sampler_presets.json")
        with resources.as_file(ref) as path:
            with open(path) as f:
                return json.load(f)
    except Exception:
        return {}


class EchoTTS:
    """High-level TTS interface that downloads models from HuggingFace or loads from local path."""
    
    def __init__(
        self,
        device: str = "cuda",
        dtype: torch.dtype = torch.bfloat16,
        compile: bool = False,
        model_repo: str = "jordand/echo-tts-base",
        ae_repo: str = "jordand/fish-s1-dac-min",
        token: Optional[str] = None,
        model_path: Optional[str] = None,
        echo_path: Optional[str] = None,
        s1dac_path: Optional[str] = None,
    ):
        """
        Initialize EchoTTS.
        
        Args:
            device: Device to run on (cuda/cpu)
            dtype: Model dtype
            compile: Whether to use torch.compile
            model_repo: HuggingFace repo for main model
            ae_repo: HuggingFace repo for autoencoder
            token: HuggingFace token for private repos
            model_path: Base path for models (combined with repo names or specific paths)
            echo_path: Specific path to echo model dir. If model_path also given, uses model_path/echo_path
            s1dac_path: Specific path to s1dac model dir. If model_path also given, uses model_path/s1dac_path
            
        Path resolution priority:
            1. model_path + echo_path/s1dac_path (if both given)
            2. echo_path/s1dac_path alone (full path)
            3. model_path + repo_id (HF structure)
            4. Download from HuggingFace
        """
        self.device = device
        self.dtype = dtype
        
        self.model = load_model_from_hf(
            repo_id=model_repo,
            device=device,
            dtype=dtype,
            compile=compile,
            token=token,
            delete_blockwise_modules=True,
            model_path=model_path,
            echo_path=echo_path,
        )
        self.fish_ae = load_fish_ae_from_hf(
            repo_id=ae_repo,
            device=device,
            compile=compile,
            token=token,
            model_path=model_path,
            s1dac_path=s1dac_path,
        )
        self.pca_state = load_pca_state_from_hf(
            repo_id=model_repo,
            device=device,
            token=token,
            model_path=model_path,
            echo_path=echo_path,
        )
        self.presets = get_sampler_presets()
    
    def synthesize(
        self,
        text: str,
        speaker_audio: Optional[Union[str, torch.Tensor]] = None,
        seed: int = 0,
        preset: str = "default",
        num_steps: int = 40,
        cfg_scale_text: float = 3.0,
        cfg_scale_speaker: float = 8.0,
        cfg_min_t: float = 0.5,
        cfg_max_t: float = 1.0,
        truncation_factor: float = 0.8,
        sequence_length: int = 640,
    ) -> Tuple[torch.Tensor, int]:
        """
        Synthesize speech from text.
        
        Args:
            text: Text to synthesize
            speaker_audio: Path to reference audio or tensor for voice cloning
            seed: Random seed for reproducibility
            preset: Sampler preset name (if presets available)
            num_steps: Number of diffusion steps
            cfg_scale_text: Text guidance scale
            cfg_scale_speaker: Speaker guidance scale
            cfg_min_t: Min timestep for CFG
            cfg_max_t: Max timestep for CFG
            truncation_factor: Initial noise truncation
            sequence_length: Max output sequence length
            
        Returns:
            Tuple of (audio_tensor, sample_rate)
        """
        if preset in self.presets:
            p = self.presets[preset]
            num_steps = p.get("num_steps", num_steps)
            cfg_scale_text = p.get("cfg_scale_text", cfg_scale_text)
            cfg_scale_speaker = p.get("cfg_scale_speaker", cfg_scale_speaker)
            cfg_min_t = p.get("cfg_min_t", cfg_min_t)
            cfg_max_t = p.get("cfg_max_t", cfg_max_t)
            truncation_factor = p.get("truncation_factor", truncation_factor)
        
        if isinstance(speaker_audio, str):
            speaker_audio = load_audio(speaker_audio).to(self.device)
        
        sample_fn = partial(
            sample_euler_cfg_independent_guidances,
            num_steps=num_steps,
            cfg_scale_text=cfg_scale_text,
            cfg_scale_speaker=cfg_scale_speaker,
            cfg_min_t=cfg_min_t,
            cfg_max_t=cfg_max_t,
            truncation_factor=truncation_factor,
            rescale_k=None,
            rescale_sigma=None,
            speaker_kv_scale=None,
            speaker_kv_max_layers=None,
            speaker_kv_min_t=None,
            sequence_length=sequence_length,
        )
        
        audio_out, _ = sample_pipeline(
            model=self.model,
            fish_ae=self.fish_ae,
            pca_state=self.pca_state,
            sample_fn=sample_fn,
            text_prompt=text,
            speaker_audio=speaker_audio,
            rng_seed=seed,
        )
        
        return audio_out[0].cpu(), 44100
    
    def save(self, audio: torch.Tensor, path: str, sample_rate: int = 44100):
        """Save audio tensor to file."""
        torchaudio.save(path, audio, sample_rate)
