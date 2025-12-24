from flask import Blueprint, render_template, request, session, redirect, jsonify
from BOFS import db
from BOFS.util import *
from datetime import timedelta, datetime
from flask import make_response, request, current_app
from functools import update_wrapper
import urllib
from BOFS.admin.util import verify_admin


superhexagon = Blueprint('superhexagon', __name__,
                         static_url_path='/superhexagon', static_folder='static', template_folder='templates')


EXPORT = [
    {
        'table': 'SHTrial',
        'fields': {
            'total_trials': 'count(shTrialID)',
            'frames_per_second': 'avg(avgFps)',
            'average_duration': 'avg(duration)',
            'max_duration': 'max(duration)',
            'min_duration': 'min(duration)'
        },
        'group_by': 'sessionNumber'
    },
    {
        'table': 'SHTrial',
        'fields': {
            'play_time_wo_interrupted': 'sum(duration)',
            'total_trials_wo_interrupted': 'count(shTrialID)',
            'average_duration_wo_interrupted': 'avg(duration)',
        },
        'group_by': 'sessionNumber',
        'filter': 'interrupted = 0'
    },
    {
        'table': 'SHReplayEvent',
        'fields': {
            'obstacles_passed': 'count(shReplayEventID)'
        },
        'group_by': 'sessionNumber',
        'filter': 'eventType = "CheckpointTrigger"'
    }
]


@superhexagon.route('/game_mode', methods=['GET', 'POST'])
@verify_correct_page
@verify_session_valid
def game_mode_route():
    if request.method == 'POST':
        condition = int(request.form['game_mode'])
        session['condition'] = condition

        p = db.session.query(db.Participant).get(session['participantID'])
        p.condition = condition
        db.session.commit()

        return redirect("/redirect_from_page/game_mode")
    return render_template("game_mode.html")


@superhexagon.route("/game")
@verify_correct_page
@verify_session_valid
def superhexagon_route():
    return render_template("superhexagon.html")


def sh_get_settings_dict(participantID=None):
    if participantID is None:
        #participantID = session['participantID']
        condition = session['condition']
    else:
        p = db.session.query(db.Participant).get(participantID)
        condition = p.condition

    feedback_map = {1: 'None', 2: 'Meaningful', 3: 'Meaningless'}

    settings = {
        'Sessions': [
            #{'InterTrialTime': 3, 'SessionTime': current_app.config['SESSION_TIME'], 'InterSessionTime': current_app.config['BREAK_TIME']},
            {'InterTrialTime': 3, 'SessionTime': current_app.config['SESSION_TIME'], 'InterSessionTime': 3}
        ],
        'FeedbackType': 'Default' #feedback_map[condition]
    }

    return settings


@superhexagon.route("/sh_get_settings/<int:participantID>", methods=['GET'])
@superhexagon.route("/sh_get_settings", methods=['GET'])
def sh_get_settings(participantID=None):
    return jsonify(sh_get_settings_dict(participantID))


@superhexagon.route("/sh_post_state", methods=['POST'])
def sh_post_state():
    if request.method == 'POST':
        try:
            participantID = session['participantID']
        except:  # This because I sometimes test from Unity directly
            participantID = request.form['participantID']

        # First, check to see if there is already a record for the user.
        state = db.session.query(db.SHState).get(participantID)

        if state is None:  # No record was found, so start one.
            state = db.SHState()
            state.participantID = participantID
            state.startTime = datetime.now()
            db.session.add(state)

        state.updateTime = datetime.now()
        state.interSessionTimeRemaining = float(request.form["interSessionTimeRemaining"])
        state.sessionTimeRemaining = float(request.form["sessionTimeRemaining"])
        state.sessionNumber = int(request.form["sessionNumber"])
        state.trialNumber = int(request.form["trialNumber"])
        state.maxDuration = float(request.form["maxDuration"])

        db.session.commit()

        return ""


@superhexagon.route("/sh_post_trial", methods=['POST'])
def sh_post_trial():
    if request.method != 'POST':
        return ""

    trial = db.SHTrial()

    try:
        trial.participantID = session['participantID']
    except:  # This because I sometimes test from Unity directly
        trial.participantID = -1
    trial.submitTime = datetime.now()
    trial.duration = float_or_0(request.form["duration"])
    trial.avgFps = float_or_0(request.form["avgFps"])
    trial.trialNumber = int_or_0(request.form["trialNumber"])
    trial.sessionNumber = int_or_0(request.form["sessionNumber"])
    trial.difficultyRotation = float_or_0(request.form["difficultyRotation"])
    trial.difficultySpawning = float_or_0(request.form["difficultySpawning"])
    trial.movements = request.form["movements"]
    trial.interrupted = request.form["interrupted"] == 'true'

    db.session.add(trial)
    db.session.commit()

    return ""


@superhexagon.route("/sh_post_replay", methods=['POST'])
def sh_post_replay():
    if 'replay' not in request.files:
        return ""

    lines = request.files['replay'].stream.readlines()
    full_log = ""

    for line in lines:
        full_log += line.decode('utf-8')

    for event_line in full_log.split('\n'):
        columns = event_line.split('|')
        #{Type}|{SessionNumber}|{TrialNumber}|{TrialTime}|{GameTime}|{PlayerRotation}|{RotationInput}|{CameraRotationSpeed}|
        #{ThreatSpeed}|{PlayerRotationRate}|{PatternName}|{EventRadius}|{PatternOuterRadius}|{PatternInnerRadius}

        if len(columns) <= 1:
            continue

        replay_event = db.SHReplayEvent()
        if 'participantID' in session:
            replay_event.participantID = session['participantID']
        else:
            replay_event.participantID = -1
        replay_event.eventType = columns[0]
        replay_event.sessionNumber = int_or_0(columns[1])
        replay_event.trialNumber = int_or_0(columns[2])
        replay_event.trialTime = float_or_0(columns[3])
        replay_event.gameTime = float_or_0(columns[4])
        replay_event.playerRotation = float_or_0(columns[5])
        replay_event.rotationInput = float_or_0(columns[6])
        replay_event.cameraRotationSpeed = float_or_0(columns[7])
        replay_event.threatSpeed = float_or_0(columns[8])
        replay_event.playerRotationRate = float_or_0(columns[9])
        replay_event.patternName = columns[10]
        replay_event.eventRadius = float_or_0(columns[11])
        replay_event.patternOuterRadius = float_or_0(columns[12])
        replay_event.patternInnerRadius = float_or_0(columns[13])
        replay_event.threatAngularPosition = float_or_0(columns[14])

        replay_event.nextTriggerAngles = columns[15]
        replay_event.canMoveCw = columns[16].lower() == 'true'
        replay_event.canMoveCcw = columns[17].lower() == 'true'
        replay_event.isTriggerAlignedWithPlayer = columns[18].lower() == 'true'
        replay_event.closestCwTriggerAngle = float_or_0(columns[19])
        replay_event.closestCwCcw = float_or_0(columns[20])
        replay_event.bestMovementOption = columns[21]

        db.session.add(replay_event)
        db.session.commit()

    return ""


# If the user reloads the page, their progress should be loaded.
@superhexagon.route("/sh_get_state/<int:participantID>", methods=['GET'])
@superhexagon.route("/sh_get_state", methods=['GET'])
def sh_get_state(participantID=None):
    return ""
    # This is broken

    if participantID is None:
        participantID = session['participantID']

    state = db.session.query(db.SHState).get(participantID)

    if state is None:
        return ""

    return jsonify(state.toDict())


@superhexagon.route("/admin/sh_summary", methods=['GET', 'POST'])
@verify_admin
def sh_summary():
    participants = db.session.query(db.Participant).filter(db.Participant.finished == True).all()

    result = "participantID,mTurkID,Session1_Trials,Session1_Max,Session1_Avg,Session1_Rest,Session1_AvgFps,Session2_Trials,Session2_Max,Session2_Avg,Session2_Rest,Session2_AvgFps,Session3_Trials,Session3_Max,Session3_Avg,Session3_Rest,Session3_AvgFps,Session4_Trials,Session4_Max,Session4_Avg,Session4_Rest,Session4_AvgFps\n"\

    for p in participants:
        result += "{0},{1},".format(p.participantID, p.mTurkID)

        session1 = SHSummary(p.participantID, 0)

        result += "{0},{1},{2},{3},{4},".format(
            session1.trialsCount(),
            session1.maxDuration(),
            session1.avgDuration(),
            session1.restDuration(),
            session1.avgFps()
        )

        session2 = SHSummary(p.participantID, 1)

        result += "{0},{1},{2},{3},{4},".format(
            session2.trialsCount(),
            session2.maxDuration(),
            session2.avgDuration(),
            session2.restDuration(),
            session2.avgFps()

        )

        session3 = SHSummary(p.participantID, 2)

        result += "{0},{1},{2},{3},{4},".format(
            session3.trialsCount(),
            session3.maxDuration(),
            session3.avgDuration(),
            session3.restDuration(),
            session3.avgFps()

        )

        session4 = SHSummary(p.participantID, 3)

        result += "{0},{1},{2},{3},{4}\n".format(
            session4.trialsCount(),
            session4.maxDuration(),
            session4.avgDuration(),
            session4.restDuration(),
            session4.avgFps()
        )

    return "<pre>" + result + "</pre>"


# Session summary. This can actually just be calculated afterwards.
class SHSummary:
    def __init__(self, participantID, sessionNumber):
        self.participantID = participantID
        self.sessionNumber = sessionNumber
        self.trials = db.session.query(db.SHTrial).filter(
            db.SHTrial.participantID == participantID,
            db.SHTrial.sessionNumber == sessionNumber
        ).\
        order_by(db.SHTrial.trialNumber).all() or []

    def restDuration(self):
        if self.sessionNumber == 0:
            return 0

        if self.trials == []:
            return 0

        try:
            prevTrials = db.session.query(db.SHTrial).filter(
                db.SHTrial.participantID == self.participantID,
                db.SHTrial.sessionNumber == (self.sessionNumber - 1)
            ).all() or []

            prevTrialsLastTimestamp = prevTrials[-1].submitTime
            theseTrialsFirstTimestamp = self.trials[0].submitTime

            theseTrialsFirstTimestamp = theseTrialsFirstTimestamp - timedelta(seconds=self.trials[0].duration)

            return (theseTrialsFirstTimestamp - prevTrialsLastTimestamp).total_seconds()
        except:
            return 0

    def maxDuration(self):
        return db.session.query(db.func.max(db.SHTrial.duration)).filter(
            db.SHTrial.participantID == self.participantID,
            db.SHTrial.sessionNumber == self.sessionNumber).scalar()or 0

    def avgDuration(self):
        sum_duration = 0
        count_trials = 0

        if self.trials == []:
            return 0

        for trial in self.trials:
            if count_trials == len(self.trials) - 1:
                session_start = self.trials[0].submitTime - timedelta(seconds=self.trials[0].duration)
                session_end = self.trials[-1].submitTime

                # Determine if the session was interrupted.
                time_delta = (session_end - session_start)

                five_minutes = timedelta(minutes=5)

                if time_delta > five_minutes:
                    time_delta = time_delta - five_minutes
                else:
                    time_delta = five_minutes - time_delta

                if abs(time_delta.microseconds) < 100000:
                    print("they were interrupted!")
                    continue

            sum_duration += trial.duration
            count_trials += 1


        return float(sum_duration) / float(count_trials)

        # Old, simple implementation
        #return db.session.query(db.func.avg(db.SHTrial.duration)).filter(
        #    db.SHTrial.participantID == self.participantID,
        #    db.SHTrial.sessionNumber == self.sessionNumber).scalar() or 0

    def trialsCount(self):
        return len(self.trials)

    def avgFps(self):
        return db.session.query(db.func.avg(db.SHTrial.avgFps)).filter(
            db.SHTrial.participantID == self.participantID,
            db.SHTrial.sessionNumber == self.sessionNumber).scalar() or 0
