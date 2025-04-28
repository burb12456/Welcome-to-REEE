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
firebase_admin.initialize_app(cred, {
    'storageBucket': 'boon-test-5bf7e.appspot.com' 
})

# Firestore client
db_client = firestore.client()
# Storage client
bucket = storage.bucket()

class HomePage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # Title
        self.title_label = tk.Label(self, text="", font=("Comic Sans MS", 32, "bold"))
        self.title_label.grid(row=0, column=0, columnspan=5, padx=10, pady=20, sticky="n")

        # Message display
        self.message_display = scrolledtext.ScrolledText(self, wrap=tk.WORD, font=("Comic Sans MS", 12), height=20, state="disabled")
        self.message_display.grid(row=1, column=0, columnspan=5, padx=10, pady=10, sticky="nsew")

        # Message entry
        self.entry = ttk.Entry(self, font=("Comic Sans MS", 14))
        self.entry.grid(row=2, column=0, columnspan=3, padx=10, pady=10, sticky="ew")
        self.entry.bind("<Return>", self.send_message)  # Bind Enter key to send_message

        # Send button
        send_button = ttk.Button(self, text="Send", command=self.send_message, style="Custom.TButton")
        send_button.grid(row=2, column=3, padx=10, pady=10, sticky="ew")

        # Upload image button
        upload_button = ttk.Button(self, text="Upload Image", command=self.upload_image, style="Custom.TButton")
        upload_button.grid(row=2, column=4, padx=10, pady=10, sticky="ew")

        # Back, Profile, and Logout buttons
        back_button = ttk.Button(self, text="Back", command=lambda: controller.show_page("SecondPage"), style="Custom.TButton")
        back_button.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        profile_button = ttk.Button(self, text="Profile", command=lambda: controller.show_page("ProfilePage"), style="Custom.TButton")
        profile_button.grid(row=0, column=4, padx=10, pady=10, sticky="e")

        logout_button = ttk.Button(self, text="Logout", command=controller.logout, style="Custom.TButton")
        logout_button.grid(row=0, column=12, padx=10, pady=10, sticky="e")

        # Making the grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=1)
        self.grid_columnconfigure(3, weight=1)
        self.grid_columnconfigure(4, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Apply custom styles
        self.apply_styles()

        # Load messages
        self.reload_messages()

    def apply_styles(self):
        # Create a custom style for ttk.Button
        style = ttk.Style()
        style.configure("Custom.TButton",
                        font=("Comic Sans MS", 14, "bold"),
                        padding=10,
                        relief="raised",
                        background="#4CAF50",  # Green background
                        foreground="white")   # White text
        style.map("Custom.TButton",
                  background=[("active", "#45a049")],  # Darker green on hover
                  foreground=[("active", "white")])

    def send_message(self, event=None):
        # Submitting new data to database
        message = self.entry.get()
        if message.strip():  # Ensure the message is not empty
            current_date = datetime.now()
            username = self.controller.username  # Get the username
            group = self.controller.group  # Get the group
            db_client.collection(group).add({"user": username, "message": message, 'Date': current_date})  # Push to Firestore
            self.entry.delete(0, tk.END)  # Clear message entry
            self.reload_messages()  # Refresh messages

    def upload_image(self):
        # Uploading image to Firebase Storage
        file_path = filedialog.askopenfilename()
        if file_path:
            file_name = os.path.basename(file_path)
            blob = bucket.blob(f"{self.controller.group}/{file_name}")
            blob.upload_from_filename(file_path)
            blob.make_public()
            image_url = blob.public_url

            # Add image URL to Firestore
            current_date = datetime.now()
            username = self.controller.username  # Get the username
            group = self.controller.group  # Get the group
            db_client.collection(group).add({"user": username, "message": f"Image: {image_url}", 'Date': current_date})  # Push to Firestore
            self.reload_messages()  # Refresh messages

    def reload_messages(self):
        # Tkinter allowing messages to show
        self.message_display.config(state="normal")
        self.message_display.delete(1.0, tk.END)
        
        # Store references to images to prevent garbage collection
        self.images = []

        # Default profile picture
        default_profile_pic = Image.open("default_profile_pic.jpg")
        default_profile_pic.thumbnail((50, 50))
        default_profile_pic = ImageTk.PhotoImage(default_profile_pic)

        # Gets the messages from firebase database
        group = self.controller.group  # Get the group
        docs = db_client.collection(group).order_by("Date").get()
        for doc in docs:
            data = doc.to_dict()
            date_str = data['Date'].strftime('%Y-%m-%d %H:%M:%S') if isinstance(data['Date'], datetime) else data['Date']
            user = data['user']
            user_doc = db_client.collection("users").where("username", "==", user).get()
            profile_pic = default_profile_pic
            if user_doc:
                profile_pic_url = user_doc[0].to_dict().get("profile_pic_url")
                if profile_pic_url:
                    response = requests.get(profile_pic_url)
                    img_data = response.content
                    img = Image.open(BytesIO(img_data))
                    img.thumbnail((50, 50))
                    profile_pic = ImageTk.PhotoImage(img)
                    self.images.append(profile_pic)  # Store reference to prevent garbage collection
            self.message_display.image_create(tk.END, image=profile_pic)
            if "Image:" in data['message']:
                self.message_display.insert(tk.END, f"{data['user']}: ({date_str})\n")
                image_url = data['message'].split('Image: ')[1]
                response = requests.get(image_url)
                img_data = response.content
                img = Image.open(BytesIO(img_data))
                img.thumbnail((200, 200))
                img = ImageTk.PhotoImage(img)
                self.images.append(img)  # Store reference to prevent garbage collection
                self.message_display.image_create(tk.END, image=img)
                self.message_display.tag_add(image_url, "end-2c", "end-1c")
                self.message_display.tag_bind(image_url, "<Button-1>", lambda e, url=image_url: webbrowser.open_new(url))
                self.message_display.insert(tk.END, "\n")
            else:
                self.message_display.insert(tk.END, f"{data['user']}: {data['message']} ({date_str})\n")
                if data['user'] == self.controller.username:
                    edit_button = ttk.Button(self.message_display, text="Edit", command=lambda doc_id=doc.id: self.edit_message(doc_id), style="Custom.TButton")
                    self.message_display.window_create(tk.END, window=edit_button)
                    delete_button = ttk.Button(self.message_display, text="Delete", command=lambda doc_id=doc.id: self.delete_message(doc_id), style="Custom.TButton")
                    self.message_display.window_create(tk.END, window=delete_button)
                self.message_display.insert(tk.END, "\n")
        self.message_display.config(state="disabled")

    def edit_message(self, doc_id):
        # Edit a message in the database
        new_message = simpledialog.askstring("Edit Message", "Enter new message:")
        if new_message:
            group = self.controller.group  # Get the group
            db_client.collection(group).document(doc_id).update({"message": new_message})
            self.reload_messages()  # Refresh messages

    def delete_message(self, doc_id):
        # Delete a message from the database
        group = self.controller.group  # Get the group
        db_client.collection(group).document(doc_id).delete()
        self.reload_messages()  # Refresh messages

    def login_page(self):
        self.show_page("LoginPage") 

    def tkraise(self, aboveThis=None):
        # Update title and username label when the page is shown
        self.title_label.config(text=self.controller.group)

        self.reload_messages()
        super().tkraise(aboveThis)