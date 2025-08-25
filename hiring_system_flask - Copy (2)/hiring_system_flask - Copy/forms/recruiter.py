# forms/recruiter.py
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, TextAreaField, DecimalField, HiddenField
from wtforms.validators import DataRequired, Length, Optional, Email, NumberRange, ValidationError

class CreateCaseForm(FlaskForm):
    # مشخصات هویتی و تماس
    full_name = StringField("نام و نام خانوادگی", validators=[DataRequired(), Length(max=120)])
    father_name = StringField("نام پدر", validators=[Optional(), Length(max=120)])
    national_id = StringField("کدملی", validators=[DataRequired(), Length(min=10, max=20)])
    mobile = StringField("موبایل", validators=[DataRequired(), Length(min=8, max=20)])
    email = StringField("ایمیل", validators=[Optional(), Email(), Length(max=120)])
    home_address = TextAreaField("آدرس محل سکونت", validators=[Optional(), Length(max=500)])

    # وضعیت‌های فردی
    gender = SelectField("جنسیت", choices=[("male","مرد"),("female","زن")], validators=[DataRequired()])
    marital_status = SelectField("وضعیت تأهل", choices=[("single","مجرد"),("married","متأهل")], validators=[DataRequired()])
    military_status = SelectField("وضعیت خدمت", choices=[
        ("", "— انتخاب کنید —"),
        ("done","پایان خدمت/معافیت دائم"),
        ("exempt","معافیت"),
        ("inprogress","درحال انجام/نامشخص"),
    ], validators=[Optional()])

    # سازمان و قرارداد
    contract_type = SelectField("نوع قرارداد", choices=[("full_time","تمام‌وقت"),("hourly","ساعتی")], validators=[DataRequired()])
    org_position = StringField("سمت سازمانی", validators=[DataRequired(), Length(max=120)])
    degree = SelectField("مدرک تحصیلی", choices=[
        ("diploma","دیپلم"),
        ("associate","کاردانی"),
        ("bachelor","کارشناسی"),
        ("master","کارشناسی ارشد"),
        ("phd","دکتری"),
    ], validators=[DataRequired()])

    # شعبه
    branch_manager_name = StringField("نام مدیر شعبه", validators=[Optional(), Length(max=120)])
    branch_manager_mobile = StringField("موبایل مدیر شعبه", validators=[Optional(), Length(max=20)])
    branch_manager_phone = StringField("شماره تماس مدیر", validators=[Optional(), Length(max=20)])
    branch_address = TextAreaField("آدرس شعبه", validators=[Optional(), Length(max=500)])

    # حقوق
    approved_salary_type = SelectField("نوع حقوق", choices=[("fixed","ثابت/ماهیانه"),("hourly","ساعتی")], validators=[DataRequired()])
    approved_salary_amount = DecimalField("حقوق تاییدشده", places=0, validators=[Optional(), NumberRange(min=0)])

    # کنترل ساخت با موبایل تکراری (از مودال تأیید)
    force_create = HiddenField(default="0")

    # اعتبارسنجی شرطی: اگر جنسیت «مرد» بود، وضعیت خدمت اجباری است
    def validate_military_status(self, field):
        if self.gender.data == "male" and not field.data:
            raise ValidationError("انتخاب وضعیت خدمت اجباری است.")
