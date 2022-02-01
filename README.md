# Mercury
Mercury is a Discord bot built on python3 and the py-cord library.

## Contents
- [Overview](#overview)
- [Key Features](#key-features)
- [Screenshots](#screenshots)
- [Installation](#installation)

## Overview
Mercury is a highly configurable bot that can be used for basic server management, and to pull data from EVE Online.

## Key Features
### General
* Easy setup and management
  * Guided initial setup, just run a command and answer questions! No copying and editing files.
  * Need to edit the bot config? Just run the setup command again!
  * "Hot Swappable" cogs! Want to enable or disable a cog without restarting the bot? That's just a command away.
* Welcome new members to your server with a custom message (set by command)
### EVE Online Related
* Subscribe to the zKillboard kill feed to post the killmails you care about straight to your discord.
* Subscribe to the EVE-Scout thera API to get notifications about thera holes near you!
* Check prices on any item in the game. (Using fuzzwork's market API)
* Get quick info on any character, corporation, alliance, or system in the game.
* Check your (or an enemy's) zkillboard stats.
* Automatically post zkillboard stats, kill data, and market data whenever a relevant link is posted in discord.

## Screenshots

### Killmails

####Kill:

![Kill Pic](https://i.imgur.com/Ho5Hteh.png)
#### Loss:
![Loss Pic](https://i.imgur.com/GXdtxHe.png)

### Thera Notifications
![thera pic](https://i.imgur.com/NjuOYM4.png)

### ESI Data
#### Systems
![System Pic](https://i.imgur.com/kWd0oDv.png)
#### Characters
![charactre pic](https://i.imgur.com/meDMJ4W.png)
#### Corporations
![corp pic](https://i.imgur.com/5nIJbGf.png)
#### Alliances
![alliance pic](https://i.imgur.com/tRd8tgV.png)

### Market Data
![market pic](https://i.imgur.com/CNW1rjD.png)

## Installation
### Requirements
Before installing Mercury there are two things that must be installed on your machine:
1. python3.9 or greater (including `python3.x-pip` and `python3.x-venv` on Ubuntu)
2. postgres 9.4 or greater

Those are the only 2 prerequisites for this project.

### Installing
1. First you will need to clone this git project. (`$ git clone https://github.com/colcrunch/Mercury`)
2. Create a new venv for the bot. (`$ python -m venv mercury`)
3. Activate the venv. (`$ source mercury/bin/activate`)
4. Install dependencies from `requirements.txt` (`(mercury)$ pip install -r requirements.txt`)
5. Run the setup command. (`(mercury)$ python launcher.py --setup`)
6. Run the migrations. (`(mercury)$ python launcher.py --migrate`)

### Running the Bot
Though it would be fine to run the bot using screen, I would suggest instead using supervisor.
