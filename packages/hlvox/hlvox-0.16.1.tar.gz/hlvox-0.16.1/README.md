# HLVox

[![pipeline status](https://gitlab.com/bhagen/hlvox/badges/master/pipeline.svg)](https://gitlab.com/bhagen/hlvox/commits/master)
[![coverage report](https://gitlab.com/bhagen/hlvox/badges/master/coverage.svg)](https://gitlab.com/bhagen/hlvox/commits/master)
[![PyPI version](https://badge.fury.io/py/hlvox.svg)](https://badge.fury.io/py/hlvox)

Originally intended to create sentences from the word snippets for the 
Half Life 1 Vox, this project can take a folder of word audio files and piece 
them into sentences.
This repo when used standalone (ie by running `voice.py` directly) will output
the sentences as audio files.

## Getting Started

To use this project, you will first need a folder full of voice files.
If you have Half Life 1 installed, the voices can be extracted from the VPK 
files using something like GCFScape.

### Prerequisites

Check pipenv file for Python package requirements.

An installation of FFMpeg is required. On Ubuntu, just run the following:

```
apt update
apt install ffmpeg
```

For persistence, a local `sqlite` database can be used, or a `postgresql` database. These are not exposed through the basic CLI.

### Installing

How to set up a basic dev environment:

Pull this repo

```
git pull https://gitlab.com/bhagen/hlvox.git
```

Change into the new repo directory

```
cd hlvox
```

Install requirements using pipenv
```
pipenv install 
```

Enter pipenv
```
pipenv shell
```

### Quick Start

If you want to jump right into generating a sentence, you can point `voice.py` 
at a folder of voice audio files!

```
python hlvox/voice.py --voice-dir ~/my_folder_of_voice_files "the sentence I want to generate"
```

Your sentence will be exported in the same directory
that you ran the file from.

### Installing package locally for development
After entering pipenv shell:
```
pip install --editable .
```

## Running the tests

Just run `pytest` from the base directory of the repo

## Documentation Generation

I used [Sphinx](http://www.sphinx-doc.org) to create autodoc documentation
from docstrings in the modules.

Change into doc directory
```
cd doc
```

(If you've modified the source code, grab the new apidocs
```
sphinx-apidoc -f -o ./source ../hlvox
```


Generate documentation
```
make html
```


## Authors

* **Blair Hagen** - *Initial work* - [bhagen](https://github.com/bhagen)


## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments

* Thanks to Valve for making such an amazing voice
