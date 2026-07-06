from flask import (render_template, redirect, url_for, flash, request, Blueprint, current_app)
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from .forms import RegisterForm, LoginForm, ComplaintForm, CategoryForm, UpdateStatusForm, CommentForm
from .models import User, Category, Complaint, ComplaintHistory, Comment, Notification
from datetime import datetime, timedelta
from flask import send_file
from app.utils.report_generator import generate_pdf, generate_excel
from . import db
from sqlalchemy import or_
from sqlalchemy import func
from flask import jsonify
import os
import uuid
from werkzeug.utils import secure_filename

main = Blueprint("main", __name__)


@main.route("/")
def home():
    return render_template("index.html")

@main.route("/register", methods=["GET", "POST"])
def register():

    form = RegisterForm()

    if form.validate_on_submit():

        existing_user = User.query.filter_by(email=form.email.data).first()

        if existing_user:
            flash("Email already exists!", "danger")
            return redirect(url_for("main.register"))

        hashed_password = generate_password_hash(form.password.data)

        user = User(
            name=form.name.data,
            email=form.email.data,
            password=hashed_password,
            department=form.department.data,
            contact_number=form.contact_number.data,
            role="student"
        )

        db.session.add(user)
        db.session.commit()

        flash("Registration Successful!", "success")

        return redirect(url_for("main.login"))

    flash("Email already exists!", "danger")
    return render_template("auth/register.html", form=form)


@main.route("/login", methods=["GET", "POST"])
def login():

    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    form = LoginForm()

    if form.validate_on_submit():

        user = User.query.filter_by(email=form.email.data).first()

        if user and check_password_hash(user.password, form.password.data):

            login_user(user)

            flash("Login Successful!", "success")

            return redirect(url_for("main.dashboard"))

        flash("Invalid Email or Password!", "danger")

    return render_template("auth/login.html", form=form)


@main.route("/dashboard")
@login_required
def dashboard():

    total = Complaint.query.filter_by(student_id=current_user.id).count()

    pending = Complaint.query.filter_by(
        student_id=current_user.id,
        status="Pending"
    ).count()

    progress = Complaint.query.filter_by(
        student_id=current_user.id,
        status="In Progress"
    ).count()

    resolved = Complaint.query.filter_by(
        student_id=current_user.id,
        status="Resolved"
    ).count()

    complaints = Complaint.query.filter_by(
        student_id=current_user.id
    ).order_by(
        Complaint.created_at.desc()
    ).limit(5).all()

    # Monthly Analytics
    monthly_data = (
        db.session.query(
            func.strftime("%m", Complaint.created_at),
            func.count(Complaint.id)
        )
        .filter(Complaint.student_id == current_user.id)
        .group_by(func.strftime("%m", Complaint.created_at))
        .all()
    )

    month_names = {
        "01":"Jan","02":"Feb","03":"Mar","04":"Apr",
        "05":"May","06":"Jun","07":"Jul","08":"Aug",
        "09":"Sep","10":"Oct","11":"Nov","12":"Dec"
    }

    months = []
    monthly_counts = []

    for month, count in monthly_data:
        months.append(month_names[month])
        monthly_counts.append(count)

    # Weekly Analytics
    today = datetime.utcnow()

    weekly_labels = []
    weekly_values = []

    for i in range(6, -1, -1):

        day = today - timedelta(days=i)

        count = Complaint.query.filter(
            Complaint.student_id == current_user.id,
            func.date(Complaint.created_at) == day.date()
        ).count()

        weekly_labels.append(day.strftime("%a"))
        weekly_values.append(count)


    return render_template(
        "dashboard.html",
        total=total,
        pending=pending,
        progress=progress,
        resolved=resolved,
        complaints=complaints,
         months=months,
        monthly_counts=monthly_counts,
        weekly_labels=weekly_labels,
        weekly_values=weekly_values
    )


@main.route("/complaint/add", methods=["GET", "POST"])
@login_required
def add_complaint():

    form = ComplaintForm()

    # Load categories into dropdown
    form.category.choices = [
        (category.id, category.category_name)
        for category in Category.query.order_by(Category.category_name).all()
    ]

    if form.validate_on_submit():

        filename = None

    if form.attachment.data:

        file = form.attachment.data

        extension = file.filename.rsplit(".", 1)[1].lower()

        filename = (
            str(uuid.uuid4()) +
            "." +
            extension
        )

        file.save(
            os.path.join(
                current_app.config["UPLOAD_FOLDER"],
                filename
            )
        )

        complaint = Complaint(
            student_id=current_user.id,
            category_id=form.category.data,
            title=form.title.data,
            description=form.description.data,
            attachment=filename,
            status="Pending"
        )

        db.session.add(complaint)

        db.session.flush()

        history = ComplaintHistory(
            complaint_id=complaint.id,
            status="Pending",
            remark="Complaint submitted by student."
        )

        db.session.add(history)

        # Notify all admins
        admins = User.query.filter_by(role="admin").all()

        for admin in admins:

            notification = Notification(
                user_id=admin.id,
                complaint_id=complaint.id,
                message=f"New complaint submitted by {current_user.name}"
            )

            db.session.add(notification)


        db.session.commit()

        flash("Complaint submitted successfully!", "success")

        return redirect(url_for("main.dashboard"))

    return render_template("complaint/add_complaint.html", form=form)


@main.route("/complaints")
@login_required
def my_complaints():

    complaints = Complaint.query.filter_by(
        student_id=current_user.id
    ).order_by(Complaint.created_at.desc()).all()

    return render_template(
        "complaint/my_complaints.html",
        complaints=complaints
    )


@main.route("/complaint/<int:complaint_id>")
@login_required
def view_complaint(complaint_id):

    complaint = Complaint.query.get_or_404(complaint_id)

    if complaint.student_id != current_user.id:
        flash("You are not authorized to view this complaint.", "danger")
        return redirect(url_for("main.my_complaints"))

    form = CommentForm()

    return render_template(
        "complaint/view_complaint.html",
        complaint=complaint,
        form=form
    )


@main.route("/complaint/edit/<int:complaint_id>", methods=["GET", "POST"])
@login_required
def edit_complaint(complaint_id):

    complaint = Complaint.query.get_or_404(complaint_id)

    # Check ownership
    if complaint.student_id != current_user.id:
        flash("You are not authorized to edit this complaint.", "danger")
        return redirect(url_for("main.my_complaints"))

    # Only pending complaints can be edited
    if complaint.status != "Pending":
        flash("Only pending complaints can be edited.", "warning")
        return redirect(url_for("main.my_complaints"))

    form = ComplaintForm()

    # Load category choices
    form.category.choices = [
        (category.id, category.category_name)
        for category in Category.query.order_by(Category.category_name).all()
    ]

    if form.validate_on_submit():

        complaint.category_id = form.category.data
        complaint.title = form.title.data
        complaint.description = form.description.data

    if form.attachment.data:

        if complaint.attachment:

            old_file = os.path.join(
                current_app.config["UPLOAD_FOLDER"],
                complaint.attachment
            )

            if os.path.exists(old_file):
                os.remove(old_file)

        file = form.attachment.data

        extension = file.filename.rsplit(".", 1)[1].lower()

        filename = (
            str(uuid.uuid4()) +
            "." +
            extension
        )

        file.save(
            os.path.join(
                current_app.config["UPLOAD_FOLDER"],
                filename
            )
        )

        complaint.attachment = filename

    db.session.commit()

    flash(
        "Complaint updated successfully!",
        "success"
    )

    return render_template(
        "complaint/edit_complaint.html",
        form=form,
        complaint=complaint
    )

    return redirect(
        url_for("main.my_complaints")
    )


@main.route("/complaint/delete/<int:complaint_id>")
@login_required
def delete_complaint(complaint_id):

    complaint = Complaint.query.get_or_404(complaint_id)

    # Check ownership
    if complaint.student_id != current_user.id:
        flash("You are not authorized to delete this complaint.", "danger")
        return redirect(url_for("main.my_complaints"))

    # Allow deletion only if pending
    if complaint.status != "Pending":
        flash("Only pending complaints can be deleted.", "warning")
        return redirect(url_for("main.my_complaints"))

    if complaint.attachment:

        file_path = os.path.join(
            current_app.config["UPLOAD_FOLDER"],
            complaint.attachment
        )

    if os.path.exists(file_path):
        os.remove(file_path)

    db.session.delete(complaint)
    db.session.commit()

    flash("Complaint deleted successfully!", "success")

    return redirect(url_for("main.my_complaints"))

# Admin Routes

@main.route("/admin/login", methods=["GET", "POST"])
def admin_login():

    if current_user.is_authenticated:

        if current_user.role == "admin":
            return redirect(url_for("main.admin_dashboard"))

        return redirect(url_for("main.dashboard"))

    form = LoginForm()

    if form.validate_on_submit():

        user = User.query.filter_by(email=form.email.data).first()

        if (
            user
            and user.role == "admin"
            and check_password_hash(user.password, form.password.data)
        ):

            login_user(user)

            flash("Welcome Admin!", "success")

            return redirect(url_for("main.admin_dashboard"))

        flash("Invalid admin credentials!", "danger")

    return render_template("admin/admin_login.html", form=form)


@main.route("/admin/dashboard")
@login_required
def admin_dashboard():

    if current_user.role != "admin":

        flash("Access Denied!", "danger")

        return redirect(url_for("main.dashboard"))

    total_students = User.query.filter_by(role="student").count()

    total_categories = Category.query.count()

    total_complaints = Complaint.query.count()

    pending = Complaint.query.filter_by(status="Pending").count()

    progress = Complaint.query.filter_by(status="In Progress").count()

    resolved = Complaint.query.filter_by(status="Resolved").count()

    recent_complaints = Complaint.query.order_by(
        Complaint.created_at.desc()
    ).limit(5).all()

    # Monthly Analytics
    monthly_data = (
        db.session.query(
            func.strftime("%m", Complaint.created_at),
            func.count(Complaint.id)
        )
        .group_by(func.strftime("%m", Complaint.created_at))
        .all()
    )

    month_names = {
        "01": "Jan",
        "02": "Feb",
        "03": "Mar",
        "04": "Apr",
        "05": "May",
        "06": "Jun",
        "07": "Jul",
        "08": "Aug",
        "09": "Sep",
        "10": "Oct",
        "11": "Nov",
        "12": "Dec",
    }

    months = []
    complaints = []

    for month, total in monthly_data:
        months.append(month_names.get(month))
        complaints.append(total)

    # Weekly Analytics
    today = datetime.utcnow()

    weekly_labels = []
    weekly_values = []

    for i in range(6, -1, -1):
        day = today - timedelta(days=i)

        count = Complaint.query.filter(
            func.date(Complaint.created_at) == day.date()
        ).count()

        weekly_labels.append(day.strftime("%a"))
        weekly_values.append(count)


    return render_template(
        "admin/admin_dashboard.html",
        total_students=total_students,
        total_categories=total_categories,
        total_complaints=total_complaints,
        pending=pending,
        progress=progress,
        resolved=resolved,
        recent_complaints=recent_complaints,
        months=months,
        complaints=complaints,
        weekly_labels=weekly_labels,
        weekly_values=weekly_values
    )

@main.route("/admin/complaints")
@login_required
def admin_complaints():

    if current_user.role != "admin":
        flash("Access Denied!", "danger")
        return redirect(url_for("main.dashboard"))

    search = request.args.get("search", "")
    status = request.args.get("status", "")

    complaints = Complaint.query.join(User).join(Category)

    # Search
    if search:
        complaints = complaints.filter(
            or_(
                User.name.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%"),
                Complaint.title.ilike(f"%{search}%")
            )
        )

    # Filter by status
    if status:
        complaints = complaints.filter(Complaint.status == status)

    complaints = complaints.order_by(
        Complaint.created_at.desc()
    ).all()

    return render_template(
        "admin/complaints.html",
        complaints=complaints,
        search=search,
        status=status
    )

@main.route("/admin/export/pdf")
@login_required
def export_pdf():

    if current_user.role != "admin":
        flash("Access Denied!", "danger")
        return redirect(url_for("main.dashboard"))

    status = request.args.get("status")

    complaints = Complaint.query

    if status:
        complaints = complaints.filter_by(status=status)

    complaints = complaints.order_by(
        Complaint.created_at.desc()
    ).all()

    pdf = generate_pdf(complaints)

    return send_file(
        pdf,
        as_attachment=True,
        download_name="complaints_report.pdf",
        mimetype="application/pdf"
    )

@main.route("/admin/export/excel")
@login_required
def export_excel():

    if current_user.role != "admin":
        flash("Access Denied!", "danger")
        return redirect(url_for("main.dashboard"))

    status = request.args.get("status")

    complaints = Complaint.query

    if status:
        complaints = complaints.filter_by(status=status)

    complaints = complaints.order_by(
        Complaint.created_at.desc()
    ).all()

    excel = generate_excel(complaints)

    return send_file(
        excel,
        as_attachment=True,
        download_name="complaints_report.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

@main.route("/admin/complaints/search")
@login_required
def complaint_live_search():

    if current_user.role != "admin":
        return jsonify([])

    search = request.args.get("q", "")
    status = request.args.get("status", "")

    complaints = Complaint.query.join(User).join(Category)

    if search:
        complaints = complaints.filter(
            or_(
                User.name.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%"),
                Complaint.title.ilike(f"%{search}%"),
                Category.category_name.ilike(f"%{search}%")
            )
        )

    if status:
        complaints = complaints.filter(
            Complaint.status == status
        )

    complaints = complaints.order_by(
        Complaint.created_at.desc()
    ).all()

    data = []

    for complaint in complaints:

        data.append({
            "id": complaint.id,
            "student": complaint.student.name,
            "category": complaint.category.category_name,
            "title": complaint.title,
            "status": complaint.status,
            "date": complaint.created_at.strftime("%d-%m-%Y")
        })

    return jsonify(data)

@main.route("/admin/complaint/<int:complaint_id>")
@login_required
def admin_view_complaint(complaint_id):

    if current_user.role != "admin":
        flash("Access Denied!", "danger")
        return redirect(url_for("main.dashboard"))

    complaint = Complaint.query.get_or_404(complaint_id)

    form = CommentForm()

    return render_template(
        "admin/view_complaint.html",
        complaint=complaint,
        form=form
    )



@main.route("/admin/complaint/status/<int:complaint_id>", methods=["GET", "POST"])
@login_required
def update_status(complaint_id):

    if current_user.role != "admin":
        flash("Access Denied!", "danger")
        return redirect(url_for("main.dashboard"))

    complaint = Complaint.query.get_or_404(complaint_id)

    form = UpdateStatusForm()

    if form.validate_on_submit():

        complaint.status = form.status.data

        history = ComplaintHistory(
            complaint_id=complaint.id,
            status=form.status.data,
            remark=form.remark.data
        )
        
        db.session.add(history)

        notification = Notification(
            user_id=complaint.student_id,
            complaint_id=complaint.id,
            message=f"Your complaint status has been updated to '{form.status.data}'."
        )

        db.session.add(notification)


        db.session.commit()

        flash(
            "Complaint updated successfully!",
            "success"
        )

        return redirect(
            url_for(
                "main.admin_view_complaint",
                complaint_id=complaint.id
            )
        )

    form.status.data = complaint.status

    return render_template(
        "admin/update_status.html",
        complaint=complaint,
        form=form
    )

@main.route("/complaint/comment/<int:complaint_id>", methods=["POST"])
@login_required
def add_comment(complaint_id):

    complaint = Complaint.query.get_or_404(complaint_id)

    form = CommentForm()

    if form.validate_on_submit():

        comment = Comment(
            complaint_id=complaint.id,
            user_id=current_user.id,
            message=form.message.data
        )

        db.session.add(comment)

        # Notify the other person
        if current_user.role == "admin":

            notification = Notification(
                user_id=complaint.student_id,
                complaint_id=complaint.id,
                message="Admin replied to your complaint."
            )

        else:

            admin = User.query.filter_by(role="admin").first()

            notification = Notification(
                user_id=admin.id,
                complaint_id=complaint.id,
                message=f"{current_user.name} replied to Complaint #{complaint.id}."
            )

        db.session.add(notification)

        db.session.commit()

        flash("Comment added successfully!", "success")

    if current_user.role == "admin":
        return redirect(url_for(
            "main.admin_view_complaint",
            complaint_id=complaint.id
        ))

    return redirect(url_for(
        "main.view_complaint",
        complaint_id=complaint.id
    ))


@main.route("/admin/students")
@login_required
def admin_students():

    if current_user.role != "admin":
        flash("Access Denied!", "danger")
        return redirect(url_for("main.dashboard"))

    search = request.args.get("search", "")

    students = User.query.filter(User.role == "student")

    if search:

        students = students.filter(
            or_(
                User.name.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%"),
                User.department.ilike(f"%{search}%")
            )
        )

    students = students.order_by(User.name.asc()).all()

    return render_template(
        "admin/students.html",
        students=students,
        search=search
    )

@main.route("/admin/students/search")
@login_required
def student_live_search():

    if current_user.role != "admin":
        return jsonify([])

    search = request.args.get("q", "")

    students = User.query.filter(User.role == "student")

    if search:
        students = students.filter(
            or_(
                User.name.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%"),
                User.department.ilike(f"%{search}%")
            )
        )

    students = students.order_by(User.name.asc()).all()

    data = []

    for student in students:
        data.append({
            "id": student.id,
            "name": student.name,
            "email": student.email,
            "department": student.department,
            "complaints": len(student.complaints)
        })

    return jsonify(data)

@main.route("/admin/student/<int:student_id>")
@login_required
def student_details(student_id):

    if current_user.role != "admin":
        flash("Access Denied!", "danger")
        return redirect(url_for("main.dashboard"))

    student = User.query.get_or_404(student_id)

    complaints = Complaint.query.filter_by(
        student_id=student.id
    ).order_by(Complaint.created_at.desc()).all()

    return render_template(
        "admin/student_details.html",
        student=student,
        complaints=complaints
    )

@main.route("/admin/student/delete/<int:student_id>")
@login_required
def delete_student(student_id):

    if current_user.role != "admin":
        flash("Access Denied!", "danger")
        return redirect(url_for("main.dashboard"))

    student = User.query.get_or_404(student_id)

    if student.role == "admin":
        flash("Admin account cannot be deleted.", "danger")
        return redirect(url_for("main.admin_students"))

    if student.complaints:
        flash(
            "Cannot delete student because they have submitted complaints.",
            "warning"
        )
        return redirect(url_for("main.admin_students"))

    db.session.delete(student)
    db.session.commit()

    flash("Student deleted successfully.", "success")

    return redirect(url_for("main.admin_students"))


@main.route("/categories/add", methods=["GET", "POST"])
@login_required
def add_category():

    # Only Admin
    if current_user.role != "admin":
        flash("Access Denied!", "danger")
        return redirect(url_for("main.dashboard"))

    form = CategoryForm()

    if form.validate_on_submit():

        category = Category.query.filter_by(
            category_name=form.category_name.data
        ).first()

        if category:

            flash("Category already exists!", "warning")

            return render_template(
                "category/add_category.html",
                form=form
            )

        new_category = Category(
            category_name=form.category_name.data,
            description=form.description.data
        )

        db.session.add(new_category)
        db.session.commit()

        flash("Category added successfully!", "success")

        return redirect(url_for("main.category_list"))

    return render_template(
        "category/add_category.html",
        form=form
    )


@main.route("/categories")
@login_required
def category_list():

    if current_user.role != "admin":
        flash("Access Denied!", "danger")
        return redirect(url_for("main.dashboard"))

    categories = Category.query.order_by(
        Category.category_name.asc()
    ).all()

    return render_template(
        "category/category_list.html",
        categories=categories
    )

@main.route("/categories/edit/<int:category_id>", methods=["GET", "POST"])
@login_required
def edit_category(category_id):

    # Admin only
    if current_user.role != "admin":
        flash("Access Denied!", "danger")
        return redirect(url_for("main.dashboard"))

    category = Category.query.get_or_404(category_id)

    form = CategoryForm()

    if form.validate_on_submit():

        # Check duplicate category name
        existing = Category.query.filter(
            Category.category_name == form.category_name.data,
            Category.id != category.id
        ).first()

        if existing:
            flash("Category already exists!", "warning")
            return render_template(
                "category/edit_category.html",
                form=form,
                category=category
            )

        category.category_name = form.category_name.data
        category.description = form.description.data

        db.session.commit()

        flash("Category updated successfully!", "success")

        return redirect(url_for("main.category_list"))

    # Pre-fill form
    form.category_name.data = category.category_name
    form.description.data = category.description

    return render_template(
        "category/edit_category.html",
        form=form,
        category=category
    )

@main.route("/categories/delete/<int:category_id>")
@login_required
def delete_category(category_id):

    # Admin only
    if current_user.role != "admin":
        flash("Access Denied!", "danger")
        return redirect(url_for("main.dashboard"))

    category = Category.query.get_or_404(category_id)

    # Check if category has complaints
    if category.complaints:
        flash(
            "Cannot delete category because it is assigned to one or more complaints.",
            "danger"
        )
        return redirect(url_for("main.category_list"))

    db.session.delete(category)
    db.session.commit()

    flash("Category deleted successfully!", "success")

    return redirect(url_for("main.category_list"))

@main.route("/notifications")
@login_required
def notifications():

    notifications = Notification.query.filter_by(
        user_id=current_user.id
    ).order_by(
        Notification.created_at.desc()
    ).all()

     # Mark unread notifications as read
    for notification in notifications:
        if not notification.is_read:
            notification.is_read = True

    db.session.commit()

    return render_template(
        "notifications.html",
        notifications=notifications
    )


@main.route("/logout")
@login_required
def logout():

    logout_user()

    flash("Logged out successfully!", "success")

    return redirect(url_for("main.login"))