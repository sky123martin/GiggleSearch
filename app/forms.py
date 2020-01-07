from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, IntegerField, SubmitField, SelectField
from wtforms.validators import DataRequired
from flask_wtf.file import FileField, FileRequired, FileAllowed
from flask import request

class SearchForm(FlaskForm):
    lowerBound = IntegerField('Lower Bound', validators=[DataRequired()])
    upperBound = IntegerField('Upper Bound', validators=[DataRequired()])
    region = StringField ('Region', validators=[DataRequired()])
    dataSource = SelectField(u'Data Source', choices=[('ucsc','UCSC')])
    submit = SubmitField('Search')

class Search(FlaskForm):
    Input = StringField ('Input', validators=[DataRequired()])
    submit = SubmitField('Search For Overlapping Intervals')

# class FilterResultsForm(FlaskForm):
#     ascending = BooleanField('Order Ascending')
#     sortBy = SelectField(u'Sort By', choices=[('0','Name'), ('2','Overlap'), 
#                                                 ('1','Total Regions'), ('3','% Overlapping')])
#     submit = SubmitField('Refine')

# class UploadForm(FlaskForm):
#     file = FileField()
#     submit = SubmitField('Search')

# class FileUploadForm(FlaskForm):
#     file = FileField(validators=[FileRequired(), FileAllowed(['bed','bed.gz'], 'Bed files only!')])
#     submit = SubmitField('Search')