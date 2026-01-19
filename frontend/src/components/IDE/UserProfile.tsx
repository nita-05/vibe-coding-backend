import { useEffect, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { User, LogOut, Settings, ChevronDown, UserCircle } from 'lucide-react';
import AuthModal from './AuthModal';
import ProfileModal from './ProfileModal';
import { getMe, login, logout, register } from '../../services/api';

interface UserProfileProps {
  onOpenSettings?: () => void;
}

export default function UserProfile({ onOpenSettings }: UserProfileProps = {}) {
  const [isOpen, setIsOpen] = useState(false);
  const [showAuth, setShowAuth] = useState(false);
  const [showProfile, setShowProfile] = useState(false);
  const queryClient = useQueryClient();

  const meQuery = useQuery({
    queryKey: ['me'],
    queryFn: getMe,
    retry: false,
  });

  const authMutation = useMutation({
    mutationFn: async (args: { mode: 'login' | 'register'; email: string; password: string; name?: string }) => {
      return args.mode === 'login'
        ? await login({ email: args.email, password: args.password })
        : await register({ email: args.email, password: args.password, name: args.name });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['me'] });
      setShowAuth(false);
      setIsOpen(false);
    },
  });

  const logoutMutation = useMutation({
    mutationFn: logout,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['me'] });
      setIsOpen(false);
    },
  });

  // If we got redirected back from Google OAuth, refresh auth state.
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get('auth_success') === 'true') {
      // Clean URL immediately (guard against "//" which breaks replaceState)
      const safePath = window.location.pathname.replace(/\/{2,}/g, '/') || '/';
      window.history.replaceState({}, '', safePath);
      // Force refresh auth state - invalidate and refetch
      queryClient.invalidateQueries({ queryKey: ['me'] });
      // Small delay to ensure cookie is set, then refetch
      setTimeout(() => {
        queryClient.refetchQueries({ queryKey: ['me'] });
      }, 100);
    }
    const err = params.get('auth_error');
    if (err) {
      const safePath = window.location.pathname.replace(/\/{2,}/g, '/') || '/';
      window.history.replaceState({}, '', safePath);
      // eslint-disable-next-line no-alert
      alert(`Authentication error: ${err}`);
    }
  }, [queryClient]);

  const userInfo = meQuery.data?.authenticated ? meQuery.data.user : null;
  const authError =
    (authMutation.error as any)?.response?.data?.detail ||
    (authMutation.error as any)?.message ||
    null;

  return (
    <div className="relative">
      {userInfo ? (
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="flex items-center gap-2 px-3 py-1.5 hover:bg-[#3e3e42] rounded transition-colors"
        >
          {userInfo.avatar_url ? (
            <img
              src={userInfo.avatar_url}
              alt="Profile"
              className="w-6 h-6 rounded-full object-cover bg-[#007acc]"
              referrerPolicy="no-referrer"
            />
          ) : (
            <div className="w-6 h-6 rounded-full bg-[#007acc] flex items-center justify-center text-xs font-semibold">
              {(userInfo.name || userInfo.email || '?').charAt(0).toUpperCase()}
            </div>
          )}
          <span className="text-xs text-[#cccccc] hidden md:block">
            {userInfo.name || userInfo.email}
          </span>
          <ChevronDown className="w-3 h-3 text-[#858585]" />
        </button>
      ) : (
        <button
          onClick={() => setShowAuth(true)}
          className="flex items-center gap-2 px-3 py-1.5 hover:bg-[#3e3e42] rounded transition-colors"
        >
          <User className="w-4 h-4 text-[#cccccc]" />
          <span className="text-xs text-[#cccccc]">Sign In</span>
        </button>
      )}

      <AuthModal
        isOpen={showAuth}
        onClose={() => setShowAuth(false)}
        onLogin={(args) => authMutation.mutate({ mode: 'login', ...args })}
        onRegister={(args) => authMutation.mutate({ mode: 'register', ...args })}
        isLoading={authMutation.isPending}
        error={authError}
      />

      {userInfo && (
        <ProfileModal
          isOpen={showProfile}
          onClose={() => setShowProfile(false)}
          user={{ name: userInfo.name, email: userInfo.email, avatar_url: userInfo.avatar_url }}
        />
      )}

      {isOpen && userInfo && (
        <>
          <div
            className="fixed inset-0 z-10"
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute right-0 top-full mt-2 w-56 bg-[#3c3c3c] border border-[#3e3e42] rounded shadow-lg z-20 py-1">
            <div className="px-4 py-3 border-b border-[#3e3e42]">
              <p className="text-sm font-semibold text-white">{userInfo.name || 'Account'}</p>
              <p className="text-xs text-[#858585] mt-0.5">{userInfo.email}</p>
            </div>
            <button
              onClick={() => {
                setIsOpen(false);
                setShowProfile(true);
              }}
              className="w-full flex items-center gap-3 px-4 py-2 text-sm text-[#cccccc] hover:bg-[#37373d] transition-colors"
            >
              <UserCircle className="w-4 h-4" />
              Profile
            </button>
            <button
              onClick={() => {
                setIsOpen(false);
                onOpenSettings?.();
              }}
              className="w-full flex items-center gap-3 px-4 py-2 text-sm text-[#cccccc] hover:bg-[#37373d] transition-colors"
            >
              <Settings className="w-4 h-4" />
              Settings
            </button>
            <button
              onClick={() => logoutMutation.mutate()}
              className="w-full flex items-center gap-3 px-4 py-2 text-sm text-[#cccccc] hover:bg-[#37373d] transition-colors"
            >
              <LogOut className="w-4 h-4" />
              {logoutMutation.isPending ? 'Signing out…' : 'Sign Out'}
            </button>
          </div>
        </>
      )}
    </div>
  );
}
