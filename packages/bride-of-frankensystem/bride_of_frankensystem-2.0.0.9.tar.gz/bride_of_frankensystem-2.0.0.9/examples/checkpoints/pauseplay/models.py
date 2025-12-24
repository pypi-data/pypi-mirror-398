from datetime import datetime
from sqlalchemy.orm import relationship


def create(db):
    class PausePlayLevels(db.Model):
        __tablename__ = "pauseplay_levels"

        levelID = db.Column(db.Integer, primary_key=True, autoincrement=True)
        participantID = db.Column(db.Integer, db.ForeignKey('participant.participantID'))
        finishedLevel = db.Column(db.Integer, nullable=False, default=0)
        levelName = db.Column(db.String, nullable=False, default=0)
        levelNumber = db.Column(db.Integer, nullable=False, default=0)
        levelTime = db.Column(db.Float, nullable=False, default=0)
        gameTime = db.Column(db.Float, nullable=False, default=0)
        coinsCollected = db.Column(db.Integer, nullable=False, default=0)
        playSession = db.Column(db.Integer, nullable=False, default=0)
        maxTime = db.Column(db.Float, nullable=False, default=0)
        levelCompletePercent = db.Column(db.Integer, nullable=False, default=0)
        breakType = db.Column(db.Integer, nullable=False, default=0)
        deathCount = db.Column(db.Integer, nullable=False, default=0)
        averageFPS = db.Column(db.Float, nullable=False, default=0)
        sessionName = db.Column(db.String, nullable=False, default="")

    class PausePlayProgress(db.Model):
        __tablename__ = "pauseplay_progress"

        deathID = db.Column(db.Integer, primary_key=True, autoincrement=True)
        participantID = db.Column(db.Integer, db.ForeignKey('participant.participantID'))
        levelName = db.Column(db.String, nullable=False, default=0)
        levelNumber = db.Column(db.Integer, nullable=False, default=0)
        levelTime = db.Column(db.Float, nullable=False, default=0)
        gameTime = db.Column(db.Float, nullable=False, default=0)
        playSession = db.Column(db.Integer, nullable=False, default=0)
        collidedWith = db.Column(db.String, nullable=False, default="")
        x = db.Column(db.Float, nullable=False, default=0)
        y = db.Column(db.Float, nullable=False, default=0)
        sessionName = db.Column(db.String, nullable=False, default="")
        progressType = db.Column(db.String, nullable=False, default="")
        timeToWait = db.Column(db.Float, nullable=False, default=0)

    return PausePlayLevels, PausePlayProgress
