from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (StringField, PasswordField, SubmitField, SelectField, TextAreaField)
from wtforms.validators import DataRequired, Email, Length, EqualTo

class RegisterForm(FlaskForm):
    name = StringField(
        "Full Name",
        validators=[DataRequired(), Length(min=3, max=100)]
    )

    email = StringField(
        "Email",
        validators=[DataRequired(), Email()]
    )

    department = StringField(
        "Department",
        validators=[DataRequired()]
    )

    contact_number = StringField(
        "Contact Number",
        validators=[DataRequired(), Length(min=10, max=15)]
    )

    password = PasswordField(
        "Password",
        validators=[
            DataRequired(),
            Length(min=6)
        ]
    )

    confirm_password = PasswordField(
        "Confirm Password",
        validators=[
            DataRequired(),
            EqualTo("password", message="Passwords must match.")
        ]
    )

    submit = SubmitField("Register")
    

class LoginForm(FlaskForm):
    email = StringField(
        "Email",
        validators=[DataRequired(), Email()]
    )

    password = PasswordField(
        "Password",
        validators=[DataRequired()]
    )

    submit = SubmitField("Login")


class ComplaintForm(FlaskForm):

    category = SelectField(
        "Complaint Category",
        coerce=int,
        validators=[DataRequired()]
    )

    title = StringField(
        "Complaint Title",
        validators=[
            DataRequired(),
            Length(min=5, max=200)
        ]
    )

    description = TextAreaField(
        "Complaint Description",
        validators=[
            DataRequired(),
            Length(min=10)
        ]
    )

    attachment = FileField(
        "Attachment",
        validators=[
            FileAllowed(
                ["jpg", "jpeg", "png", "pdf", "doc", "docx"],
                "Only Images, PDF and Word files are allowed."
            )
        ]
    )

    submit = SubmitField("Submit Complaint")


class CategoryForm(FlaskForm):

    category_name = StringField(
        "Category Name",
        validators=[
            DataRequired(),
            Length(min=3, max=100)
        ]
    )

    description = TextAreaField(
        "Description",
        validators=[
            DataRequired(),
            Length(min=5)
        ]
    )

    submit = SubmitField("Save Category")

class UpdateStatusForm(FlaskForm):

    status = SelectField(
        "Complaint Status",
        choices=[
            ("Pending", "Pending"),
            ("In Progress", "In Progress"),
            ("Resolved", "Resolved")
        ],
        validators=[DataRequired()]
    )

    remark = TextAreaField(
        "Admin Remark",
        validators=[
            DataRequired(),
            Length(
                min=5,
                max=500
            )
        ]
    )

    submit = SubmitField(
        "Update Complaint"
    )

class CommentForm(FlaskForm):

    message = TextAreaField(
        "Comment",
        validators=[
            DataRequired(),
            Length(min=2, max=1000)
        ]
    )

    submit = SubmitField("Send")