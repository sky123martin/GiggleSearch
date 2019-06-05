from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, IntegerField, SubmitField, SelectField
from wtforms.validators import DataRequired

class SearchForm(FlaskForm):
    lowerBound = IntegerField('Lower Bound', validators=[DataRequired()])
    upperBound = IntegerField('Upper Bound', validators=[DataRequired()])
    region = StringField ('Region', validators=[DataRequired()])
    dataSource = SelectField(u'Data Source', choices=[('rme','RME'), ('ucsc','UCSC')])
    submit = SubmitField('Search')

class FilterResultsForm(FlaskForm):
    Ascending = BooleanField('Order Ascending')
    sortBy = SelectField(u'Sort By', choices=[('0','Name'), ('2','Overlap'), 
                                                ('1','Total Regions'), ('3','% Overlapping')])
    submit = SubmitField('Refine')