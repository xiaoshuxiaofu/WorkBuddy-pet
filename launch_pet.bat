@echo off
REM Launch Desktop Pet - Blue Slime
REM Usage: Double-click this file or run from command line

cd /d "%~dp0"
python scripts\desktop_pet.py --atlas output\pets\demo\blue-slime_atlas.png --manifest output\pets\demo\pet.json --scale 2.0
