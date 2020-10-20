from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, IntegerField, SubmitField, SelectField
from wtforms.validators import DataRequired
# from flask_wtf.file import FileField, FileRequired, FileAllowed
from flask import request

class Search(FlaskForm):
    Input = StringField ('Input', validators=[DataRequired()])
    submit = SubmitField('Search For Overlapping Intervals')
