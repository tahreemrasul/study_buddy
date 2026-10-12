"use client";

import Image from "next/image";
import { useState, useRef } from "react";

const EXAMPLE_TOPICS = [
  "transformer attention",
  "gradient descent",
  "RAG pipelines",
  "dropout in neural networks",
];

const MAX_PDF_MB = 10;

interface Props {
  onGenerate: (topic: string, file: File | null) => void;
  isStreaming: boolean;
}

export default function InputSection({ onGenerate, isStreaming }: Props) {
  const [topic, setTopic] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [fileError, setFileError] = useState<string | null>(null);
  const typingTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const fileInput = useRef<HTMLInputElement>(null);

  function handleFile(e: React.ChangeEvent<HTMLInputElement>) {
    const picked = e.target.files?.[0];
    e.target.value = "";  // allow re-picking the same file
    if (!picked) return;
    if (picked.type !== "application/pdf") {
      setFileError("Only PDF files are supported.");
      return;
    }
    if (picked.size > MAX_PDF_MB * 1024 * 1024) {
      setFileError(`PDF is too large (max ${MAX_PDF_MB} MB).`);
      return;
    }
    setFileError(null);
    setFile(picked);
  }

  function handleInput(e: React.ChangeEvent<HTMLTextAreaElement>) {
    setTopic(e.target.value);
    setIsTyping(true);
    if (typingTimer.current) clearTimeout(typingTimer.current);
    typingTimer.current = setTimeout(() => setIsTyping(false), 1600);
  }

  return (
    <section className="mb-11">
      {/* Eyebrow */}
      <div className="flex items-center gap-2 mb-2">
        <span className="w-4 h-px bg-primary inline-block" />
        <span className="text-[0.6rem] uppercase tracking-[0.14em] text-primary">
          your study companion
        </span>
      </div>

      {/* Title */}
      <h1 className="font-display text-[1.75rem] font-semibold tracking-tight text-ink mb-2">
        What do you want to <em className="text-primary">learn today?</em>
      </h1>
      <p className="text-[0.72rem] text-muted leading-relaxed mb-7">
        Type any topic — short or detailed — or attach a PDF of your notes. Six agents build your complete study guide.
      </p>

      {/* Input card */}
      <div className="relative rounded-[14px] border-[1.5px] border-border bg-white shadow-sm
                      focus-within:border-primary-mid focus-within:ring-3 focus-within:ring-primary-light
                      overflow-hidden">
        {/* Top accent bar */}
        <div className="absolute top-0 left-0 right-0 h-[2px]"
          style={{ background: "linear-gradient(90deg, #4f46e5, #f97316)" }} />

        <div className="px-6 pt-7 pb-4">
          <p className="text-[0.6rem] uppercase tracking-[0.12em] text-muted mb-2">
            study topic
          </p>

          {/* Owl + textarea row */}
          <div className="flex items-start gap-3">
            <Image
              src={isTyping ? "/owls/owl_think.png" : "/owls/owl_idle.png"}
              alt=""
              width={30}
              height={30}
              className={`pixelated mt-1 flex-shrink-0 ${isTyping ? "animate-think" : "animate-float"}`}
            />
            <textarea
              rows={2}
              value={topic}
              onChange={handleInput}
              placeholder="e.g. Neural networks, Keynesian economics, CRISPR gene editing..."
              className="flex-1 bg-transparent border-none outline-none resize-none
                         font-display text-[0.95rem] leading-relaxed text-ink
                         placeholder:text-gray-200 placeholder:italic"
            />
          </div>

          {/* Footer */}
          <div className="flex items-center justify-between mt-4 pt-3 border-t border-border-light flex-wrap gap-2">
            <div className="flex gap-2 flex-wrap">
              {EXAMPLE_TOPICS.map((t) => (
                <button
                  key={t}
                  onClick={() => setTopic(t)}
                  className="text-[0.6rem] bg-surface border border-border text-muted
                             px-3 py-1 rounded-full hover:bg-primary-light hover:border-primary-mid
                             hover:text-primary transition-all"
                >
                  {t}
                </button>
              ))}
            </div>
            <div className="flex items-center gap-2">
              <input
                ref={fileInput}
                type="file"
                accept="application/pdf"
                onChange={handleFile}
                className="hidden"
              />
              {file ? (
                <span className="flex items-center gap-2 bg-accent-light text-accent border border-accent-mid
                                 text-[0.68rem] font-medium tracking-wide pl-4 pr-2 py-2.5 rounded-lg">
                  <span className="max-w-[160px] truncate">{file.name}</span>
                  <button
                    onClick={() => setFile(null)}
                    disabled={isStreaming}
                    aria-label="Remove PDF"
                    className="w-5 h-5 rounded leading-none hover:bg-accent-mid transition-all
                               disabled:cursor-not-allowed"
                  >
                    ×
                  </button>
                </span>
              ) : (
                <button
                  onClick={() => fileInput.current?.click()}
                  disabled={isStreaming}
                  className="flex items-center gap-2 bg-white border border-primary-mid text-primary text-[0.68rem]
                             font-medium tracking-wide px-5 py-2.5 rounded-lg
                             hover:bg-primary-light transition-all
                             disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  + Attach PDF
                </button>
              )}
              <button
                onClick={() => onGenerate(topic, file)}
                disabled={isStreaming || (!topic.trim() && !file)}
                className="flex items-center gap-2 bg-primary border border-primary text-white text-[0.68rem]
               font-medium tracking-wide px-5 py-2.5 rounded-lg
               hover:bg-indigo-700 transition-all shadow-md shadow-indigo-200
               disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-primary"
              >
                {isStreaming ? (
                  <>
                    <span className="w-1.5 h-1.5 rounded-full bg-accent animate-pulse" />
                    Generating...
                  </>
                ) : (
                  <>
                    <span className="w-1.5 h-1.5 rounded-full bg-accent" />
                    Generate guide
                  </>
                )}
              </button>
            </div>
          </div>
          {fileError && (
            <p className="text-[0.6rem] text-accent mt-2">{fileError}</p>
          )}
        </div>
      </div>
    </section>
  );
}