# Pickleball du Jour

Site statique de pickleballdujour.fr (FR + EN).

- `content/` : textes (pages de fond, conseils, pages annexes)
- `illus.py` : illustrations SVG originales
- `build.py` : génère le site dans `docs/` (servi par GitHub Pages)

Ajouter un conseil : ajouter une entrée dans `content/tips_fr.py` et `content/tips_en.py` (même position), puis `python3 build.py`.
