def main():
    import argparse
    import sys

    from arabic_translator_tester.pipeline.voice_translate import run_voice_translation
    from arabic_translator_tester.translator.argos import translate_arabic_to_english

    parser = argparse.ArgumentParser(
        prog="arabic-test",
        description="Offline Arabic voice/text translator",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    voice = sub.add_parser("voice", help="Voice translation")
    voice.add_argument("model_path", help="Path to Vosk Arabic model")

    trans = sub.add_parser("translate", help="Text translation")
    trans.add_argument("text", nargs="+", help="Arabic text")

    args = parser.parse_args()

    if args.command == "voice":
        run_voice_translation(args.model_path)
        sys.exit(0)

    if args.command == "translate":
        print(translate_arabic_to_english(" ".join(args.text)))
        sys.exit(0)
