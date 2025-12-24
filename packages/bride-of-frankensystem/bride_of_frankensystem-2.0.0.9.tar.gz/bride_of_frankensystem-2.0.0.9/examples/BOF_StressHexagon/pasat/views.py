from flask import Blueprint, render_template, request, session, redirect, jsonify
from BOFS import db
from BOFS.globals import tables
from BOFS.util import *
from datetime import timedelta, datetime
from flask import make_response, request, current_app
from functools import update_wrapper
from BOFS.admin.util import verify_admin


pasat = Blueprint('pasat', __name__,
                  static_url_path='/pasat',
                  static_folder='static',
                  template_folder='templates')


@pasat.get("/pasat")
@verify_correct_page
@verify_session_valid
def route_pasat():
    return render_template("pasat.html")


@pasat.post("/pasat_log")
@verify_session_valid
def route_pasat_log():
    if 'log' not in request.files:
        return ""

    lines = request.files['log'].stream.readlines()
    full_log = ""

    for line in lines:
        full_log += line.decode('utf-8')

    for event_line in full_log.split('\n'):
        columns = event_line.split('|')

        if len(columns) <= 1:
            continue

        entry = tables['pasat'].dbClass()
        entry.participantID = session['participantID']
        entry.trialId = int_or_0(columns[0])
        entry.firstDigit = float_or_0(columns[1])
        entry.secondDigit = float_or_0(columns[2])
        entry.timeOut = columns[3].lower == 'true'
        entry.timeInTask = float_or_0(columns[4])
        entry.successful = columns[5].lower() == 'true'

        db.session.add(entry)

    db.session.commit()
    return ""