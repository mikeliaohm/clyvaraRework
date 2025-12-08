# 📁 Project Structure Documentation  
**Last Updated:** 12/5/25  

This project consists of a **React + Vite frontend** and a **FastAPI + Python backend**, organized into two main directories. Below is a clean overview of the full structure, runtime behavior, and features.

---

## 🚀 Runtime Information
- **Frontend (React/Vite)** runs on **port `8001`**  
- **Backend (FastAPI)** runs on **port `8000`**
- **Global styling** is defined in:
  - `app.css` or  
  - `index.css`
- **Styled Components**  
  We use the React library **Styled Components** to integrate CSS directly within JavaScript, enabling dynamic styling tied to component logic.

---

## 🧠 Core Features

### **Dashboard**
- Users can **upload study materials directly from their device**.
- Uploaded files are processed and stored so students can review and study them inside **Clyvara**.

### **Learning Plans**
- Each learning plan page includes **AI quiz generation** at the bottom.  
- After reviewing the lesson/module content, users can generate **quiz questions** tailored to what they just studied.
- Powered by **OpenAI** and integrated tightly with the learning plan content.

### **Anesthesia Careplan**
- Users can input medical diagnosis information into careplan (be sure to populate all required fields at minimum)
- Once form is filled out, generate AI careplan recommendations to assist treatment/diagnosis
---

## 🖥️ Backend (`backend/`)

Handles all server-side logic, API routing, authentication, schemas, and AI integration.

### **Technologies & Integrations**
- **Supabase** — manages all **user authentication** (login/signup)  
- **AWS** — stores all **backend schemas** and data structures  
- **OpenAI** — powers:
  - The **Brainie assistant**  
  - AI features used in the **Anesthesia Care Plan**  
  - AI quiz question generation for learning plans  

### **Key Files & Directories**
- **`roadmaps/`**  
  High-level documentation of backend workflow and structure.

- **`.env`**  
  Stores all secret environment variables.  
  ⚠️ *Never commit this file.*

- **`systemprompt.txt`**  
  Defines the system prompt used by OpenAI to guide AI behavior.

---

## 🎨 Frontend (`frontend/`)

Built with **React + Vite**, containing all UI logic, routing, and component structures.

### **Directory Overview**
- **`src/`**  
  Contains all React logic, UI components, routes, and hooks.

- **`app.jsx`**  
  The main entry point for **frontend routing**.

- **`assets/`**  
  Houses:
  - Learning plan content  
  - All images, icons, and logos used across the UI  

- **`components/`**  
  Collection of reusable UI building blocks used throughout the application.

- **`layouts/`**  
  Standard layout components ensuring consistent design patterns across pages.

---
# Branding & Design Documentation

## Overview
This document summarizes the early-stage visual identity and product design work for Clyvara. The focus includes color exploration, mascot design, and wireframe iterations for the initial product concept.

## Deliverables
### 1. Color Palette
A foundational color system exploring brand personality and tone.  
- Primary colors  
- Secondary/supporting colors  
- Example use cases (buttons, backgrounds, accents)

### 2. Mascot Design
Early mascot concepts to represent the brand voice and visual identity.  
- Initial sketches  
- Style direction  
- Final mascot and logo

### 3. Wireframe Iterations
Low- to mid-fidelity wireframes created to establish layout, structure, and early user flow.  
- Initial layout (Dashboard, log in/sign up page, landing page) 
- Refinement based on feedback  
- Updated structure + improved usability

## Figma Source File
All designs are documented in the Figma file below:  
👉 https://www.figma.com/design/IQhMApIk2VSPbIWeg7JERp/Design?node-id=0-1&t=qjeOu8ACJfbgBrFr-1

This file includes:
- Color palette frames  
- Mascot concepts  
- Wireframe versions 

## Notes
These assets reflect exploration and early product direction. They can be expanded into full brand guidelines and high-fidelity UI in future phases.

---
## 📦 Miscellaneous

- **`node_modules/`**  
  Contains all dependency packages required for the frontend to run.  
  Automatically generated — do *not* modify manually.

- **`package-lock.json`**  
  Ensures consistent dependency versions for all developers.  
  Must be committed to version control.

---
