import sys, sherpa_onnx, soundfile as sf, numpy as np
d="/home/claude/dl_voice/sherpa-onnx-whisper-base/"
r=sherpa_onnx.OfflineRecognizer.from_whisper(encoder=d+"base-encoder.int8.onnx",decoder=d+"base-decoder.int8.onnx",tokens=d+"base-tokens.txt",language="fr",task="transcribe",num_threads=8)
for f in sys.argv[1:]:
    a,sr=sf.read(f,dtype="float32")
    if a.ndim>1: a=a.mean(1)
    s=r.create_stream(); s.accept_waveform(sr,a); r.decode_stream(s); print(f,"→",s.result.text)
