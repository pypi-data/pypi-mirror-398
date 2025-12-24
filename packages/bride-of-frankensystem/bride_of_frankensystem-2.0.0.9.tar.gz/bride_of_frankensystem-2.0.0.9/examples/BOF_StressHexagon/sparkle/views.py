from flask import Blueprint, render_template, request, session, redirect, jsonify
from BOFS import db
from BOFS.globals import tables
from BOFS.util import *
from datetime import timedelta, datetime
from flask import make_response, request, current_app
from functools import update_wrapper
from BOFS.admin.util import verify_admin

sparkle = Blueprint('sparkle', __name__,
                    static_url_path='/sparkle',
                    static_folder='static',
                    template_folder='templates')

@sparkle.get("/sparkle")
@verify_correct_page
@verify_session_valid
def route_sparkle():
    return render_template("sparkle.html")


@sparkle.post("/sparkle_log")
@verify_session_valid
def route_pasat_log():

    score = request.form['score']

    entry = tables['sparkle'].dbClass()
    entry.participantID = session['participantID']
    entry.score = score

    db.session.add(entry)
    db.session.commit()
    return ""