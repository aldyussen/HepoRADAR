import React, { useState } from 'react';
import { useAuth } from '../lib/auth';
import { useNavigate } from 'react-router-dom';

export function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const isMock = import.meta.env.VITE_USE_MOCKS === 'true';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login({ username, password });
      navigate('/scan');
    } catch (err: any) {
      setError(err.message || 'Ошибка входа. Проверьте данные.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
      <div className="bg-white p-8 rounded-xl shadow-sm border border-slate-200 max-w-sm w-full">
        <h1 className="text-2xl font-semibold mb-6 text-center text-slate-800">Вход в HepaRadar</h1>
        
        {isMock && (
          <div className="mb-6 p-4 bg-blue-50 text-blue-800 text-sm rounded-lg border border-blue-100">
            <p className="font-semibold mb-2">Демонстрационный режим</p>
            <p className="mb-2">Логин определяет роль, пароль любой:</p>
            <ul className="list-disc pl-5 space-y-1">
              <li><b>admin</b> - полный доступ</li>
              <li><b>doctor</b> - врач</li>
              <li><b>coordinator</b> - координатор</li>
              <li><b>viewer</b> - только чтение</li>
            </ul>
          </div>
        )}
        
        {error && (
          <div className="mb-4 p-3 bg-red-50 text-red-700 text-sm rounded-lg border border-red-100">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Логин</label>
            <input 
              type="text" 
              value={username}
              onChange={e => setUsername(e.target.value)}
              className="w-full border-slate-300 rounded-lg shadow-sm focus:ring-blue-500 focus:border-blue-500 p-2.5 border"
              required 
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Пароль</label>
            <input 
              type="password" 
              value={password}
              onChange={e => setPassword(e.target.value)}
              className="w-full border-slate-300 rounded-lg shadow-sm focus:ring-blue-500 focus:border-blue-500 p-2.5 border"
              required 
            />
          </div>
          
          <button 
            type="submit" 
            disabled={loading}
            className="w-full bg-blue-600 text-white py-2.5 px-4 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-70 disabled:cursor-not-allowed font-medium mt-2"
          >
            {loading ? 'Вход...' : 'Войти'}
          </button>
        </form>
      </div>
    </div>
  );
}
