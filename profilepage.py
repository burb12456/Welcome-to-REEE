import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox, simpledialog
from PIL import Image, ImageTk
import requests
from io import BytesIO
import webbrowser
import firebase_admin
from firebase_admin import credentials, firestore, storage, auth
from datetime import datetime
import os
import json

db_client = firestore.client()
# Storage client
bucket = storage.bucket()
class ProfilePage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # Title
        label = tk.Label(self, text="Profile Page", font=("Comic Sans MS", 32))
        label.pack(pady=20)

        # Username display
        label = tk.Label(self, text="Username:", font=("Comic Sans MS", 18))
        label.pack(pady=10)
        self.username_label = tk.Label(self, text=controller.username, font=("Comic Sans MS", 14))
        self.username_label.pack(pady=10)

        # Profile picture display
        self.profile_pic_label = tk.Label(self)
        self.profile_pic_label.pack(pady=10)
        self.load_profile_picture()

        # Upload profile picture button
        upload_pic_button = tk.Button(self, text="Upload Profile Picture", command=self.upload_profile_picture, fg="blue", font=("Comic Sans MS", 16))
        upload_pic_button.pack(pady=10)

        # Name input
        label = tk.Label(self, text="Name:", font=("Comic Sans MS", 18))
        label.pack(pady=10)
        self.name_entry = tk.Entry(self, font=("Comic Sans MS", 14))
        self.name_entry.pack(pady=10)

        # Description input
        label = tk.Label(self, text="Description:", font=("Comic Sans MS", 18))
        label.pack(pady=10)
        self.description_entry = tk.Entry(self, font=("Comic Sans MS", 14))
        self.description_entry.pack(pady=10)

        # Change password input
        label = tk.Label(self, text="New Password:", font=("Comic Sans MS", 18))
        label.pack(pady=10)
        self.password_entry = tk.Entry(self, font=("Comic Sans MS", 14), show="*")
        self.password_entry.pack(pady=10)

        # Update profile button
        update_button = tk.Button(self, text="Update Profile", command=self.update_profile, fg="red", font=("Comic Sans MS", 16))
        update_button.pack(pady=10)

        # Back to Home Page button
        back_button = ttk.Button(self, text="Back to Home Page", command=lambda: controller.show_page("HomePage"))
        back_button.pack(pady=20)

    def load_profile_picture(self):
        # Load the user's profile picture
        try:
            user = auth.get_user_by_email(self.controller.username)
            profile_pic_url = db_client.collection("users").document(user.uid).get().to_dict().get("profile_pic_url")
            if profile_pic_url:
                response = requests.get(profile_pic_url)
                img_data = response.content
                img = Image.open(BytesIO(img_data))
                img.thumbnail((200, 200))
                img = ImageTk.PhotoImage(img)
                self.profile_pic_label.config(image=img)
                self.profile_pic_label.image = img  # Keep a reference to avoid garbage collection
        except Exception as e:
            print(f"Failed to load profile picture: {e}")

    def upload_profile_picture(self):
        # Upload a new profile picture to Firebase Storage
        file_path = filedialog.askopenfilename()
        if file_path:
            # Preview the selected image
            img = Image.open(file_path)
            img.thumbnail((200, 200))
            img = ImageTk.PhotoImage(img)
            self.profile_pic_label.config(image=img)
            self.profile_pic_label.image = img  # Keep a reference to avoid garbage collection

            # Confirm upload
            if messagebox.askyesno("Confirm Upload", "Do you want to upload this profile picture?"):
                file_name = os.path.basename(file_path)
                user = auth.get_user_by_email(self.controller.username)
                blob = bucket.blob(f"profile_pictures/{user.uid}/{file_name}")
                blob.upload_from_filename(file_path)
                blob.make_public()
                profile_pic_url = blob.public_url

                # Update Firestore with the new profile picture URL
                db_client.collection("users").document(user.uid).set({
                    "profile_pic_url": profile_pic_url,
                    "username": self.controller.username,
                    "user_id": user.uid
                }, merge=True)
                self.load_profile_picture()  # Refresh the profile picture

    def update_profile(self):
        # Update the user's profile
        new_name = self.name_entry.get().strip()
        new_description = self.description_entry.get().strip()
        new_password = self.password_entry.get().strip()
        try:
            user = auth.get_user_by_email(self.controller.username)
            if new_name:
                auth.update_user(user.uid, display_name=new_name)
            if new_password:
                auth.update_user(user.uid, password=new_password)
            db_client.collection("users").document(user.uid).set({
                "description": new_description,
                "username": self.controller.username,
                "user_id": user.uid
            }, merge=True)
            messagebox.showinfo("Success", "Profile updated successfully!")
        except auth.AuthError:
            messagebox.showerror("Error", "Failed to update profile. Please try again.")

# Second Page