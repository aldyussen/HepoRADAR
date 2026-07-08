import { User, LogOut } from "lucide-react";
import { useAuth } from "../lib/auth";
import { useNavigate } from "react-router-dom";

export function Topbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const roleLabels: Record<string, string> = {
    doctor: "Врач (Doctor)",
    coordinator: "Координатор (Coordinator)",
    admin: "Администратор (Admin)",
    viewer: "Наблюдатель (Viewer)",
  };

  const currentRole = user?.role || 'viewer';

  return (
    <header className="h-16 bg-white border-b px-6 flex items-center justify-between shadow-sm">
      <h2 className="text-sm font-semibold text-slate-600">
        Рабочая область &middot; <span className="text-slate-800 font-bold">{roleLabels[currentRole] || currentRole}</span>
      </h2>
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 text-sm text-slate-600">
          <User className="w-4 h-4 text-slate-400" />
          <span className="font-medium">{user?.username || 'Гость'}</span>
        </div>
        <button 
          onClick={handleLogout}
          className="flex items-center gap-1.5 text-sm text-slate-500 hover:text-red-600 transition-colors"
          title="Выйти"
        >
          <LogOut className="w-4 h-4" />
          <span className="hidden sm:inline">Выйти</span>
        </button>
      </div>
    </header>
  );
}
