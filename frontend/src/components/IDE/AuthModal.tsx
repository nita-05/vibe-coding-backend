import { useEffect, useMemo, useState } from 'react';
import { X } from 'lucide-react';
import { getGoogleAuthUrl } from '../../services/api';

type Mode = 'login' | 'register';

export default function AuthModal({
  isOpen,
  onClose,
  onLogin,
  onRegister,
  isLoading,
  error,
}: {
  isOpen: boolean;
  onClose: () => void;
  onLogin: (args: { email: string; password: string }) => void;
  onRegister: (args: { name?: string; email: string; password: string }) => void;
  isLoading: boolean;
  error?: string | null;
}) {
  const [mode, setMode] = useState<Mode>('login');
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const [googleLoading, setGoogleLoading] = useState(false);

  const canSubmit = useMemo(() => {
    if (!email.trim() || !password.trim()) return false;
    if (mode === 'register' && password.trim().length < 8) return false;
    return true;
  }, [email, password, mode]);

  const handleGoogleSignIn = async () => {
    try {
      setGoogleLoading(true);
      const { auth_url } = await getGoogleAuthUrl();
      window.location.href = auth_url;
    } catch (error: any) {
      console.error('Google auth error:', error);
      alert(error.response?.data?.detail || 'Failed to initiate Google sign-in');
      setGoogleLoading(false);
    }
  };

  // Check for auth success/error in URL params
  useEffect(() => {
    if (!isOpen) return;
    const params = new URLSearchParams(window.location.search);
    if (params.get('auth_success') === 'true') {
      onClose();
      window.history.replaceState({}, '', window.location.pathname);
      // Reload to refresh auth state
      window.location.reload();
    } else if (params.get('auth_error')) {
      const error = params.get('auth_error');
      window.history.replaceState({}, '', window.location.pathname);
      alert(`Authentication error: ${error}`);
    }
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
      <div className="w-full max-w-md bg-[#252526] border border-[#3e3e42] rounded-lg shadow-xl">
        <div className="flex items-center justify-between p-4 border-b border-[#3e3e42]">
          <div className="flex items-center gap-2">
            <h2 className="text-base font-semibold text-white">
              {mode === 'login' ? 'Sign in' : 'Create account'}
            </h2>
          </div>
          <button
            onClick={onClose}
            className="p-1 hover:bg-[#3e3e42] rounded transition-colors"
            aria-label="Close"
          >
            <X className="w-4 h-4 text-[#cccccc]" />
          </button>
        </div>

        <div className="p-4">
          <div className="flex gap-2 mb-4">
            <button
              onClick={() => setMode('login')}
              className={`flex-1 px-3 py-2 text-sm rounded border transition-colors ${
                mode === 'login'
                  ? 'bg-[#007acc] border-[#007acc] text-white'
                  : 'bg-transparent border-[#3e3e42] text-[#cccccc] hover:bg-[#2a2d2e]'
              }`}
            >
              Sign in
            </button>
            <button
              onClick={() => setMode('register')}
              className={`flex-1 px-3 py-2 text-sm rounded border transition-colors ${
                mode === 'register'
                  ? 'bg-[#007acc] border-[#007acc] text-white'
                  : 'bg-transparent border-[#3e3e42] text-[#cccccc] hover:bg-[#2a2d2e]'
              }`}
            >
              Register
            </button>
          </div>

          {error && (
            <div className="mb-3 text-xs text-[#f48771] border border-[#5a2b2b] bg-[#2a1f1f] rounded px-3 py-2">
              {error}
            </div>
          )}

          {/* Google Sign In Button */}
          <button
            type="button"
            onClick={handleGoogleSignIn}
            disabled={googleLoading || isLoading}
            className="w-full h-10 rounded border border-[#3e3e42] bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm text-gray-700 font-medium flex items-center justify-center gap-2 mb-3"
          >
            <svg className="w-5 h-5" viewBox="0 0 24 24">
              <path
                fill="#4285F4"
                d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
              />
              <path
                fill="#34A853"
                d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
              />
              <path
                fill="#FBBC05"
                d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
              />
              <path
                fill="#EA4335"
                d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
              />
            </svg>
            {googleLoading ? 'Redirecting...' : 'Sign in with Google'}
          </button>

          <div className="relative my-3">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-[#3e3e42]"></div>
            </div>
            <div className="relative flex justify-center text-xs">
              <span className="px-2 bg-[#252526] text-[#858585]">or</span>
            </div>
          </div>

          <form
            onSubmit={(e) => {
              e.preventDefault();
              if (!canSubmit || isLoading) return;
              if (mode === 'login') onLogin({ email: email.trim(), password });
              else onRegister({ name: name.trim() || undefined, email: email.trim(), password });
            }}
            className="space-y-3"
          >
            {mode === 'register' && (
              <div>
                <label className="block text-xs text-[#cccccc] mb-1">Name (optional)</label>
                <input
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full h-9 px-3 text-sm bg-[#1e1e1e] border border-[#3e3e42] rounded text-[#cccccc] focus:outline-none focus:border-[#007acc]"
                  placeholder="Your name"
                  autoComplete="name"
                />
              </div>
            )}

            <div>
              <label className="block text-xs text-[#cccccc] mb-1">Email</label>
              <input
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full h-9 px-3 text-sm bg-[#1e1e1e] border border-[#3e3e42] rounded text-[#cccccc] focus:outline-none focus:border-[#007acc]"
                placeholder="you@example.com"
                autoComplete="email"
                inputMode="email"
              />
            </div>

            <div>
              <label className="block text-xs text-[#cccccc] mb-1">
                Password {mode === 'register' ? '(min 8 chars)' : ''}
              </label>
              <input
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                type="password"
                className="w-full h-9 px-3 text-sm bg-[#1e1e1e] border border-[#3e3e42] rounded text-[#cccccc] focus:outline-none focus:border-[#007acc]"
                autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
              />
            </div>

            <button
              type="submit"
              disabled={!canSubmit || isLoading}
              className="w-full h-10 rounded bg-[#007acc] hover:bg-[#0066aa] disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm text-white"
            >
              {isLoading ? 'Please wait…' : mode === 'login' ? 'Sign in' : 'Create account'}
            </button>
          </form>

          <p className="mt-3 text-[11px] text-[#858585]">
            This uses secure HttpOnly cookies (no tokens stored in localStorage).
          </p>
        </div>
      </div>
    </div>
  );
}

