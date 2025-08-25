from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, HiddenField
from wtforms.validators import DataRequired, Optional, Email

class CreateCaseForm(FlaskForm):
    full_name = StringField('نام و نام خانوادگی', validators=[DataRequired()])
    father_name = StringField('نام پدر', validators=[DataRequired()])
    national_id = StringField('کد ملی', validators=[DataRequired()])
    mobile = StringField('موبایل متقاضی', validators=[DataRequired()])
    email = StringField('ایمیل', validators=[Optional(), Email()])
    home_address = StringField('آدرس محل سکونت', validators=[Optional()])
    gender = SelectField('جنسیت', choices=[('male','مرد'),('female','زن')], validators=[DataRequired()])
    marital_status = SelectField('وضعیت تاهل', choices=[('single','مجرد'),('married','متاهل')], validators=[DataRequired()])
    military_status = SelectField('وضعیت خدمتی', choices=[
        ('finished','دارای کارت پایان خدمت'),
        ('permanent_exempt','دارای کارت معافیت دائم'),
        ('temporary_exempt','دارای معافیت موقت'),
        ('liable','مشمول خدمت'),
        ('serving','در حال انجام خدمت'),
        ('age_exempt','معافیت سنی'),
        ('absent','غایب'),
    ], validators=[Optional()])
    contract_type = SelectField('نوع قرارداد', choices=[('hourly','ساعتی'),('fulltime','تمام وقت')], validators=[DataRequired()])
    org_position = StringField('سمت سازمانی', validators=[Optional()])
    degree = SelectField('مدرک تحصیلی', choices=[
        ('diploma','دیپلم'),
        ('associate','کاردانی'),
        ('bachelor','کارشناسی'),
        ('master','کارشناسی ارشد'),
        ('doctorate','دکتری'),
    ], validators=[Optional()])
    branch_manager_mobile = StringField('موبایل مدیر شعبه', validators=[Optional()])
    branch_address = StringField('آدرس شعبه', validators=[Optional()])
    recruiter_phone = StringField('شماره تماس ادمین جذب', validators=[Optional()])
    approved_salary_type = SelectField('نوع حقوق', choices=[('monthly','ماهانه'),('daily','روزانه')], validators=[Optional()])
    approved_salary_amount = StringField('حقوق تایید شده', validators=[Optional()])
    force_create = HiddenField()
