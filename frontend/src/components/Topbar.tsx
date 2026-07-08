import { useState, useEffect } from "react";
import { User } from "lucide-react";

export function Topbar() {
  const [role, setRole] = useState(() => localStorage.getItem("heparadar_user_role") || "doctor");

  useEffect(() => {
    const handleRoleChange = () => {
      setRole(localStorage.getItem("heparadar_user_role") || "doctor");
    };
    window.addEventListener("roleChanged", handleRoleChange);
    return () => window.removeEventListener("roleChanged", handleRoleChange);
  }, []);

  const handleRoleChange = (newRole: string) => {
    localStorage.setItem("heparadar_user_role", newRole);
    setRole(newRole);
    window.dispatchEvent(new Event("roleChanged"));
  };

  const roleLabels: Record<string, string> = {
    doctor: "Врач (Doctor)",
    coordinator: "Координатор (Coordinator)",
    admin: "Администратор (Admin)",
    viewer: "Наблюдатель (Viewer)",
  };

  return (
    <header className="h-16 bg-white border-b px-6 flex items-center justify-between shadow-sm">
      <h2 className="text-sm font-semibold text-slate-600">
        Рабочая область &middot; <span className="text-slate-800 font-bold">{roleLabels[role] || role}</span>
      </h2>
      <div className="flex items-center gap-2">
        <User className="w-4 h-4 text-slate-400" />
        <select
          aria-label="Выбор роли пользователя (демо-режим)"
          value={role}
          onChange={(e) => handleRoleChange(e.target.value)}
          className="border border-slate-200 rounded-lg p-1.5 px-2.5 text-xs font-semibold bg-slate-50 focus:outline-none focus:ring-1 focus:ring-blue-500"
        >
          <option value="doctor">Врач (Doctor)</option>
          <option value="coordinator">Координатор (Coordinator)</option>
          <option value="admin">Администратор (Admin)</option>
          <option value="viewer">Наблюдатель (Viewer)</option>
        </select>
      </div>
    </header>
  );
}
