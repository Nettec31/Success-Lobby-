# 🚀 Success Lobby
### *Connecting Students. Building Success.*

**Success Lobby** is a collaboration platform designed specifically for CPCC students to find study partners, share resources, and build academic communities. 

---

## 📋 Project Overview
Many students struggle to find consistent study groups or peers within their specific courses. **Success Lobby** bridges this gap by providing a centralized hub where students can:
* **Find Peers:** Connect with others in the same course or major.
* **Collaborate:** Share notes and schedule study sessions.
* **Succeed Together:** Foster an environment of mutual academic support.

## 👥 The Team (Code-Avengers)
* **Lynnette Ray:** Project Lead & Lead Architect
* **Juanita:** Lead UI/UX Developer
* **Daksh:** Technical Contributor
*  **Urangoo:** System Architect

---
*Developed for the CPCC Innovation Challenge.*
---

## 🏗️ Technical Architecture
As Lead Architect, I designed the system flow to ensure a seamless connection between student data and the user interface.

### The Stack:
* **Backend:** Python with **Flask** to manage routing and server-side logic.
* **Data Management:** **JSON**-based storage for user profiles and study group metadata, allowing for lightweight and fast data retrieval.
* **Frontend:** A responsive **HTML/CSS** interface designed for high-stress student environments (fast navigation).

### Logic Flow:
1.  **Authentication:** A centralized login logic that validates user credentials against the `users.json` database.
2.  **Lobby Routing:** Dynamic routing that directs students to specific "Study Rooms" based on their course selection.
3.  **Interactive Assessment:** An integrated **Quiz System** (`quiz.html`) designed to provide immediate feedback and knowledge validation for students within the lobby.
4.  **Data Persistence:** Ensuring student profile updates are captured and reflected across the platform in real-time.
