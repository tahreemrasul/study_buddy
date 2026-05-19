"use client";

import Image from "next/image";
import { useState } from "react";
import { StudyState, QAPair, Difficulty } from "../types";

interface Props {
  state: StudyState;
}

const DIFF_FILTERS: (Difficulty | "All")[] = ["All", "Easy", "Medium", "Hard"];

function diffStyle(d: Difficulty) {
  if (d === "Easy")   return "bg-green-50 text-green-600 border border-green-200";
  if (d === "Medium") return "bg-amber-50 text-amber-600 border border-amber-200";
  return "bg-red-50 text-red-500 border border-red-200";
}

function filterBtnStyle(f: Difficulty | "All", active: boolean) {
  if (!active) return "bg-white border border-border text-muted hover:text-ink";
  if (f === "All")    return "bg-ink text-white border border-ink";
  if (f === "Easy")   return "bg-green-50 text-green-600 border border-green-200";
  if (f === "Medium") return "bg-amber-50 text-amber-600 border border-amber-200";
  return "bg-red-50 text-red-500 border border-red-200";
}

export default function QATab({ state }: Props) {
  const [filter, setFilter]   = useState<Difficulty | "All">("All");
  const [index, setIndex]     = useState(0);
  const [flipped, setFlipped] = useState(false);

  if (!state.qa || !Array.isArray(state.qa) || state.qa.length === 0) {
  const isWorking = state.isStreaming || state.activeStep > 0;
  return (
    <div className="flex flex-col items-center justify-center py-20 gap-4 text-center">
      <Image
        src={isWorking ? "/owls/owl_think.png" : "/owls/owl_idle.png"}
        alt="" width={60} height={60}
        className={`pixelated ${isWorking ? "animate-think" : "animate-float"}`}
      />
      <p className="font-display italic text-muted text-[0.95rem]">
        {isWorking
          ? "Q&A pairs are being generated..."
          : "Your Q&A cards will appear here."}
      </p>
      <p className="text-[0.6rem] uppercase tracking-widest text-border">
        {isWorking ? "almost there" : "enter a topic above"}
      </p>
    </div>
  );
}

  const filtered = filter === "All" ? state.qa : state.qa.filter(q => q.difficulty === filter);
  const total    = filtered.length;
  const current  = filtered[index] ?? filtered[0];

  function goTo(i: number) {
    setIndex(i);
    setFlipped(false);
  }

  function navigate(dir: number) {
    const next = index + dir;
    if (next < 0 || next >= total) return;
    goTo(next);
  }

  function handleFilter(f: Difficulty | "All") {
    setFilter(f);
    setIndex(0);
    setFlipped(false);
  }

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-7">
        <div className="flex items-center gap-3">
          <Image src="/owls/owl_idle.png" alt="" width={38} height={38}
            className="pixelated animate-float flex-shrink-0" />
          <h2 className="font-display text-[1.2rem] font-semibold text-ink">
            Test Yourself
          </h2>
        </div>
        <span className="text-[0.65rem] text-muted">{index + 1} / {total}</span>
      </div>

      {/* Difficulty filter */}
      <div className="flex gap-2 mb-7">
        {DIFF_FILTERS.map(f => (
          <button key={f} onClick={() => handleFilter(f)}
            className={`text-[0.62rem] uppercase tracking-wide px-3 py-1.5
                        rounded-full transition-all ${filterBtnStyle(f, filter === f)}`}>
            {f}
          </button>
        ))}
      </div>

      {/* Reset */}
      <div className="flex justify-end mb-3">
        <button onClick={() => { setIndex(0); setFlipped(false); }}
          className="text-[0.62rem] text-muted border border-border px-3 py-1.5
                     rounded-lg hover:border-primary hover:text-primary transition-all">
          ↺ reset
        </button>
      </div>

      {/* Flip card */}
      {current && (
        <div className="mb-5" style={{ perspective: "1200px" }}>
          <div onClick={() => setFlipped(f => !f)}
            className="relative w-full cursor-pointer"
            style={{
              height: "280px",
              transformStyle: "preserve-3d",
              transition: "transform 0.6s cubic-bezier(0.4,0,0.2,1)",
              transform: flipped ? "rotateY(180deg)" : "rotateY(0deg)",
            }}>

            {/* Front */}
            <div className="absolute inset-0 rounded-2xl border-[1.5px] border-border
                            bg-white shadow-md px-8 py-8 flex flex-col justify-between"
              style={{ backfaceVisibility: "hidden" }}>
              <div className="flex items-center justify-between">
                <span className="text-[0.6rem] uppercase tracking-widest text-muted">Question</span>
                <span className={`text-[0.58rem] px-2 py-0.5 rounded-full ${diffStyle(current.difficulty)}`}>
                  {current.difficulty}
                </span>
              </div>
              <p className="font-display text-[1.1rem] font-semibold leading-snug text-ink">
                {current.question}
              </p>
              <span className="text-[0.58rem] text-border tracking-wide">
                tap to reveal answer →
              </span>
            </div>

            {/* Back */}
            <div className="absolute inset-0 rounded-2xl border-[1.5px] border-primary-mid
                            bg-primary-light shadow-md px-8 py-8 flex flex-col justify-between"
              style={{ backfaceVisibility: "hidden", transform: "rotateY(180deg)" }}>
              <div className="flex items-center justify-between">
                <span className="text-[0.6rem] uppercase tracking-widest text-primary">Answer</span>
                <span className={`text-[0.58rem] px-2 py-0.5 rounded-full ${diffStyle(current.difficulty)}`}>
                  {current.difficulty}
                </span>
              </div>
              <p className="font-display text-[0.9rem] leading-relaxed text-primary">
                {current.answer}
              </p>
              <span className="text-[0.58rem] text-primary-mid tracking-wide">
                tap to flip back
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Navigation */}
      <div className="flex items-center justify-center gap-4 mb-4">
        <button onClick={() => navigate(-1)} disabled={index === 0}
          className="w-9 h-9 rounded-full border-[1.5px] border-border flex items-center
                     justify-center text-ink-soft hover:border-primary hover:text-primary
                     hover:bg-primary-light transition-all disabled:opacity-30
                     disabled:cursor-not-allowed">
          ←
        </button>
        <div className="flex gap-1.5 items-center">
          {filtered.map((_, i) => (
            <button key={i} onClick={() => goTo(i)}
              className="rounded-full transition-all"
              style={{
                width:        i === index ? "18px" : "6px",
                height:       "6px",
                background:   i === index ? "#4f46e5" : "#e5e7eb",
                borderRadius: i === index ? "3px"    : "50%",
              }} />
          ))}
        </div>
        <button onClick={() => navigate(1)} disabled={index === total - 1}
          className="w-9 h-9 rounded-full border-[1.5px] border-border flex items-center
                     justify-center text-ink-soft hover:border-primary hover:text-primary
                     hover:bg-primary-light transition-all disabled:opacity-30
                     disabled:cursor-not-allowed">
          →
        </button>
      </div>

      {/* Progress bar */}
      <div className="h-[3px] bg-border-light rounded-full overflow-hidden">
        <div className="h-full rounded-full transition-all duration-300"
          style={{
            width:      `${((index + 1) / total) * 100}%`,
            background: "linear-gradient(90deg, #4f46e5, #f97316)",
          }} />
      </div>
    </div>
  );
}