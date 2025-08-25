# blueprints/recruiter/routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime
from sqlalchemy import or_, func            # ⇐ func اضافه شد
from extensions import db
from models import User, Role, HiringCase, Document, VideoKYC, PhysicalChecklist
from forms.recruiter import CreateCaseForm
from forms.verification import VerifyDocForm
from services.sms import send_sms
from services.notify import inapp
from utils.normalize import norm_dict, norm_digits

recruiter_bp = Blueprint("recruiter", __name__, template_folder='../../templates')

# ------------------------ داشبورد + جست‌وجو ------------------------
@recruiter_bp.get("/dashboard")
@login_required
def dashboard():
    q = (request.args.get("q") or "").strip()
    qn = norm_digits(q)

    query = HiringCase.query
    query = query.outerjoin(User, HiringCase.candidate_id == User.id)

    if q:
        query = query.filter(
            or_(
                HiringCase.full_name.ilike(f"%{q}%"),
                HiringCase.national_id.ilike(f"%{qn}%"),
                User.mobile.ilike(f"%{qn}%"),
            )
        )

    qs = query.order_by(HiringCase.created_at.desc()).all()

    rows = []
    for c in qs:
        has_docs = Document.query.filter_by(case_id=c.id).count() > 0
        has_video = VideoKYC.query.filter_by(case_id=c.id).count() > 0
        has_physical = PhysicalChecklist.query.filter_by(case_id=c.id).count() > 0
        rows.append({"case": c, "has_docs": has_docs, "has_video": has_video, "has_physical": has_physical})

    # --- شمارنده‌ها برای سه دکمه‌ی بالای صفحه
    docs_total = (db.session.query(func.count(func.distinct(Document.case_id))).scalar() or 0)
    docs_pending = (db.session.query(func.count(func.distinct(Document.case_id)))
                    .filter((Document.verify_status.is_(None)) | (Document.verify_status == "pending"))
                    .scalar() or 0)

    videos_total = (db.session.query(func.count(VideoKYC.id)).scalar() or 0)
    videos_pending = (db.session.query(func.count(VideoKYC.id))
                      .filter((VideoKYC.review_status.is_(None)) | (VideoKYC.review_status == "pending"))
                      .scalar() or 0)

    phys_total = (db.session.query(func.count(PhysicalChecklist.id)).scalar() or 0)
    phys_pending = (db.session.query(func.count(PhysicalChecklist.id))
                    .filter((PhysicalChecklist.recruiter_verdict.is_(None)) | (PhysicalChecklist.recruiter_verdict == "incomplete"))
                    .scalar() or 0)

    stats = {
        "docs": {"total": docs_total, "pending": docs_pending},
        "videos": {"total": videos_total, "pending": videos_pending},
        "physical": {"total": phys_total, "pending": phys_pending},
    }

    return render_template("role_recruiter_dashboard.html", cases=rows, q=q, stats=stats)


# ------------------------ ایجاد پرونده (بدون تغییر در منطق فعلی) ------------------------
@recruiter_bp.route("/create", methods=["GET", "POST"])
@login_required
def create_case():
    form = CreateCaseForm()
    if form.validate_on_submit():
        data = norm_dict(request.form)  # اعداد فارسی/عربی → انگلیسی

        full_name   = data.get("full_name")
        national_id = data.get("national_id")
        mobile      = data.get("mobile")
        force       = (data.get("force_create") == "1")  # از مودال می‌آید

        # جلوگیری از پروندهٔ تکراریِ باز با همان کدملی
        dup_case = HiringCase.query.filter(
            HiringCase.national_id == national_id,
            HiringCase.status != "closed"
        ).first()
        if dup_case:
            # همان صفحه را نشان بده، اما با مودال هشدار
            modal = {
                "status": "failed",
                "title": "ثبت نشد",
                "text": "برای این کدملی یک پروندهٔ باز وجود دارد.",
            }
            return render_template("recruiter_create_case.html", form=form, modal=modal)

        # آیا کاربری با این موبایل از قبل هست؟
        existing_user = User.query.filter_by(mobile=mobile).first()
        if existing_user and not force:
            return render_template(
                "recruiter_create_case.html",
                form=form,
                dup_user=existing_user,
                show_dup_modal=True,
            )

        cand_role = Role.query.filter_by(name="candidate").first()
        if not cand_role:
            cand_role = Role(name="candidate")
            db.session.add(cand_role)
            db.session.commit()

        user = User(
            full_name=full_name,
            mobile=mobile,
            national_id=national_id,
            email=data.get("email"),
            role_id=cand_role.id,
        )
        db.session.add(user)
        db.session.flush()
        user.username = f"cand{user.id}"
        password = "Cand#2025"
        user.set_password(password)
        db.session.commit()

        case = HiringCase(
            candidate_id=user.id,
            created_by_id=current_user.id,
            full_name=full_name,
            national_id=national_id,
            contract_type=data.get("contract_type"),
            org_position=data.get("org_position"),
            degree=data.get("degree"),
            branch_manager_name=data.get("branch_manager_name"),
            branch_manager_mobile=data.get("branch_manager_mobile"),
            branch_manager_phone=data.get("branch_manager_phone"),
            branch_address=data.get("branch_address"),
            approved_salary_type=data.get("approved_salary_type"),
            approved_salary_amount=data.get("approved_salary_amount"),
            created_at=datetime.utcnow(),
        )
        db.session.add(case)
        db.session.commit()

        inapp(user.id, "case_created", {"case_id": case.id})

        login_url = request.host_url.rstrip("/") + url_for("auth.login")
        text = (
            "سامانه استخدام نیک و مهرآمن\n"
            f"نام کاربری: {user.username}\n"
            f"رمز عبور: Cand#2025\n"
            f"ورود: {login_url}"
        )
        try:
            ok = send_sms(user.mobile, text)
            flash(
                "پرونده ایجاد شد و پیامک ورود ارسال گردید." if ok else "پرونده ایجاد شد (ارسال پیامک ناموفق).",
                "success" if ok else "warning",
            )
        except Exception as e:
            flash(f"پرونده ایجاد شد (SMS خطا: {e})", "warning")

        return redirect(url_for("recruiter.dashboard"))

    # GET
    return render_template("recruiter_create_case.html", form=form)


@recruiter_bp.get("/user/<int:user_id>")
@login_required
def view_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        flash("کاربر یافت نشد.", "danger")
        return redirect(url_for("recruiter.dashboard"))
    return render_template("recruiter_user_info.html", user=user)


# ------------------------ صف بررسی مدارک (بدون uploaded_at) ------------------------
@recruiter_bp.get("/queue/docs")
@login_required
def docs_queue():
    q = (request.args.get("q") or "").strip()
    qn = norm_digits(q)

    base = db.session.query(HiringCase).join(Document, Document.case_id == HiringCase.id).distinct()

    if q:
        base = base.outerjoin(User, User.id == HiringCase.candidate_id).filter(
            or_(
                HiringCase.full_name.ilike(f"%{q}%"),
                HiringCase.national_id.ilike(f"%{qn}%"),
                User.mobile.ilike(f"%{qn}%"),
            )
        )

    cases = base.order_by(HiringCase.id.desc()).all()

    items = []
    for c in cases:
        cnt = db.session.query(func.count(Document.id)).filter_by(case_id=c.id).scalar() or 0
        items.append((c, cnt))

    return render_template("recruiter_docs_queue.html", items=items, q=q)


# ------------------------ بقیه‌ی روت‌ها (بدون تغییر) ------------------------
@recruiter_bp.get("/docs/<int:case_id>")
@login_required
def review_docs(case_id):
    docs = Document.query.filter_by(case_id=case_id).all()
    return render_template("recruiter_review_docs.html", docs=docs, case_id=case_id)

@recruiter_bp.post("/docs/<int:doc_id>/decision")
@login_required
def doc_decision(doc_id):
    form = VerifyDocForm()
    if form.validate_on_submit():
        doc = db.session.get(Document, doc_id)
        if not doc:
            flash("مدرک یافت نشد.", "danger")
        else:
            doc.verify_status = form.decision.data
            if form.decision.data == "rejected":
                doc.reject_code = form.reject_code.data
                doc.reject_reason = form.reject_reason.data
            db.session.commit()
            flash("نتیجه ثبت شد.", "success")
    else:
        flash("فرم نامعتبر است.", "warning")
    return redirect(request.referrer or url_for("recruiter.review_docs", case_id=doc.case_id if 'doc' in locals() and doc else None))

@recruiter_bp.get("/videos")
@login_required
def videos_queue():
    vids = VideoKYC.query.order_by(VideoKYC.submitted_at.desc()).all()
    return render_template("recruiter_videos.html", vids=vids)

@recruiter_bp.post("/video/<int:vid_id>/decision")
@login_required
def review_video(vid_id):
    form = VerifyDocForm()
    if form.validate_on_submit():
        v = db.session.get(VideoKYC, vid_id)
        if not v:
            flash("ویدیو یافت نشد.", "danger")
        else:
            v.review_status = form.decision.data
            if form.decision.data == "rejected":
                v.reject_code = form.reject_code.data
                v.reject_reason = form.reject_reason.data
            db.session.commit()
            flash("نتیجهٔ بررسی ویدیو ثبت شد.", "success")
    else:
        flash("فرم نامعتبر است.", "warning")
    return redirect(request.referrer or url_for("recruiter.videos_queue"))

@recruiter_bp.get("/physical")
@login_required
def physical_queue():
    items = PhysicalChecklist.query.order_by(PhysicalChecklist.id.desc()).all()
    return render_template("recruiter_physical.html", items=items)

@recruiter_bp.post("/physical/<int:item_id>/decision")
@login_required
def review_physical(item_id):
    form = VerifyDocForm()
    if form.validate_on_submit():
        pc = db.session.get(PhysicalChecklist, item_id)
        if not pc:
            flash("رکورد یافت نشد.", "danger")
        else:
            pc.recruiter_verdict = form.decision.data if form.decision.data in ["approved","rejected"] else "incomplete"
            pc.verdict_at = datetime.utcnow()
            pc.verdict_reason = form.reject_reason.data
            db.session.commit()
            flash("نتیجهٔ تحویل فیزیکی ثبت شد.", "success")
    else:
        flash("فرم نامعتبر است.", "warning")
    return redirect(request.referrer or url_for("recruiter.physical_queue"))

@recruiter_bp.post("/case/<int:case_id>/close")
@login_required
def close_case(case_id):
    c = db.session.get(HiringCase, case_id)
    if not c:
        flash("پرونده یافت نشد.", "danger")
    else:
        c.status = "closed"
        db.session.commit()
        flash("پرونده بسته شد.", "success")
    return redirect(url_for("recruiter.dashboard"))
# --- حذف پرونده ---
@recruiter_bp.post("/case/<int:case_id>/delete")
@login_required
def delete_case_hard(case_id):
    from models import Document, VideoKYC, PhysicalChecklist
    case = db.session.get(HiringCase, case_id)
    if not case:
        flash("پرونده یافت نشد.", "danger")
        return redirect(url_for("recruiter.dashboard"))

    # حذف ساده‌ی وابسته‌ها (اگر کَسکِید ندارید)
    Document.query.filter_by(case_id=case_id).delete(synchronize_session=False)
    VideoKYC.query.filter_by(case_id=case_id).delete(synchronize_session=False)
    PhysicalChecklist.query.filter_by(case_id=case_id).delete(synchronize_session=False)

    db.session.delete(case)
    db.session.commit()
    flash("پرونده حذف شد.", "success")
    return redirect(url_for("recruiter.dashboard"))

