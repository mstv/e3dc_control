# E3DC Control
Control the charging of an E3DC system (wallbox and battery) via RSCP (using pye3dc)

## Configuration
* Move and rename the folder `control/_config/e3dc_config.sample/` to `../e3dc_config/`
  so that `e3dc_config` is at the same level as the checked repo
* Enter the IP address, the user password and the RSCP secret of your E3DC in `e3dc_config/e3dc_config.py`
* Adapt the settings in `control/_config/config.py`

## Get info from the E3DC
* Run `python -u 'control/main.py' --verbose --num-loops=1 --info`

## Control the E3DC
* Run `python -u 'control/main.py' --dry-run`
* Control the charging strategy during runtime by editing `e3dc_config/e3dc_directives.yaml`

## Kudos
Many thanks go to
* [fsantini](https://github.com/fsantini) for  [fsantini/python-e3dc](https://github.com/fsantini/python-e3dc) / https://pypi.org/project/pye3dc
* [mdhom](https://github.com/mdhom) for https://github.com/fsantini/python-e3dc/pull/59

who enabled the development of this control script.
