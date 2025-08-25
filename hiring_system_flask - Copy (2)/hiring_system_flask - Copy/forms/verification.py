from flask_wtf import FlaskForm
from wtforms import SubmitField, SelectField, TextAreaField
from wtforms.validators import Optional

class VerifyDocForm(FlaskForm):
    decision = SelectField("نتیجه", choices=[("approved","تأیید"),("rejected","رد")])
    reject_code = SelectField("کد علت رد", choices=[("incomplete","ناقص"),("unreadable","ناخوانا"),("invalid","نامعتبر")])
    reject_reason = TextAreaField("توضیح", validators=[Optional()])
    submit = SubmitField("ثبت نتیجه")
