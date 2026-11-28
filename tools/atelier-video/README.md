# Atelier vidéo des séances

Fabrique les séances vidéo de 30 à 60 secondes publiées sur pickleballdujour.fr/seances/ :
terrain animé, voix off féminine (Kokoro, voix ff_siwis), sous-titres incrustés et fichier VTT, miniature.

## Installer (une fois par machine)

```
pip install --break-system-packages sherpa-onnx==1.12.40 soundfile numpy pillow
mkdir -p /home/claude/dl_voice && cd /home/claude/dl_voice
curl -sSLO https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/kokoro-multi-lang-v1_0.tar.bz2
mkdir -p kk && tar xjf kokoro-multi-lang-v1_0.tar.bz2 -C kk
# Optionnel, pour vérifier la prononciation par retranscription :
curl -sSLO https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-whisper-base.tar.bz2 && tar xjf sherpa-onnx-whisper-base.tar.bz2
```

## Utiliser

- `python3 sessions.py plan` : synthèse vocale et durée de chaque séance.
- `python3 sessions.py frames <slug>` : images clés et miniature, à regarder avant de rendre.
- `python3 audit.py` : contrôle automatique des règles et de la cohérence des animations. **Doit afficher « Total : 0 » avant toute publication.**
- `python3 sessions.py render <slug> ...` : rendu final dans `catalogue/` (mp4, jpg, vtt).
- `python3 asr.py fichier.wav` : retranscription, pour vérifier que la voix dit bien ce qui est écrit.

Puis copier `catalogue/<slug>.{mp4,jpg,vtt}` dans `static/seances/`, mettre à jour `content/seances.py` et lancer `python3 build.py`.

## Règles de l'atelier (issues de l'audit du 28/11/2026)

- Le serveur se tient derrière la ligne de fond, sert en diagonale, depuis sa moitié droite quand le score de son équipe est pair (dont 0-0-2).
- Un joueur ne frappe jamais une balle loin de lui : il se déplace d'abord (`moves`, `rep_moves`).
- Dans un exercice, une réussite tombe dans la zone visée et un raté n'y tombe pas (`OBJ` dans sessions.py).
- La balle qui va dans le camp adverse traverse toujours le filet ; une balle « dehors » sort dans le camp de celui qui la reçoit.
- Erne : on contourne la cuisine par l'extérieur, jamais à travers. Tour du poteau : la balle rebondit dans le terrain avant de sortir.
- Toute nouvelle séance passe le skill de vérification « formateur » puis la validation d'un joueur avant publication.
