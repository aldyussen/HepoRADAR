import { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Users, Upload, Activity, Search, BarChart3, GitFork } from 'lucide-react';

export function Sidebar() {
  const location = useLocation();
  const [role, setRole] = useState(() => localStorage.getItem("heparadar_user_role") || "doctor");

  useEffect(() => {
    const handleRoleChange = () => {
      setRole(localStorage.getItem("heparadar_user_role") || "doctor");
    };
    window.addEventListener("roleChanged", handleRoleChange);
    return () => window.removeEventListener("roleChanged", handleRoleChange);
  }, []);

  const allLinks = [
    { name: 'Сканирование когорты', path: '/scan', icon: Search, roles: ['doctor', 'admin'] },
    { name: 'Список пациентов', path: '/worklist', icon: Users, roles: ['doctor', 'coordinator', 'viewer'] },
    { name: 'Обзор когорты', path: '/cohort', icon: BarChart3, roles: ['doctor', 'admin', 'viewer'] },
    { name: 'Каскад ХВГ', path: '/cascade', icon: GitFork, roles: ['coordinator'] },
    { name: 'Загрузка CSV', path: '/ingest', icon: Upload, roles: ['admin'] },
  ];

  const links = allLinks.filter(link => link.roles.includes(role));

  return (
    <div className="w-64 bg-slate-900 text-white min-h-screen p-4 flex flex-col">
      <div className="flex items-center gap-2 mb-8 mt-2 px-2">
        <Activity className="w-8 h-8 text-blue-400" />
        <h1 className="text-xl font-bold tracking-wider">HepaRadar</h1>
      </div>
      <nav className="flex-1 space-y-2">
        {links.map((link) => {
          const Icon = link.icon;
          const isActive = location.pathname === link.path;
          return (
            <Link
              key={link.path}
              to={link.path}
              className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                isActive ? 'bg-blue-600 text-white' : 'text-slate-400 hover:bg-slate-800 hover:text-white'
              }`}
            >
              <Icon className="w-5 h-5" />
              {link.name}
            </Link>
          );
        })}
      </nav>
    </div>
  );
}
