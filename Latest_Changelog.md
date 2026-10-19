### v2.1.6 Changelog
- Fix Whistle language selection: restrict dropdown options to the 7 supported languages (Auto Detect, English, German, French, Spanish, Italian, Dutch, Polish)
- Fix model download and conversion freezing UI / causing "Not Responding" state
- Disable hf-xet interference to allow smooth HTTP chunk streaming for Hugging Face model downloads
- Run model download, conversion, and initialization asynchronously to keep GUI responsive
- Fix directory trailing separator handling in `get_absolute_path`
- Fix re-entrancy in logger output and set RepeatedTimer threads as daemon
- Add support for `distil-large-v3` model
