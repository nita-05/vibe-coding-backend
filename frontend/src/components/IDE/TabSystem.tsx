import { X } from 'lucide-react';

interface TabSystemProps {
  tabs: string[];
  activeTab: string | null | (string | null)[];
  onTabClick: (path: string) => void;
  onTabClose: (path: string, e: React.MouseEvent) => void;
  getTabLabel: (path: string) => string;
}

export default function TabSystem({
  tabs,
  activeTab,
  onTabClick,
  onTabClose,
  getTabLabel
}: TabSystemProps) {
  if (tabs.length === 0) return null;

  const activeTabs = Array.isArray(activeTab) ? activeTab.filter(Boolean) : (activeTab ? [activeTab] : []);

  return (
    <div className="h-9 bg-[#2d2d30] border-b border-[#3e3e42] flex items-end overflow-x-auto">
      {tabs.map((path) => {
        const isActive = activeTabs.includes(path);
        const label = getTabLabel(path);

        return (
          <div
            key={path}
            className={`
              flex items-center gap-2 px-4 py-1.5 cursor-pointer text-sm
              border-r border-[#3e3e42] min-w-[120px] max-w-[200px]
              ${isActive ? 'bg-[#1e1e1e] text-white border-t-2 border-[#007acc]' : 'bg-[#2d2d30] text-[#cccccc] hover:bg-[#37373d]'}
            `}
            onClick={() => onTabClick(path)}
          >
            <span className="flex-1 truncate text-xs">{label}</span>
            <button
              onClick={(e) => onTabClose(path, e)}
              className={`
                p-0.5 rounded hover:bg-[#3e3e42] transition-colors
                ${isActive ? 'text-[#cccccc]' : 'text-[#858585]'}
              `}
            >
              <X className="w-3 h-3" />
            </button>
          </div>
        );
      })}
    </div>
  );
}
