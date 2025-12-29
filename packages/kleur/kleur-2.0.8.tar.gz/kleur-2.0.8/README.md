# Kleur: [HSLuv](https://www.hsluv.org/) based color utils & palette generators

[![Poetry](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/githuib/kleur/master/assets/logo.json)](https://pypi.org/project/kleur)
[![PyPI - Version](https://img.shields.io/pypi/v/kleur)](https://pypi.org/project/kleur/#history)
[![PyPI - Python Versions](https://img.shields.io/pypi/pyversions/kleur)](https://pypi.org/project/kleur)

I'd like to give special credits to [Alexei Boronine](https://github.com/boronine) and everyone else who contributed to the [HSLuv](https://www.hsluv.org/) project.
This work provided the fundaments to build this package on (and is the only dependency used in it).

![alt text](https://github.com/githuib/kleur/raw/master/assets/screenshots/palette.png "kleur palette")
![alt text](https://github.com/githuib/kleur/raw/master/assets/screenshots/shades.png "kleur shades")

## Installation

```commandline
pip install kleur
```

## Library usage

When used as a dependency the kleur package contains convenience wrappers around the [HSLuv Python API](https://pypi.org/project/hsluv/), as well as utilities for styling console ouput built on top of it.

(API reference to be added)

## Command line usage

### Preview a color palette

#### General help

```commandline
$ kleur palette -h
usage: kleur palette [-h] [-c NAME=HUE (1-360) [NAME=HUE (1-360) ...]]
[-m] [-a] [-s NUMBER_OF_SHADES] [-v NUMBER_OF_VIBRANCES]

options:
  -h, --help            show this help message and exit
  -c, --colors NAME=HUE (1-360) [NAME=HUE (1-360) ...]
  -m, --merge-with-default-palette
  -a, --alt-default-palette
  -s, --number-of-shades NUMBER_OF_SHADES
  -v, --number-of-vibrances NUMBER_OF_VIBRANCES
```

#### Preview default palette

```commandline
$ kleur palette
```
![alt text](https://github.com/githuib/kleur/raw/master/assets/screenshots/palette/default.png "kleur palette")

#### Preview custom palette

```commandline
$ kleur palette -c green=143 blue=257 tomato=21 violet=273
 ```
![alt text](https://github.com/githuib/kleur/raw/master/assets/screenshots/palette/custom.png "kleur palette -c green=143 blue=257 tomato=21 violet=273")

#### Preview custom palette merged with default palette

```commandline
$ kleur palette -c green=143 blue=257 tomato=21 violet=273 -m
 ```
![alt text](https://github.com/githuib/kleur/raw/master/assets/screenshots/palette/merged.png "kleur palette -c green=143 blue=257 tomato=21 violet=273 -m")

### Generate shades (as CSS variables), based one 1 or 2 (hex) colors

#### General help

```commandline
$ kleur shades -h
usage: kleur shades [-h] [-l LABEL] -c COLOR1 [-k COLOR2]
[-s NUMBER_OF_SHADES] [-b] [-i] [-d DYNAMIC_RANGE]

options:
  -h, --help            show this help message and exit
  -l, --label LABEL
  -c, --color1 COLOR1
  -k, --color2 COLOR2
  -s, --number-of-shades NUMBER_OF_SHADES
  -b, --include-black-and-white
  -i, --include-input-shades
  -d, --dynamic-range DYNAMIC_RANGE
```

#### Based on one input color

```commandline
$ kleur shades -l tables -c 7ab1e5
```
![alt text](https://github.com/githuib/kleur/raw/master/assets/screenshots/shades/single.png "kleur shades -l tables -c 7ab1e5 -i")

With input markers:

```commandline
$ kleur shades -l tables -c 7ab1e5 -i
```
![alt text](https://github.com/githuib/kleur/raw/master/assets/screenshots/shades/single_input.png "kleur shades -l tables -c 7ab1e5 -i")

#### Based on two input colors

The dynamic range specifies to what degree the hue of the input colors will be used as boundaries:

- Dynamic range 0 (0%):

  *The shades will interpolate (or extrapolate) between the input colors.*

- Dynamic range between 0 and 1 (between 0% and 100%):

  *The shades will interpolate (or extrapolate) between darker / brighter shades of the input colors.*

- Dynamic range 1 (100%):

  *The shades will interpolate between the darkest & brightest shades of the input colors.*

```commandline
$ kleur shades -l bad-guy -c badddd -k aa601f -d 66
```
![alt text](https://github.com/githuib/kleur/raw/master/assets/screenshots/shades/double.png "kleur shades -l bad-guy -c badddd -k aa601f -d 66")

With input markers, varying in dynamic range:

```commandline
$ kleur shades -l bad-guy -c badddd -k aa601f -d 0 -i
```
![alt text](https://github.com/githuib/kleur/raw/master/assets/screenshots/shades/double_0.png "kleur shades -l bad-guy -c badddd -k aa601f -d 0 -i")

```commandline
$ kleur shades -l bad-guy -c badddd -k aa601f -d 50 -i
```
![alt text](https://github.com/githuib/kleur/raw/master/assets/screenshots/shades/double_50.png "kleur shades -l bad-guy -c badddd -k aa601f -d 50 -i")

```commandline
$ kleur shades -l bad-guy -c badddd -k aa601f -d 100 -i
```
![alt text](https://github.com/githuib/kleur/raw/master/assets/screenshots/shades/double_100.png "kleur shades -l bad-guy -c badddd -k aa601f -d 100 -i")
