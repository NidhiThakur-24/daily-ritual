# Daily Ritual

A full-stack application designed to help users build and maintain daily rituals, track workouts, and achieve their goals with AI-powered planning.

## Features

- **Dashboard**: View and manage your daily activities and progress
- **Workout Tracker**: Log and track your workout sessions
- **AI Plan Generator**: Get personalized daily plans powered by AI
- **Authentication**: Secure user authentication and account management
- **Navbar**: Easy navigation across the application
- **Responsive Design**: Built with Tailwind CSS for a modern UI

## Project Structure

```
my_choas/
├── backend/              # Python Flask backend
│   └── app.py
├── daily_ritual/         # Main React frontend
│   ├── daily-ritual/     # Vite + React app
│   │   ├── components/   # React components
│   │   │   ├── AI/
│   │   │   ├── Auth/
│   │   │   ├── workout/
│   │   │   ├── Dashboard.jsx
│   │   │   └── Navbar.jsx
│   │   ├── services/     # API and database services
│   │   ├── store/        # State management
│   │   └── src/
│   ├── package.json
│   ├── tailwind.config.js
│   └── postcss.config.js
├── unvalidated/          # Alternative frontend version
└── daily_ritual_backup/  # Backup files
```

## Tech Stack

### Frontend
- **React** - UI library
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Utility-first CSS framework
- **PostCSS** - CSS processing

### Backend
- **Python** - Server-side language
- **Flask** - Web framework
- **Appwrite** - Backend-as-a-service (based on services)

### Services
- **AI Integration** - AI-powered plan generation
- **Database** - Data persistence
- **Authentication** - User authentication and management

## Getting Started

### Prerequisites
- Node.js (v14+)
- Python (v3.8+)
- npm or yarn

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/NidhiThakur-24/daily-ritual.git
cd daily-ritual
```

2. **Backend Setup**
```bash
cd backend
python -m venv venv
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

3. **Frontend Setup**
```bash
cd daily_ritual/daily-ritual
npm install
```

## Running the Application

### Start Backend
```bash
cd backend
python app.py
```
The backend will run on `http://localhost:5000` (or configured port)

### Start Frontend
```bash
cd daily_ritual/daily-ritual
npm run dev
```
The frontend will run on `http://localhost:5173` (Vite default)

## Available Scripts

### Frontend
- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint (if configured)

## Configuration

- **Tailwind CSS**: Configured in `daily_ritual/tailwind.config.js`
- **PostCSS**: Configured in `daily_ritual/postcss.config.js`
- **Environment Variables**: Create `.env.local` files in respective directories

## Key Components

### AI/
- `planGenerator.jsx` - Generates AI-powered daily plans

### Auth/
- `Login.jsx` - User login interface
- `Signup.jsx` - User registration interface

### Workout/
- `WorkoutTracker.jsx` - Track and log workouts

### Core Components
- `Dashboard.jsx` - Main dashboard view
- `Navbar.jsx` - Navigation bar

## Services

- `ai.js` - AI integration service
- `appwrite.js` - Appwrite backend service
- `database.js` - Database operations

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open source and available under the MIT License.

## Support

For support, please open an issue on the GitHub repository.

## Author

**Nidhi Thakur**

---

Built with ❤️ for better daily rituals and habits
