<p align="center">
  <img src="https://github.com/spicytigermeat/LabelMakr/blob/v030/assets/labelmakr.png" alt="LabelMakr 🛋️">
</p>

<p align="center">
  <img src="https://github.com/spicytigermeat/LabelMakr/blob/v030/.github/labelmakr_sc.png", alt="Screenshot of LabelMakr and the transcription editor.">
</p>

LabelMakr is a GUI tool to help users easily generate SVS phoneme-level labels. It is intended for use with DiffSinger, but is easily adaptable for other systems. Currently, LabelMakr has full support for English, Japanese, Chinese, French and Korean singing!

Please use the portable version for Windows found [here](https://github.com/spicytigermeat/LabelMakr/releases/tag/v030).

## Manual Installation

### Windows/macOS

(work in progress)

### Linux

Tkinter distributions are weird on Linux, so you have to set up a conda environment in a specific way.

```
conda create -n labelmakr -y -c conda-forge "python=3.12.*" "tk[build=xft_*]"
pip install torch torchvision torchaudio
pip install -r requirements.txt
python labelmakr.py
```

## Community Contributions 🧑‍🤝‍🧑

- Le guide d'utilisation en Français [peut-être trouvé ici](https://utaufrance.com/comment-utiliser-labelmakr/)! (Written by [Mim](https://twitter.com/mimsynth))
- 한국어 사용 가이드는 [여기](https://docs.google.com/document/d/1-EcFrkt4VDjRlFQ8Sytvov4_3GjDt4-xHYNjQDuDScU/edit)서 찾을 수 있습니다! (Written by [군곰 KUNGOM](https://twitter.com/utaukg))

## Custom SOFA Model Implementation

Please check out the guide on how to implement custom SOFA models [here!](https://github.com/spicytigermeat/LabelMakr/blob/v030/DOCS/implement_custom_sofa_model.md)

## Credits

Please check out credits [here!](https://github.com/spicytigermeat/LabelMakr/blob/v030/DOCS/credits.md)

## Manual Installation 🧰

Read the guide on how to manually install LabelMakr [here!](https://github.com/spicytigermeat/LabelMakr/blob/v030/DOCS/manual_install_guide.md)
