
from extensions import db
from flask_login import UserMixin
from passlib.hash import bcrypt
from datetime import datetime

class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120))
    mobile = db.Column(db.String(20), index=True, nullable=True)
    email = db.Column(db.String(120))
    username = db.Column(db.String(120), unique=True)
    national_id = db.Column(db.String(20), unique=True)
    password_hash = db.Column(db.String(255))
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), nullable=False)
    role = db.relationship('Role')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = bcrypt.hash(password)

    def check_password(self, password):
        # Hotfix: support legacy/plain passwords in DB
        try:
            return bcrypt.verify(password, self.password_hash)
        except Exception:
            # If stored value isn't a bcrypt hash (legacy plain text), compare directly
            return self.password_hash == password

class Setting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.JSON, nullable=False)

    @staticmethod
    def get(key, default=None):
        s = Setting.query.filter_by(key=key).first()
        return s.value if s else default

    @staticmethod
    def set(key, value):
        s = Setting.query.filter_by(key=key).first()
        if not s:
            s = Setting(key=key, value=value)
            db.session.add(s)
        else:
            s.value = value
        db.session.commit()

from enum import Enum

class CaseStatus(Enum):
    DRAFT = "draft"
    CANDIDATE_COMPLETE = "candidate_complete"
    DOCS_REVIEW = "docs_review"
    HR_ISSUE_DECREE = "hr_issue_decree"
    VIDEO_REQUESTED = "video_requested"
    VIDEO_REVIEW = "video_review"
    PHYSICAL_DELIVERY = "physical_delivery"
    PHYSICAL_REVIEW = "physical_review"
    IT_PR_FINANCE = "it_pr_finance"
    CLOSED = "closed"

class HiringCase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    candidate = db.relationship('User', foreign_keys=[candidate_id])
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_by = db.relationship('User', foreign_keys=[created_by_id])
    status = db.Column(db.String(50), default=CaseStatus.DRAFT.value)
    current_step = db.Column(db.Integer, default=0)
    national_id = db.Column(db.String(20))  # quick access
    contract_type = db.Column(db.String(20))  # hourly/fulltime
    org_position = db.Column(db.String(100))
    degree = db.Column(db.String(50))
    branch_manager_mobile = db.Column(db.String(20))
    branch_address = db.Column(db.String(200))
    recruiter_phone = db.Column(db.String(20))
    approved_salary_type = db.Column(db.String(50))
    approved_salary_amount = db.Column(db.Integer)
    version = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class CandidateProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    marital_status = db.Column(db.String(20))  # single/married
    has_children = db.Column(db.Boolean, default=False)
    gender = db.Column(db.String(10))
    military_status = db.Column(db.String(100))
    address = db.Column(db.String(255))
    education = db.Column(db.String(100))
    bank_iban = db.Column(db.String(30))
    bank_card = db.Column(db.String(30))
    insurance_status = db.Column(db.String(50))

class FamilyMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    type = db.Column(db.String(20))  # spouse|child
    full_name = db.Column(db.String(120))
    relation = db.Column(db.String(20))
    birth_date_jalali = db.Column(db.String(10))
    gender = db.Column(db.String(10))
    married = db.Column(db.Boolean, default=False)

class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey('hiring_case.id'), nullable=False)
    type = db.Column(db.String(50))  # enums like national_card_front, etc.
    file_path = db.Column(db.String(255))
    mime = db.Column(db.String(50))
    size = db.Column(db.Integer)
    checksum = db.Column(db.String(128))
    verify_status = db.Column(db.String(20), default="pending")
    reject_code = db.Column(db.String(50))
    reject_reason = db.Column(db.Text)
    max_size_hint = db.Column(db.Integer)  # bytes (UI hint)

class HRDecree(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey('hiring_case.id'), nullable=False)
    personnel_code = db.Column(db.String(30))
    start_date_jalali = db.Column(db.String(10))
    end_date_jalali = db.Column(db.String(10))
    duration_months = db.Column(db.Integer)
    job_title = db.Column(db.String(100))
    job_post = db.Column(db.String(100))
    org_grade = db.Column(db.String(100))
    org_unit = db.Column(db.String(100))
    base_salary = db.Column(db.Integer, default=0)
    attraction_allowance = db.Column(db.Integer, default=0)
    job_extra = db.Column(db.Integer, default=0)
    years_of_service = db.Column(db.Integer, default=0)
    experience_allowance = db.Column(db.Integer, default=0)
    education_allowance = db.Column(db.Integer, default=0)
    base_total = db.Column(db.Integer, default=0)
    housing = db.Column(db.Integer, default=0)
    food = db.Column(db.Integer, default=0)
    child_allowance = db.Column(db.Integer, default=0)
    marital = db.Column(db.Integer, default=0)
    commute = db.Column(db.Integer, default=0)
    other = db.Column(db.Integer, default=0)
    benefits_total = db.Column(db.Integer, default=0)
    grand_total = db.Column(db.Integer, default=0)
    calc_log_json = db.Column(db.JSON)
    version = db.Column(db.Integer, default=1)

class VideoKYC(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey('hiring_case.id'), nullable=False)
    file_path = db.Column(db.String(255))
    duration_sec = db.Column(db.Integer)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    review_status = db.Column(db.String(20), default="pending")
    reject_code = db.Column(db.String(50))
    reject_reason = db.Column(db.Text)

class PhysicalChecklist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey('hiring_case.id'), nullable=False)
    tracking_code = db.Column(db.String(50))
    candidate_marked_delivered_at = db.Column(db.DateTime)
    recruiter_verdict = db.Column(db.String(20))  # approved|incomplete|rejected
    verdict_at = db.Column(db.DateTime)
    verdict_reason = db.Column(db.Text)

class ITProvision(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey('hiring_case.id'), nullable=False)
    accounts_sent_json = db.Column(db.JSON)
    sent_to_candidate_at = db.Column(db.DateTime)

class PROnboarding(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey('hiring_case.id'), nullable=False)
    fields_json = db.Column(db.JSON)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    to_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    channel = db.Column(db.String(20), default="inapp")  # inapp|sms|email
    template_key = db.Column(db.String(50))
    payload_json = db.Column(db.JSON)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    delivery_state = db.Column(db.String(20), default="sent")
    read_at = db.Column(db.DateTime)

# Helper to initialize default constants
def seed_default_constants():
    defaults = {
        "constants": {
            "base_yearly_unit": 2100000,        # پایه سنوات واحد
            "housing_allowance": 9000000,       # حق مسکن
            "food_allowance": 14000000,         # بن
            "per_child_allowance": 7166184,     # حق اولاد هر فرزند
            "marital_allowance": 5000000        # تاهل
        },
        "document_limits": {
            "birth_cert": {"max_mb": 5, "types": ["pdf","jpg","png"]},
            "national_card": {"max_mb": 5, "types": ["jpg","png"]},
            "spouse_id": {"max_mb": 5, "types": ["pdf","jpg","png"]},
            "child_id": {"max_mb": 5, "types": ["pdf","jpg","png"]},
            "education_last": {"max_mb": 10, "types": ["pdf"]},
            "bank": {"max_mb": 10, "types": ["pdf","jpg","png"]},
            "insurance": {"max_mb": 10, "types": ["pdf","jpg","png"]},
            "military": {"max_mb": 10, "types": ["pdf","jpg","png"]},
            "property_lease": {"max_mb": 20, "types": ["pdf","jpg","png"]},
            "utility_bill": {"max_mb": 20, "types": ["pdf","jpg","png"]},
            "video_kyc": {"max_mb": 250, "types": ["mp4"]}
        }
    }
    if not Setting.query.filter_by(key="app_config").first():
        db.session.add(Setting(key="app_config", value=defaults))
        db.session.commit()
