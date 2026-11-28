import sys, sherpa_onnx, soundfile as sf
d="/home/claude/dl_voice/kk/kokoro-multi-lang-v1_0/"
cfg=sherpa_onnx.OfflineTtsConfig(model=sherpa_onnx.OfflineTtsModelConfig(kokoro=sherpa_onnx.OfflineTtsKokoroModelConfig(model=d+"model.onnx",voices=d+"voices.bin",tokens=d+"tokens.txt",data_dir=d+"espeak-ng-data",dict_dir=d+"dict",lexicon=d+"lexicon-us-en.txt",lang="fr"),num_threads=8))
tts=sherpa_onnx.OfflineTts(cfg)
def say(text,out,sid=30,speed=1.0):
    a=tts.generate(text,sid=sid,speed=speed); sf.write(out,a.samples,a.sample_rate); return len(a.samples)/a.sample_rate
if __name__=="__main__":
    print(say(sys.argv[1],sys.argv[2],int(sys.argv[3]) if len(sys.argv)>3 else 30))
