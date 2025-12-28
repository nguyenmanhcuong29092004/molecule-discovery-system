import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import StartRunPage from './pages/StartRunPage';
import { Toaster } from './components/ui/toaster';
import './globals.css';

// Create QueryClient instance
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

// Placeholder Dashboard component
function DashboardPage() {
  return (
    <div className="container mx-auto py-8 px-4">
      <h1 className="text-3xl font-bold">Dashboard</h1>
      <p className="text-muted-foreground mt-2">
        Your runs will appear here (to be implemented)
      </p>
    </div>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <div className="min-h-screen bg-background">
          {/* Navbar placeholder */}
          <nav className="border-b">
            <div className="container mx-auto px-4 py-4">
              <h1 className="text-xl font-bold">Molecule Discovery System</h1>
            </div>
          </nav>

          {/* Routes */}
          <Routes>
            <Route path="/" element={<Navigate to="/start" replace />} />
            <Route path="/start" element={<StartRunPage />} />
            <Route path="/dashboard" element={<DashboardPage />} />
          </Routes>

          {/* Toast notifications */}
          <Toaster />
        </div>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;