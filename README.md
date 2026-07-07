<div align="center">
  <img src="https://raw.githubusercontent.com/Sayyednaa/Trakment/main/staticfiles/img/icons/icon.png" width="120" alt="Trakment Logo">
  <h1>Trakment</h1>
  <p><strong>Your Ultimate Gamified Student & Habit Tracker</strong></p>
  
  [![Django](https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=green)](#)
  [![Bootstrap](https://img.shields.io/badge/Bootstrap-563D7C?style=for-the-badge&logo=bootstrap&logoColor=white)](#)
  [![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](#)
  [![License](https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge)](#)
</div>

<br>

**Trakment** is an all-in-one, beautifully designed productivity dashboard built with Django. Drawing inspiration from modern, gamified interfaces (like Duolingo), Trakment brings together study analytics, habit tracking, deep focus sessions, and spiritual routines into a single, cohesive platform.

---

## 🌟 Key Features

### 📚 Study & Syllabus Tracking
- **Interactive Dashboard:** View your weekly study hours, completed tasks, and syllabus coverage at a glance.
- **Visual Analytics:** Dynamic Area Charts and Line Charts built with ApexCharts.
- **Syllabus Progress:** Break down subjects by chapters and track completion percentages.

### 🧠 Deep Focus Sessions
- **Distraction-Free Mode:** A built-in timer with a true full-screen interface.
- **Ambient Soundscapes:** Seamlessly stream background noises like Rain, Thunder, or Jungle directly inside your focus session using the Web Audio API.
- **Auto-Sync:** Sessions are automatically logged to your daily study time when you finish.

### 🔄 Spaced Repetition Revision Tracker
- **Smart Scheduling:** Easily add lectures and assign custom spaced repetition intervals (e.g., 1-3-7-14-30 days).
- **Due Dates Management:** Automatically calculates the exact date your next revision is due.

### 📝 OMR & Self Tests
- **Automated Grading Prep:** Includes an integrated Optical Mark Recognition (OMR) Setup sheet.
- **Self-Test Analytics:** Log test scores, review mistakes, and analyze your academic performance over time.

### 🕌 Salah & Habit Tracker
- **Daily Check-Ins:** Track your five daily prayers (Fard, Sunnah, Nafl) alongside your academic habits.
- **Visual Streaks:** Maintain momentum with gamified streaks and colorful, interactive checkboxes.

---

## 🚀 Tech Stack

- **Backend:** Python, Django 
- **Database:** SQLite (Development)
- **Frontend:** HTML5, Vanilla CSS (Custom Design System), JavaScript, Bootstrap 5
- **Charting:** ApexCharts.js
- **Icons:** FontAwesome 6

---

## ⚙️ Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Sayyednaa/Trakment.git
   cd Trakment
   ```

2. **Create a virtual environment (optional but recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install dependencies:**
   *(Ensure you have Django and other requirements installed)*
   ```bash
   pip install -r requirements.txt
   ```

4. **Apply database migrations:**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Run the development server:**
   ```bash
   python manage.py runserver
   ```
6. **Access the App:** Open your browser and go to `http://127.0.0.1:8000`.

---

## 🎨 UI/UX Philosophy

Trakment embraces a modern, gamified aesthetic:
- **Card-Duo Design:** Elements feature pronounced borders, soft drop shadows, and vibrant accent colors (Primary Teal, Accent Purple, Vibrant Yellow).
- **Glassmorphism & Gradients:** Subtle, clean background styles for an immersive feel.
- **Micro-Interactions:** Buttons that physically depress when clicked, giving a satisfying tactile response.

---

<div align="center">
  <i>Built with ❤️ to keep you focused and tracking forward.</i>
</div>
