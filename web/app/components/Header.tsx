import Image from "next/image";

export default function Header() {
  return (
    <header className="sticky top-0 z-50 h-[62px] flex items-center justify-between px-10"
      style={{ background: "linear-gradient(135deg, #4f46e5 0%, #6366f1 50%, #7c3aed 100%)" }}>
      
      <div className="flex items-center gap-3">
        <Image
          src="/owls/owl_idle.png"
          alt="Study Buddy owl"
          width={34}
          height={34}
          className="pixelated animate-float"
        />
        <span className="font-display text-[1.15rem] font-semibold tracking-tight text-white">
          Study <em className="text-accent">Buddy</em>
        </span>
      </div>

      <span className="text-[0.6rem] uppercase tracking-widest text-white/70 border border-white/20 bg-white/10 px-3 py-1 rounded-full">
        Google ADK · multi-agent
      </span>

    </header>
  );
}