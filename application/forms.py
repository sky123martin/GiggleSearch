from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, IntegerField, SubmitField, SelectField
from wtforms.validators import DataRequired
from flask_wtf.file import FileField, FileRequired, FileAllowed
from flask import request

class intervalForm(FlaskForm):
    interval = StringField ('intervals', validators=[DataRequired()])
    refGenome = StringField ('refGenome')
    submit = SubmitField('Search For Overlapping Intervals')

class Search(FlaskForm):
    Input = StringField ('Input', validators=[DataRequired()])
    submit = SubmitField('Search For Overlapping Intervals')

class fileForm(FlaskForm):
    file = FileField(validators=[FileRequired(), FileAllowed(['bed'], 'Bed files only!')])
# from flask_wtf.file import FileField, FileRequired, FileAllowed

