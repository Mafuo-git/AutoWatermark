# AutoWatermark

**Ajoutez un filigrane à vos photos et vidéos par lots, en quelques clics.**

AutoWatermark est une application Windows portable. Choisissez des fichiers ou un dossier, personnalisez le texte et le logo, placez le filigrane sur l’aperçu, puis lancez le traitement. Les médias sont traités localement sur votre ordinateur.

## Fonctionnalités

- Sélection de fichiers individuels ou de tous les médias pris en charge dans un dossier et ses sous-dossiers.
- Filigrane combinant texte et logo, avec aperçu en direct.
- Choix de la police, de la taille, de la couleur du texte, de la couleur de fond et de l’opacité.
- Positionnement du filigrane par glisser-déposer sur l’aperçu.
- Enregistrement dans un dossier de sortie distinct, en conservant l’arborescence, ou remplacement des originaux après confirmation.
- Barre de progression et rapport explicite des fichiers qui n’ont pas pu être traités.
- Aucun runtime, bibliothèque ou installation requis sur le PC qui exécute l’application publiée.

## Utiliser l’application

1. Téléchargez `AutoWatermark.exe` depuis les artefacts de la dernière compilation Windows du dépôt, puis double-cliquez dessus.
2. Cliquez sur **Choisir un dossier** ou **Ajouter des fichiers**.
3. Choisissez un dossier de sortie. L’option **Remplacer les fichiers originaux** est désactivée par défaut ; elle demande une confirmation avant toute modification.
4. Personnalisez le texte, la police, les couleurs, la taille et l’opacité. Ajoutez un logo facultatif.
5. Faites glisser le filigrane dans l’aperçu pour choisir son emplacement.
6. Cliquez sur **Exécuter** et consultez le résultat affiché à la fin.

La sélection d’un dossier recherche les fichiers pris en charge dans ses sous-dossiers. Les copies conservent cette arborescence sous le dossier de sortie. Choisissez un dossier de sortie distinct, situé en dehors du dossier source.

### Formats pris en charge

- **Images :** JPEG, PNG, WebP, BMP et TIFF.
- **Vidéos :** MP4, MOV, M4V, MKV et AVI.
- **Logos :** PNG, JPEG, WebP, BMP et TIFF.

Les vidéos sont réencodées en H.264 avec audio AAC. Cela permet d’incruster le filigrane dans l’image, mais peut prendre du temps et modifier les caractéristiques d’encodage du fichier. Gardez une copie de vos originaux ; le remplacement est irréversible.

## Obtenir l’exécutable Windows

Le dépôt contient les sources et un workflow de compilation Windows. Pour télécharger l’exécutable prêt à l’emploi :

1. Ouvrez l’onglet **Actions** du dépôt GitHub et sélectionnez **Build Windows executable**.
2. Cliquez sur **Run workflow**.
3. Une fois la compilation terminée, ouvrez son résumé et téléchargez l’artefact **AutoWatermark-Windows-x64**.
4. Extrayez `AutoWatermark.exe` et partagez ce seul fichier.

La création d’une étiquette Git commençant par `v` déclenche également une compilation. Le fichier compilé n’est pas suivi dans Git ; il est produit par le workflow.

## Compiler depuis les sources

Sur Windows, installez Python 3.12 ou une version compatible, puis exécutez PowerShell depuis la racine du dépôt :

```powershell
.\build.ps1
```

Le script installe les dépendances Python, exécute les tests et crée `dist\AutoWatermark.exe` avec PyInstaller. L’exécutable inclut Python, Pillow et le binaire FFmpeg utilisé pour les vidéos : aucun de ces composants n’a besoin d’être installé sur l’ordinateur destinataire.

Dépendances principales : [Pillow](https://python-pillow.org/), [imageio-ffmpeg](https://github.com/imageio/imageio-ffmpeg) et [PyInstaller](https://pyinstaller.org/). FFmpeg et les composants tiers restent soumis à leurs licences respectives.

## Confidentialité et limites

Les fichiers et logos sont lus localement et ne sont envoyés à aucun service en ligne. L’application ne modifie que les fichiers sélectionnés. Les fichiers vidéo dont le codec ou le conteneur ne peut pas être traité par le binaire FFmpeg inclus sont signalés en erreur ; les originaux sont conservés si le traitement échoue.

La première ouverture peut être retardée de quelques secondes par l’analyse antivirus, car l’application est distribuée sous forme d’un exécutable autonome non signé.

## Développement

```powershell
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python app.py
```

## Licence

Le code de ce projet est distribué sous licence MIT. Consultez [LICENSE](./LICENSE) et les licences des composants tiers utilisés pour la compilation et le traitement vidéo.
