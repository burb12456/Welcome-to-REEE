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
cred = credentials.Certificate("boon-test-5bf7e-firebase-adminsdk-9ifsc-717d93af43.json")


# Firestore client
db_client = firestore.client()
# Storage client
bucket = storage.bucket()
class SecondPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # Title
        label = tk.Label(self, text="Second Page", font=("Comic Sans MS", 32))
        label.pack(pady=20)

        # Username input
        label = tk.Label(self, text="Username:", font=("Comic Sans MS", 18))
        label.pack(pady=10)
        self.username_entry = tk.Entry(self, font=("Comic Sans MS", 14))
        self.username_entry.pack(pady=10)

        # Group input
        label = tk.Label(self, text="Group Name:", font=("Comic Sans MS", 18))
        label.pack(pady=10)
        self.group_entry = tk.Entry(self, font=("Comic Sans MS", 14))
        self.group_entry.pack(pady=10)

        # Privacy setting
        self.privacy_var = tk.StringVar(value="public")
        public_radio = tk.Radiobutton(self, text="Public", variable=self.privacy_var, value="public", font=("Comic Sans MS", 14))
        public_radio.pack(pady=5)
        private_radio = tk.Radiobutton(self, text="Private", variable=self.privacy_var, value="private", font=("Comic Sans MS", 14))
        private_radio.pack(pady=5)

        # Group code input for private groups
        label = tk.Label(self, text="Group Code (for private groups):", font=("Comic Sans MS", 18))
        label.pack(pady=10)
        self.group_code_entry = tk.Entry(self, font=("Comic Sans MS", 14))
        self.group_code_entry.pack(pady=10)

        # Set Username and Group button
        set_button = tk.Button(self, text="Set Username and Group", command=self.set_username_and_group, fg="red", font=("Comic Sans MS", 16))
        set_button.pack(pady=10)

        # Create Group button
        create_group_button = tk.Button(self, text="Create Group", command=self.create_group, fg="red", font=("Comic Sans MS", 16))
        create_group_button.pack(pady=10)

        # List of groups
        label = tk.Label(self, text="Available Groups:", font=("Comic Sans MS", 18))
        label.pack(pady=10)
        self.groups_listbox = tk.Listbox(self, font=("Comic Sans MS", 14))
        self.groups_listbox.pack(pady=10, fill=tk.BOTH, expand=True)

        self.load_groups()

        # Back to Home Page button
        back_button = ttk.Button(self, text="Go to Home Page", command=lambda: controller.show_page("HomePage"))
        back_button.pack(pady=20)

    def set_username_and_group(self):
        # Set username and group
        new_username = self.username_entry.get().strip()
        new_group = self.group_entry.get().strip()
        group_code = self.group_code_entry.get().strip()
        if new_username and new_group:  # Ensure both fields are not empty
            group_doc = db_client.collection("groups").document(new_group).get()
            if group_doc.exists:
                group_data = group_doc.to_dict()
                if group_data["privacy"] == "private" and group_data.get("code") != group_code:
                    tk.messagebox.showerror("Access Denied", "Incorrect group code for private group.")
                else:
                    self.controller.username = new_username
                    self.controller.group = new_group
                    self.controller.show_page("HomePage")
            else:
                tk.messagebox.showerror("Group Not Found", "The specified group does not exist.")

    def create_group(self):
        # Create a new group with privacy setting
        group_name = self.group_entry.get().strip()
        privacy = self.privacy_var.get()
        group_code = self.group_code_entry.get().strip() if privacy == "private" else None
        if group_name:  # Ensure the group name is not empty
            db_client.collection("groups").document(group_name).set({"privacy": privacy, "code": group_code})
            tk.messagebox.showinfo("Group Created", f"Group '{group_name}' created successfully!")
            self.load_groups()  # Refresh the list of groups

    def load_groups(self):
        # Load the list of available groups
        self.groups_listbox.delete(0, tk.END)
        groups = db_client.collection("groups").get()
        for group in groups:
            group_data = group.to_dict()
            group_name = group.id
            privacy = group_data.get("privacy", "public")
            self.groups_listbox.insert(tk.END, f"{group_name} ({privacy})")
