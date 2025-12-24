from flask import Blueprint, render_template, request, session, redirect, jsonify
from BOFS import db
from BOFS.globals import tables
from BOFS.util import *
from datetime import timedelta, datetime
from flask import make_response, request, current_app
from functools import update_wrapper
from BOFS.admin.util import verify_admin

condition_from_csv = Blueprint('condition_from_csv', __name__,
                               static_url_path='/condition_from_csv',
                               static_folder='static',
                               template_folder='templates')


@condition_from_csv.get("/condition_from_csv")
@verify_correct_page
@verify_session_valid
def route_condition_from_csv():
    mTurkID = session['mTurkID']
    p = db.session.query(db.Participant).get(session['participantID'])

    with open('conditions_by_external_id.csv') as file:
        file.readline()  # Read the header

        for line in file:
            line = line.strip()
            externalID, condition = line.split(',')

            if externalID == mTurkID:  # We found the line with our participant
                p.condition = int(condition)
                db.session.commit()
                session['condition'] = p.condition
                return redirect("/redirect_from_page/condition_from_csv")

    return render_template("error.html")

