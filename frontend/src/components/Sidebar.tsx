import { Link, useLocation } from 'react-router-dom';
import { Users, Upload, Activity, Search, BarChart3 } from 'lucide-react';

export function Sidebar() {
  const location = useLocation();

  const links = [
    { name: 'Сканирование когорты', path: '/scan', icon: Search },
    { name: 'Список пациентов', path: '/worklist', icon: Users },
    { name: 'Обзор когорты', path: '/cohort', icon: BarChart3 },
    { name: 'Загрузка CSV', path: '/ingest', icon: Upload },
  ];

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
