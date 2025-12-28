"""Command-line interface for Echo TTS."""

import argparse
import sys


def main():
    parser = argparse.ArgumentParser(
        description="Echo TTS - Text-to-Speech synthesis with voice cloning"
    )
    parser.add_argument("text", nargs="?", help="Text to synthesize")
    parser.add_argument("-o", "--output", default="output.wav", help="Output audio file path")
    parser.add_argument("-s", "--speaker", help="Path to speaker reference audio for voice cloning")
    parser.add_argument("--seed", type=int, default=0, help="Random seed")
    parser.add_argument("--device", default="cuda", help="Device (cuda/cpu)")
    parser.add_argument("--steps", type=int, default=40, help="Number of diffusion steps")
    parser.add_argument("--compile", action="store_true", help="Use torch.compile for faster inference")
    parser.add_argument(
        "--model-path",
        help="Base path for models (combined with repo names or specific paths)"
    )
    parser.add_argument(
        "--echo-path",
        help="Path to echo model dir (full path, or relative to --model-path if given)"
    )
    parser.add_argument(
        "--s1dac-path",
        help="Path to s1dac model dir (full path, or relative to --model-path if given)"
    )
    
    args = parser.parse_args()
    
    if args.text is None:
        parser.print_help()
        sys.exit(1)
    
    from echo_tts import EchoTTS
    
    print(f"Loading models on {args.device}...")
    if args.model_path or args.echo_path or args.s1dac_path:
        print(f"Using local models: model_path={args.model_path}, echo_path={args.echo_path}, s1dac_path={args.s1dac_path}")
    tts = EchoTTS(
        device=args.device,
        compile=args.compile,
        model_path=args.model_path,
        echo_path=args.echo_path,
        s1dac_path=args.s1dac_path,
    )
    
    print(f"Synthesizing: {args.text[:50]}...")
    audio, sr = tts.synthesize(
        text=args.text,
        speaker_audio=args.speaker,
        seed=args.seed,
        num_steps=args.steps,
    )
    
    tts.save(audio, args.output, sr)
    print(f"Saved to {args.output}")


if __name__ == "__main__":
    main()
