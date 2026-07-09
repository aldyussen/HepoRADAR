import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Sidebar } from './components/Sidebar';
import { Topbar } from './components/Topbar';
import { Worklist } from './pages/Worklist';
import { PatientDetail } from './pages/PatientDetail';
import { Ingest } from './pages/Ingest';
import { ScanPage } from './pages/ScanPage';
import { CohortPage } from './pages/CohortPage';
import { CascadePage } from './pages/CascadePage';
import { Login } from './pages/Login';
import { AuthProvider, useAuth } from './lib/auth';
import { QuickCheck } from './pages/QuickCheck';

function Layout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen bg-slate-50">
      <Sidebar />
      <div className="flex-1 flex flex-col h-screen overflow-hidden">
        <Topbar />
        <main className="flex-1 p-6 overflow-auto">
          {children}
        </main>
      </div>
    </div>
  );
}

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, token, isLoading } = useAuth();
  
  if (isLoading) {
    return <div className="min-h-screen flex items-center justify-center">Загрузка...</div>;
  }
  
  if (!token && !user) {
    return <Navigate to="/login" replace />;
  }
  
  return <>{children}</>;
}

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/check" element={<QuickCheck />} />
          <Route path="/" element={<Navigate to="/scan" replace />} />
          <Route path="/scan" element={<ProtectedRoute><Layout><ScanPage /></Layout></ProtectedRoute>} />
          <Route path="/worklist" element={<ProtectedRoute><Layout><Worklist /></Layout></ProtectedRoute>} />
          <Route path="/patients/:id" element={<ProtectedRoute><Layout><PatientDetail /></Layout></ProtectedRoute>} />
          <Route path="/cohort" element={<ProtectedRoute><Layout><CohortPage /></Layout></ProtectedRoute>} />
          <Route path="/cascade" element={<ProtectedRoute><Layout><CascadePage /></Layout></ProtectedRoute>} />
          <Route path="/ingest" element={<ProtectedRoute><Layout><Ingest /></Layout></ProtectedRoute>} />
          <Route path="*" element={<Navigate to="/scan" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
