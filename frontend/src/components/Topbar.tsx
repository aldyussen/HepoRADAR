import { User, LogOut } from "lucide-react";
import { useAuth } from "../lib/auth";
import { useNavigate } from "react-router-dom";
import { useState } from "react";

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
  const [isChangingRole, setIsChangingRole] = useState(false);

  const handleRoleChange = async (e: React.ChangeEvent<HTMLSelectElement>) => {
    setIsChangingRole(true);
    const newRole = e.target.value;
    try {
      // @ts-ignore
      await useAuth().login({ username: newRole, password: "123" });
    } catch (e) {
      console.error(e);
    }
    setIsChangingRole(false);
    // Reload page to apply new role safely
    window.location.reload();
  };

  return (
    <header className="h-16 bg-white border-b px-6 flex items-center justify-between shadow-sm">
      <div className="flex items-center gap-2">
        <h2 className="text-sm font-semibold text-slate-600 hidden sm:block">
          Рабочая область &middot; 
        </h2>
        <select 
          value={currentRole} 
          onChange={handleRoleChange}
          disabled={isChangingRole}
          className="text-sm font-bold text-slate-800 bg-transparent border-none p-0 cursor-pointer focus:ring-0 outline-none"
        >
          {Object.entries(roleLabels).map(([key, label]) => (
            <option key={key} value={key}>{label}</option>
          ))}
        </select>
      </div>
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
