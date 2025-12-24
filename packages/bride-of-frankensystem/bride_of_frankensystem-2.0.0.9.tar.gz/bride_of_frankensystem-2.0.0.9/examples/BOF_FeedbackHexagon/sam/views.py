from flask import Blueprint, render_template, session, request
from BOFS.util import verify_correct_page, verify_session_valid
from BOFS.globals import db

sam = Blueprint('sam', __name__,
                url_prefix='/sam',
                static_url_path='/sam',
                static_folder='static',
                template_folder='templates')


EXPORT = [
    {
        'table': 'LogSAM',
        'fields': {
            'arousal': 'avg(arousal)',
            'valence': 'avg(valence)',
        },
        'group_by': 'tag'
    }
]


@sam.route("/<tag>", methods=['GET', 'POST'])
@verify_session_valid
@verify_correct_page
def self_assessment_manikin(tag=""):
    return render_template("task_sam_arousal_valence.html", tag=tag)


@sam.route("/log_sam", methods=['POST'])
def log_sam():
    message = request.form['message']
    if message == "logSAM":
        log_entry = db.LogSAM()
        pid = request.form['pid']
        #if db.session.query(db.LogSAM).filter(db.LogSAM.participantID == pid).first() is not None:
        #    print("There is already a SAM db entry for pid={pid}".format(pid=pid))
        #    return ""
        # log_entry.participantID = session['participantID']
        log_entry.tag = request.form['tag']
        log_entry.participantID = pid
        log_entry.arousal = request.form['arousal']
        log_entry.valence = request.form['valence']
        log_entry.dominance = 0  #= request.form['dominance']

        db.session.add(log_entry)
        db.session.commit()
    return ""
