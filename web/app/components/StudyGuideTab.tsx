import Image from "next/image";
import ReactMarkdown from "react-markdown";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import "katex/dist/katex.min.css";
import { StudyState } from "../types";

interface Props {
  state: StudyState;
}

export default function StudyGuideTab({ state }: Props) {
  if (!state.studyGuide) {
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
            ? "Your study guide is being prepared..."
            : "Generate a study guide to get started."}
        </p>
        <p className="text-[0.6rem] uppercase tracking-widest text-border">
          {isWorking ? "agents are still working" : "enter a topic above"}
        </p>
      </div>
    );
  }

  return (
    <div>
      {/* Header */}
      <div className="flex items-center gap-3 mb-2">
        <Image src="/owls/owl_idle.png" alt="" width={42} height={42}
          className="pixelated animate-float flex-shrink-0" />
        <div>
          <h2 className="font-display text-[1.5rem] font-semibold tracking-tight text-ink">
            {state.topic} — Study Guide
          </h2>
          <div className="flex items-center gap-3 mt-1 text-[0.65rem] text-muted">
            <span className="text-border">·</span>
            <span className="text-accent">● complete</span>
          </div>
        </div>
      </div>

      <div className="border-b border-border-light mb-6" />

      {/* Markdown content */}
      <div className="
        prose prose-sm max-w-none
        prose-headings:font-display prose-headings:font-semibold prose-headings:text-ink
        prose-h1:text-[1.3rem] prose-h1:mt-8 prose-h1:mb-3
        prose-h2:text-[1.1rem] prose-h2:mt-6 prose-h2:mb-2 prose-h2:text-primary
        prose-h3:text-[0.95rem] prose-h3:mt-4 prose-h3:mb-1.5 prose-h3:text-ink
        prose-p:text-[0.78rem] prose-p:leading-[1.9] prose-p:text-ink-soft prose-p:text-justify
        prose-li:text-[0.78rem] prose-li:leading-[1.9] prose-li:text-ink-soft
        prose-strong:text-ink prose-strong:font-medium
        prose-ul:my-2 prose-ol:my-2
        prose-hr:border-border-light
      ">
        <ReactMarkdown
          remarkPlugins={[remarkMath]}
          rehypePlugins={[rehypeKatex]}
        >
          {state.studyGuide}
        </ReactMarkdown>
      </div>
    </div>
  );
}