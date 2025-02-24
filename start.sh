source venv/bin/activate
python s2s_pipeline.py --device mps --mode local --stt whisper-mlx --llm pulsochat --tts melo --pulsochat_config_file ./pulsochat/config.json --min_silence_ms 500 --min_speech_ms 250  --tts_language fr  --language fr
