from PyQt6 import QtWidgets
import random
import smtplib
import ssl
from string import ascii_lowercase
import re

from source.utils import get_users, get_pyhomecage_email, get_path


class AddUserDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(AddUserDialog, self).__init__(parent)

        self.setGeometry(10, 30, 300, 200)  # Left, top, width, height.
        self.label = QtWidgets.QLabel(
            """You must create an account linked to an email that you frequently check.
                                The homecage system will send you daily updated about your subjects which 
                                MUST be checked to ensure there are no welfare concerns. Therefore we will
                                do an email confirmation thing to register
                            """
        )
        self.textName = QtWidgets.QLineEdit("User Name")
        self.textEmail = QtWidgets.QLineEdit("User email")
        self.addUserButton = QtWidgets.QPushButton("Send code", self)
        self.addUserButton.clicked.connect(self.email_confirmation_code)

        self.confirm_email = QtWidgets.QLineEdit("Enter code")
        self.confirmCodeButton = QtWidgets.QPushButton("Confirm", self)
        self.confirmCodeButton.clicked.connect(self.handleLogin)
        self.users = get_users()

        layout = QtWidgets.QVBoxLayout(self)

        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addWidget(self.textName)
        hlayout.addWidget(self.textEmail)
        hlayout.addWidget(self.addUserButton)

        hlayout2 = QtWidgets.QHBoxLayout(self)
        hlayout2.addWidget(self.confirm_email)
        hlayout2.addWidget(self.confirmCodeButton)
        layout.addWidget(self.label)
        layout.addLayout(hlayout)
        layout.addLayout(hlayout2)

    def email_confirmation_code(self):
        """Send verification code to users email address"""
        # Get and validate email address
        self.receiver_email = str(self.textEmail.text())
        email_pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        if not re.match(email_pattern, self.receiver_email):
            QtWidgets.QMessageBox.warning(self, "Invalid Email", "Please enter a valid email address.")
            return
        # Get Username
        self.user = str(self.textName.text())
        sender_email, password = get_pyhomecage_email()
        # Disable user from editing
        self.textName.setEnabled(False)
        self.textEmail.setEnabled(False)
        # Create Confirmation message
        self.code = "".join(random.choice(ascii_lowercase) for _ in range(20))  # Generate confirmation code
        # Send confirmation email
        try:
            self.send_email(
                message="""\
        Subject: Pyhomecage email confirmation code"""
                + str(self.code),
                sender_email=sender_email,
                password=password,
                receiver_email=self.receiver_email,
            )
            # Confirm email has been sent
            QtWidgets.QMessageBox.information(
                self,
                "Email Sent",
                f"A confirmation code has been sent to {self.receiver_email}. Please check your email.",
            )
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Email Error", f"Failed to send confirmation email: {e}")
            self.textName.setEnabled(True)
            self.textEmail.setEnabled(True)

    def send_email(self, message: str, sender_email: str, password: str, receiver_email: str) -> None:
        # Email setup
        port = 587  # For starttls
        smtp_server = "smtp.gmail.com"
        context = ssl.create_default_context()

        # Open context and send email
        with smtplib.SMTP(smtp_server, port) as server:
            server.ehlo()  # Can be omitted
            server.starttls(context=context)
            server.ehlo()  # Can be omitted
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message)

    def handleLogin(self):
        self.users = get_users()
        if str(self.confirm_email.text()) == str(self.code):
            if self.user.lower() not in [i.lower() for i in self.users]:
                with open(get_path("users.txt"), "a") as file:
                    user_details = "user_data:{'" + str(self.user) + "':' " + str(self.receiver_email) + "'}"
                    file.writelines("\n" + user_details)
        self.accept()
