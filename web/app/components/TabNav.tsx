export type Tab = "progress" | "guide" | "qa";

interface Props {
  active: Tab;
  onChange: (tab: Tab) => void;
}

const TABS: { id: Tab; label: string; done: boolean }[] = [
  { id: "progress", label: "Progress",    done: false },
  { id: "guide",    label: "Study Guide", done: true  },
  { id: "qa",       label: "Q&A",         done: true  },
];

export default function TabNav({ active, onChange }: Props) {
  return (
    <div className="flex gap-0.5 bg-surface border border-border rounded-[10px] p-1 mb-8">
      {TABS.map((tab) => (
        <button
          key={tab.id}
          onClick={() => onChange(tab.id)}
          className={`flex-1 flex items-center justify-center gap-2 text-[0.68rem] 
                      tracking-wide px-4 py-2.5 rounded-[7px] transition-all
                      ${active === tab.id
                        ? "bg-white text-primary shadow-sm font-medium"
                        : "text-muted hover:text-ink hover:bg-white"
                      }`}
        >
          <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0
                            ${active === tab.id ? "bg-primary"
                            : tab.done         ? "bg-accent"
                            :                    "bg-border"}`}
          />
          {tab.label}
        </button>
      ))}
    </div>
  );
}