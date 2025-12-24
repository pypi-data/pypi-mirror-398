def create(db):
    class LogSAM(db.Model):
        __tablename__ = "log_sam"

        logSAMID = db.Column(db.Integer, primary_key=True, autoincrement=True)
        participantID = db.Column(db.Integer, db.ForeignKey('participant.participantID'))
        tag = db.Column(db.Text, nullable=False, default=0)
        arousal = db.Column(db.Integer, nullable=False, default=0)
        valence = db.Column(db.Integer, nullable=False, default=0)
        dominance = db.Column(db.Integer, nullable=False, default=0)

    return LogSAM
