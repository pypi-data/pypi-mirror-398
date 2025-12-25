# cas-toolbox

**Version:** ex: `2025.7.2` -> (2025 wk 7 hotfix 2) 

Will update every monday if there is a code change.

Cluster Automation Scripts Toolbox - 
- One stop ship for tool scripts for cluster automation operations in high performance computing.
- All single file script / libs for easy transportation
- Minimal dependencies for all scripts

## Requirements
- Python >= 3.6  
- argparse

## Optional Python Libs
- curses
- python-dateutil
- xxhash
- resource
- prettytable
- ipaddress
- numpy

## Includes following single file libs
- hpcp.py
- multiCMD.py 
- multiSSH3.py
- iotest.py (simple-iotest) 
- statbtrfs.py
- Tee_Logger.py
- TSVZ.py
- statblk.py

## Installation
Use pip:
```bash
pip install cas-toolbox
```
Use pipx:
```bash
pipx install cas-toolbox
```
Use uv:
```bash
uv tool install --with numpy cas-toolbox
```
Note: with numpy, iotest random number generator will perform much better. But it is not used anywhere else.

Use uv to add as dependency:
```bash
uv add cas-toolbox
```

## Commands provided:
- `hpcp`  
- `mcmd` / `multicmd` / `multiCMD`  
- `mssh` / `mssh3` / `multissh` / `multissh3` / `multiSSH3`  
- `iotest`  
- `statbtrfs`  
- `TSVZ` / `tsvz`
- `statblk`

All with `--help` / `-h` provided.

## Author
- Yufei Pan (pan@zopyr.us)

## License
GPL-3.0-or-later

## Links
- [hpcp](https://github.com/yufei-pan/hpcp)
- [multiCMD](https://github.com/yufei-pan/multiCMD)
- [multiSSH3](https://github.com/yufei-pan/multiSSH3)
- [simple-iotest](https://github.com/yufei-pan/simple-iotest)
- [statbtrfs](https://github.com/yufei-pan/statbtrfs)
- [Tee_Logger](https://github.com/yufei-pan/Tee_Logger)
- [TSVZ](https://github.com/yufei-pan/TSVZ)
- [statblk](https://github.com/yufei-pan/statblk)
