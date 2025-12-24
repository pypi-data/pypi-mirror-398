from datetime import datetime

from BOFS.admin.util import verify_admin
from flask import Blueprint, render_template, request, session, redirect, jsonify
from BOFS.util import *
from BOFS.globals import db
from flask import make_response, request, current_app
from functools import update_wrapper
import urllib

pauseplay = Blueprint('pauseplay', __name__,
                      static_url_path='/pauseplay', template_folder='templates', static_folder='static')

EXPORT = [
    {
        'measure_type': 'repeated',
        'table': 'PausePlayLevels',
        'group_by': 'sessionName',
        'order_by': 'sessionName',
        'filter': '',
        'fields': {'LevelsFinished': 'sum(finishedLevel = \'True\')', 'Deaths': 'sum(deathCount)'}
    },
    {
        'measure_type': 'repeated',
        'table': 'PausePlayProgress',
        'group_by': 'sessionName',
        'order_by': 'sessionName',
        'filter': '',
        'fields': {'TotalWaitTime': 'sum(timeToWait)'}
    },
    {
        'measure_type': 'repeated',
        'table': 'PausePlayLevels',
        'filter': 'levelName IN (\'Intro1\', \'Intro2\', \'Intro3\')',
        'fields': {'TutorialLevelsTime': 'sum(levelTime)', 'TutorialLevelsCompleted': 'sum(finishedLevel = \'True\')'}
    },
    {
        'measure_type': 'repeated',
        'table': 'PausePlayLevels',
        'filter': '',
        'fields': {'AverageFps': 'avg(averageFPS)'}
    }
]

"""
EXPORT = [
    {
        'measure_type': 'repeated',
        'table': 'PausePlayLaps',
        'group_by': 'session',
        'order_by': 'session',
        'filter': 'finishedLap = "True"',
        'fields': ['avg(lapTime)']
    },
    {
        'measure_type': 'repeated',
        'table': 'PausePlayLaps',
        'group_by': 'session',
        'order_by': 'session',
        'filter': '',
        'fields': ['max(totalDistance)', 'sum(lapTime)']
    },
    {
        'measure_type': 'repeated',
        'table': 'PausePlayBreaks',
        'group_by': 'breakSession',
        'order_by': 'breakSession',
        'filter': '',
        'fields': ['breakTime', 'interactionCount']
    }
]
"""


@pauseplay.route("/pauseplay", methods=['POST', 'GET'])
@verify_correct_page
@verify_session_valid
def game_pauseplay():
    if request.method == 'POST':
        trial = db.PausePlay()

        try:
            trial.participantID = session['participantID']
        except:
            trial.participantID = request.form['participantID']

        db.session.add(trial)
        db.session.commit()

        return ""

    # Condition 1: no checkpoints, no respawn delay
    # Condition 2: yes checkpoints, no respawn delay
    # Condition 3: yes checkpoints, yes respawn delay
    # Condition 4: no checkpoints, yes respawn delay
    checkpoints = False
    respawnDelay = 1

    if session['condition'] in (2, 3):
        checkpoints = True
    if session['condition'] in (3, 4):
        respawnDelay = 10

    return render_template("training.html",
                           crumbs=create_breadcrumbs(),
                           application_root=current_app.config["APPLICATION_ROOT"],
                           checkpoints=checkpoints,
                           respawnDelay=respawnDelay)


@pauseplay.route("/pauseplay_immediate", methods=['POST', 'GET'])
@verify_correct_page
@verify_session_valid
def game_pauseplay_immediate():
    if request.method == 'POST':
        trial = db.PausePlay()

        try:
            trial.participantID = session['participantID']
        except:
            trial.participantID = request.form['participantID']

        db.session.add(trial)
        db.session.commit()

        return ""

    checkpoints = False
    respawnDelay = 1

    return render_template("immediate.html",
                           crumbs=create_breadcrumbs(),
                           application_root=current_app.config["APPLICATION_ROOT"],
                           checkpoints=checkpoints,
                           respawnDelay=respawnDelay)


@pauseplay.route("/pauseplay_retention", methods=['POST', 'GET'])
@verify_correct_page
@verify_session_valid
def game_pauseplay_retention():
    return render_template("retention.html",
                           crumbs=create_breadcrumbs(),
                           application_root=current_app.config["APPLICATION_ROOT"],
                           checkpoints=False,
                           respawnDelay=1)


@pauseplay.route("/end_game_early")
@verify_session_valid
def end_game_early():
    p = db.session.query(db.Participant).get(session['participantID'])
    p.condition = -p.condition
    db.session.commit()

    return redirect("redirect_to_page/end")


@pauseplay.route("/pauselevels", methods=['POST'])
@verify_session_valid
def game_levels():
    log = db.PausePlayLevels()

    try:
        log.participantID = session['participantID']
    except:
        log.participantID = request.form['participantID']

    log.finishedLevel = request.form['FinishedLevel']
    log.levelName = request.form['LevelName']
    log.levelNumber = request.form['LevelNumber']
    log.levelTime = request.form['LevelTime']
    log.gameTime = request.form['GameTime']
    log.coinsCollected = request.form['CoinsCollected']
    log.playSession = request.form['session']
    log.maxTime = request.form['MaxTime']
    log.levelCompletePercent = request.form['LevelCompletePercentage']
    log.breakType = request.form['BreakType']
    log.deathCount = request.form['DeathCount']
    log.averageFPS = request.form['AverageFPS']
    log.sessionName = request.form['SessionName']

    db.session.add(log)
    db.session.commit()

    return ""


@pauseplay.route("/pauseprogress", methods=['POST'])
@verify_session_valid
def game_death():
    log = db.PausePlayProgress()

    try:
        log.participantID = session['participantID']
    except:
        log.participantID = request.form['participantID']

    log.levelName = request.form['levelName']
    log.levelNumber = request.form['levelNumber']
    log.levelTime = request.form['levelTime']
    log.gameTime = request.form['gameTime']
    log.playSession = request.form['session']
    log.collidedWith = request.form['collidedWith']
    log.x = request.form['x']
    log.y = request.form['y']
    log.sessionName = request.form['sessionName']
    log.progressType = request.form['progressType']
    log.timeToWait = request.form['timeToWait']

    db.session.add(log)
    db.session.commit()

    return ""

