import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Sidebar } from './components/Sidebar';
import { Topbar } from './components/Topbar';
import { Worklist } from './pages/Worklist';
import { PatientDetail } from './pages/PatientDetail';
import { Ingest } from './pages/Ingest';
import { ScanPage } from './pages/ScanPage';
import { CohortPage } from './pages/CohortPage';
import { CascadePage } from './pages/CascadePage';

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

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/scan" replace />} />
        <Route path="/scan" element={<Layout><ScanPage /></Layout>} />
        <Route path="/worklist" element={<Layout><Worklist /></Layout>} />
        <Route path="/patients/:id" element={<Layout><PatientDetail /></Layout>} />
        <Route path="/cohort" element={<Layout><CohortPage /></Layout>} />
        <Route path="/cascade" element={<Layout><CascadePage /></Layout>} />
        <Route path="/ingest" element={<Layout><Ingest /></Layout>} />
        <Route path="*" element={<Navigate to="/scan" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
