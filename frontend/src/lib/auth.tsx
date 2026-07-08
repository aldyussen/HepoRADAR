import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { api, setLogoutHandler } from '../api';

export interface User {
  id?: number;
  username: string;
  role: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (credentials: any) => Promise<void>;
  logout: () => void;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(localStorage.getItem('heparadar_access_token'));
  const [isLoading, setIsLoading] = useState(true);

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('heparadar_access_token');
    // If mock role was stored, clean it up too
    localStorage.removeItem('heparadar_user_role');
    localStorage.removeItem('heparadar_user_name');
  };

  useEffect(() => {
    setLogoutHandler(logout);
  }, []);

  useEffect(() => {
    async function loadUser() {
      if (token) {
        try {
          if (import.meta.env.VITE_USE_MOCKS === 'true') {
            setUser({ 
              username: localStorage.getItem('heparadar_user_name') || 'demo', 
              role: localStorage.getItem('heparadar_user_role') || 'doctor' 
            });
          } else {
            const me = await api.getMe();
            setUser(me);
          }
        } catch (error) {
          console.error("Failed to load user info", error);
          logout();
        }
      }
      setIsLoading(false);
    }
    loadUser();
  }, [token]);

  const login = async (credentials: any) => {
    if (import.meta.env.VITE_USE_MOCKS === 'true') {
      const mockToken = "mock_token";
      setToken(mockToken);
      localStorage.setItem('heparadar_access_token', mockToken);
      
      const mockRole = credentials.username === 'admin' ? 'admin' 
        : (credentials.username === 'viewer' ? 'viewer' 
        : (credentials.username === 'coordinator' ? 'coordinator' : 'doctor'));
      
      localStorage.setItem('heparadar_user_role', mockRole);
      localStorage.setItem('heparadar_user_name', credentials.username);
      setUser({ username: credentials.username, role: mockRole });
      return;
    }
    
    const data = await api.login(credentials);
    setToken(data.access_token);
    localStorage.setItem('heparadar_access_token', data.access_token);
  };

  return (
    <AuthContext.Provider value={{ user, token, login, logout, isLoading }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
