# Demo Generator Project

This project is a **Demo Generator** that consists of two parts:
1. **Backend** - A Flask application.
2. **Frontend** - A React application.

Below are the steps to set up and run both the backend and frontend applications on your local machine.

---

## 🖥️ **Backend Setup**
### Prerequisites:
- Python 3.x
- Flask
- OpenAI API Key (stored in a `.env` file)

### Steps to Start the Backend:

1. **Navigate to the backend folder:**
   ```bash
   cd backend
   ```

2. **Create a `.env` file:**
   - In the `backend` directory, create a `.env` file to store your OpenAI API key:
     ```
     OPENAI_API_KEY=your_openai_api_key_here
     ```

3. **Run the Flask application:**
   ```bash
   python app.py
   ```

5. **Access the backend:**
   - Once the server is running, you can access the backend at:
     ```
     http://127.0.0.1:5000
     ```

---

## 🌐 **Frontend Setup**
### Prerequisites:
- Node.js
- npm or yarn

### Steps to Start the Frontend:

1. **Navigate to the frontend folder:**
   ```bash
   cd frontend
   ```

2. **Install the required dependencies:**
   ```bash
   npm install
   ```

3. **Start the React development server:**
   ```bash
   npm start
   ```

4. **Access the frontend:**
   - The frontend will be available at:
     ```
     http://localhost:3000
     ```

---

## 🛠 **Additional Commands**

### Backend:
- To run the backend in debug mode:
  ```bash
  flask run --debug
  ```

### Frontend:
- To build the React app for production:
  ```bash
  npm run build
  ```
  - The production-ready files will be created in the `build` folder.

---


## 📧 **Contact**
If you have any questions or issues, feel free to contact the project owner at:
- **GitHub:** [leanabarbion](https://github.com/leanabarbion)

