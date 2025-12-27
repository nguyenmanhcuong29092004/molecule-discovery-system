import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-50">
        <nav className="bg-white border-b p-4">
          <h1 className="text-2xl font-bold">Molecule Discovery System</h1>
        </nav>
        <main className="container mx-auto p-6">
          <Routes>
            <Route path="/" element={<div>Dashboard Coming Soon</div>} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}

export default App