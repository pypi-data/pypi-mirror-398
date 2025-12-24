from datetime import datetime


def create(db):
    # This gets updated periodically by the game so that progress can be recovered if the web page is refreshed.
    class SHState(db.Model):
        __tablename__ = "sh_state"

        participantID = db.Column(db.Integer, db.ForeignKey('participant.participantID'), primary_key=True)
        startTime = db.Column(db.DateTime, nullable=False, default=datetime.min)
        updateTime = db.Column(db.DateTime, nullable=False, default=datetime.min)
        interSessionTimeRemaining = db.Column(db.Float, nullable=False, default=0.0)  # 0 if game is active, >0 if anything else
        sessionTimeRemaining = db.Column(db.Float, nullable=False, default=0.0)
        sessionNumber = db.Column(db.Integer, nullable=False, default=0)
        trialNumber = db.Column(db.Integer, nullable=False, default=0)
        maxDuration = db.Column(db.Float, nullable=False, default=0.0)  # High score

        def toDict(self):
            return {
                'participantID': self.participantID,
                'interSessionTimeRemaining': self.interSessionTimeRemaining,
                'sessionTimeRemaining': self.sessionTimeRemaining,
                'sessionNumber': self.sessionNumber,
                'trialNumber': self.trialNumber,
                'maxDuration': self.maxDuration
            }

    # Gets saved after each trial ends.
    class SHTrial(db.Model):
        __tablename__ = "sh_trial"

        shTrialID = db.Column(db.Integer, primary_key=True, autoincrement=True)
        participantID = db.Column(db.Integer, db.ForeignKey('participant.participantID'))
        submitTime = db.Column(db.DateTime, nullable=False, default=datetime.min)
        duration = db.Column(db.Float, nullable=False, default=0.0)
        avgFps = db.Column(db.Float, nullable=False, default=0.0)
        trialNumber = db.Column(db.Integer, nullable=False, default=0)
        interrupted = db.Column(db.Boolean, nullable=False, default=False)
        sessionNumber = db.Column(db.Integer, nullable=False, default=0)
        difficultyRotation = db.Column(db.Float, nullable=False, default=0.0)
        difficultySpawning = db.Column(db.Float, nullable=False, default=0.0)
        keyPressCount = db.Column(db.Integer, nullable=False, default=0)
        referrer = db.Column(db.Text, nullable=False, default="")

        movements = db.Column(db.Text, nullable=False, default="")  # CSV list of player positional information

    class SHReplayEvent(db.Model):
        __tablename__ = "sh_replay_event"

        shReplayEventID = db.Column(db.Integer, primary_key=True, autoincrement=True)
        participantID = db.Column(db.Integer, db.ForeignKey('participant.participantID'))
        eventType = db.Column(db.Text, nullable=False, default="")
        sessionNumber = db.Column(db.Integer, nullable=False)
        trialNumber = db.Column(db.Integer, nullable=False)
        trialTime = db.Column(db.Float, nullable=False, default=0.0)
        gameTime = db.Column(db.Float, nullable=False, default=0.0)
        playerRotation = db.Column(db.Float, nullable=False, default=0.0)
        rotationInput = db.Column(db.Float, nullable=False, default=0.0)
        cameraRotationSpeed = db.Column(db.Float, nullable=False, default=0.0)
        threatSpeed = db.Column(db.Float, nullable=False, default=0.0)
        playerRotationRate = db.Column(db.Float, nullable=False, default=0.0)
        patternName = db.Column(db.Text, nullable=False, default="")
        eventRadius = db.Column(db.Float, nullable=False, default=0.0)
        patternOuterRadius = db.Column(db.Float, nullable=False, default=0.0)
        patternInnerRadius = db.Column(db.Float, nullable=False, default=0.0)
        threatAngularPosition = db.Column(db.Float, nullable=False, default=0.0)
        nextTriggerAngles = db.Column(db.Text, nullable=False, default="")
        canMoveCw = db.Column(db.Boolean, nullable=False, default=False)
        canMoveCcw = db.Column(db.Boolean, nullable=False, default=False)
        isTriggerAlignedWithPlayer = db.Column(db.Boolean, nullable=False, default=False)
        closestCwTriggerAngle = db.Column(db.Float, nullable=False, default=0.0)
        closestCwCcw = db.Column(db.Float, nullable=False, default=0.0)
        bestMovementOption = db.Column(db.Text, nullable=False, default="")
        referrer = db.Column(db.Text, nullable=False, default="")

    """
    class MultiDayCondition(db.Model):
        __tablename__ = "multi_day_condition"
        __bind_key__ = "multi"

        mTurkID = db.Column(db.Text, nullable=False, primary_key=True)
        condition = db.Column(db.Integer, nullable=False, default=-1)
    """

    return SHState, SHTrial, SHReplayEvent
