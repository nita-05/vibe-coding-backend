import { X } from 'lucide-react';

export default function ProfileModal({
  isOpen,
  onClose,
  user,
}: {
  isOpen: boolean;
  onClose: () => void;
  user: { name?: string | null; email: string; avatar_url?: string | null };
}) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
      <div className="w-full max-w-md bg-[#252526] border border-[#3e3e42] rounded-lg shadow-xl">
        <div className="flex items-center justify-between p-4 border-b border-[#3e3e42]">
          <h2 className="text-base font-semibold text-white">Profile</h2>
          <button
            onClick={onClose}
            className="p-1 hover:bg-[#3e3e42] rounded transition-colors"
            aria-label="Close"
          >
            <X className="w-4 h-4 text-[#cccccc]" />
          </button>
        </div>

        <div className="p-4">
          <div className="flex items-center gap-3">
            {user.avatar_url ? (
              <img
                src={user.avatar_url}
                alt="Profile"
                className="w-12 h-12 rounded-full object-cover bg-[#007acc]"
                referrerPolicy="no-referrer"
              />
            ) : (
              <div className="w-12 h-12 rounded-full bg-[#007acc] flex items-center justify-center text-base font-semibold">
                {(user.name || user.email || '?').charAt(0).toUpperCase()}
              </div>
            )}
            <div>
              <div className="text-sm font-semibold text-white">{user.name || 'Account'}</div>
              <div className="text-xs text-[#9e9e9e]">{user.email}</div>
            </div>
          </div>

          <div className="mt-4 text-xs text-[#858585] leading-relaxed">
            Theme preference, usage history, saved chats, and stats can be added here next (ChatGPT-style).
          </div>

          <div className="mt-4 flex justify-end">
            <button
              onClick={onClose}
              className="px-4 py-2 text-sm bg-[#3e3e42] hover:bg-[#4a4a4f] rounded transition-colors text-white"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

