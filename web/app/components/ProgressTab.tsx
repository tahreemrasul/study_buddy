import Image from "next/image";
import ReactMarkdown from "react-markdown";
import { StudyState, STEP_LABELS } from "../types";

interface Props {
  state: StudyState;
}

function stepStatus(stepIndex: number, activeStep: number) {
  if (activeStep === 0) return "idle";
  if (activeStep >= 7) return "done";  // all complete
  if (stepIndex < activeStep - 1) return "done";
  if (stepIndex === activeStep - 1) return "active";
  return "idle";
}

function badgeClass(status: string) {
  if (status === "done") return "bg-accent-light text-accent border border-accent-mid";
  if (status === "active") return "bg-primary-light text-primary border border-primary-mid animate-pulse";
  return "bg-surface text-muted border border-border opacity-60";
}

function CardContent({ stepIndex, state }: { stepIndex: number; state: StudyState }) {
  const skeletons = (
    <div className="space-y-2">
      {[72, 88, 58, 78].map((w, i) => (
        <div key={i} className="h-[10px] rounded animate-pulse bg-border"
          style={{ width: `${w}%` }} />
      ))}
    </div>
  );

  if (stepIndex === 0) {
    if (!state.overview) return skeletons;
    return (
      <div className="prose prose-sm max-w-none
                    prose-p:text-[0.74rem] prose-p:leading-relaxed prose-p:text-ink-soft
                    prose-strong:text-ink prose-strong:font-medium">
        <ReactMarkdown>{state.overview}</ReactMarkdown>
      </div>
    );
  }

  if (stepIndex === 1) {
    if (!state.queries) return skeletons;
    return (
      <div className="flex flex-wrap gap-2">
        {state.queries.split("\n").filter(Boolean).map((q, i) => (
          <span key={i}
            className="text-[0.65rem] italic font-display bg-accent-light text-accent
                       border border-accent-mid px-3 py-1 rounded-full">
            {q.replace(/^\d+\.\s*/, "")}
          </span>
        ))}
      </div>
    );
  }

  if (stepIndex === 2) {
    if (!state.search) return skeletons;

    const sourceMatches = state.search.match(/\*\*Sources Used\*\*:\s*([^\n]+)/g) ?? [];
    const KNOWN_SOURCES = ["Wikipedia", "ArXiv", "Internal Knowledge"];
    const sources = Array.from(
      new Set(
        sourceMatches
          .flatMap(line => line.replace("**Sources Used**:", "").trim().split(","))
          .map(s => s.trim())
          .filter(s => KNOWN_SOURCES.some(k => s.toLowerCase().includes(k.toLowerCase())))
      )
    );

    return (
      <div className="flex flex-wrap gap-2">
        {sources.length > 0
          ? sources.map((s, i) => (
            <span key={i}
              className="text-[0.62rem] bg-accent-light text-accent
                         border border-accent-mid px-2.5 py-1 rounded-full">
              {s}
            </span>
          ))
          : <p className="text-[0.72rem] text-muted">Sources retrieved.</p>
        }
      </div>
    );
  }

  if (stepIndex === 3) {
    if (!state.outline) return skeletons;
    return (
      <div className="prose prose-sm max-w-none
                    prose-p:text-[0.74rem] prose-p:leading-relaxed prose-p:text-ink-soft
                    prose-li:text-[0.74rem] prose-li:leading-relaxed prose-li:text-ink-soft
                    prose-strong:text-ink prose-strong:font-medium
                    prose-ol:my-1 prose-ul:my-1">
        <ReactMarkdown>{state.outline}</ReactMarkdown>
      </div>
    );
  }

  if (stepIndex === 4) {
    if (!state.studyGuide) return skeletons;
    return <p>Study guide ready — see the Study Guide tab.</p>;
  }

  if (stepIndex === 5) {
    if (!state.qa) return skeletons;
    return <p>{state.qa.length} questions ready — see the Q&amp;A tab.</p>;
  }

  return null;
}

const STEP_METAS = [
  (s: StudyState) => s.overview ? "complete" : "generating",
  (s: StudyState) => s.queries ? "2 queries" : "generating",
  (s: StudyState) => s.search ? "sources found" : "generating",
  (s: StudyState) => s.outline ? "structured" : "generating",
  (s: StudyState) => s.studyGuide ? "complete" : "generating",
  (s: StudyState) => s.qa ? `${s.qa.length} questions` : "generating",
];

const STEP_TITLES_WAITING = [
  "Overview",
  "Search queries",
  "Web search",
  "Outline",
  "Study guide",
  "Q&A",
];

const STEP_TITLES_ACTIVE = [
  "Generating overview...",
  "Generating queries...",
  "Searching the web...",
  "Building structure...",
  "Writing study guide...",
  "Generating Q&A...",
];

const STEP_TITLES_DONE = [
  "Overview complete",
  "Queries ready",
  "Sources retrieved",
  "Outline ready",
  "Study guide complete",
  "Q&A ready",
];

export default function ProgressTab({ state }: Props) {
  const { activeStep, isStreaming } = state;

  return (
    <div>
      {/* Pipeline bar */}
      <p className="text-[0.6rem] uppercase tracking-[0.12em] text-muted mb-3
                    flex items-center gap-2 after:flex-1 after:h-px after:bg-border-light">
        agent pipeline
      </p>

      <div className="flex gap-1.5 mb-2.5">
        {STEP_LABELS.map((_, i) => {
          const status = stepStatus(i, activeStep);
          return (
            <div key={i}
              className={`flex-1 h-[5px] rounded-full relative overflow-hidden
                          ${status === "done" ? "bg-accent"
                  : status === "active" ? "bg-primary-mid"
                    : "bg-border"}`}>
              {status === "active" && (
                <span className="absolute inset-0 bg-gradient-to-r
                                 from-transparent via-primary to-transparent animate-sweep" />
              )}
            </div>
          );
        })}
      </div>

      <div className="grid grid-cols-6 gap-1.5 mb-3">
        {STEP_LABELS.map((label, i) => {
          const status = stepStatus(i, activeStep);
          return (
            <p key={i}
              className={`text-center text-[0.55rem]
                          ${status === "done" ? "text-accent"
                  : status === "active" ? "text-primary"
                    : "text-muted opacity-50"}`}>
              {label}
            </p>
          );
        })}
      </div>

      {/* Active callout — only show while streaming */}
      {isStreaming && activeStep > 0 && activeStep <= 6 && (
        <div className="flex items-center gap-3 bg-primary-light border border-primary-mid
                        rounded-lg px-4 py-2.5 mb-8">
          <Image src="/owls/owl_think.png" alt="" width={38} height={38}
            className="pixelated animate-think flex-shrink-0" />
          <span className="text-[0.68rem] text-primary flex-1">
            {STEP_LABELS[activeStep - 1]} agent is working...
          </span>
        </div>
      )}

      {/* Not started state */}
      {!isStreaming && activeStep === 0 && (
        <div className="flex items-center gap-3 bg-surface border border-border
                        rounded-lg px-4 py-2.5 mb-8">
          <Image src="/owls/owl_idle.png" alt="" width={38} height={38}
            className="pixelated animate-float flex-shrink-0" />
          <span className="text-[0.68rem] text-muted">
            Enter a topic above and hit Generate to start.
          </span>
        </div>
      )}

      {/* Completed state */}
      {!isStreaming && activeStep === 6 && (
        <div className="flex items-center gap-3 bg-accent-light border border-accent-mid
                        rounded-lg px-4 py-2.5 mb-8">
          <Image src="/owls/owl_idle.png" alt="" width={38} height={38}
            className="pixelated animate-float flex-shrink-0" />
          <span className="text-[0.68rem] text-accent flex-1">
            All done! Check the Study Guide and Q&amp;A tabs.
          </span>
        </div>
      )}

      {/* Output cards */}
      <p className="text-[0.6rem] uppercase tracking-[0.12em] text-muted mb-3
                    flex items-center gap-2 after:flex-1 after:h-px after:bg-border-light">
        outputs
      </p>

      <div className="flex flex-col gap-3">
        {STEP_LABELS.map((label, i) => {
          const status = stepStatus(i, activeStep);

          return (
            <div key={i}
              className={`border rounded-[10px] bg-white overflow-hidden transition-opacity
                          ${status === "active" ? "border-primary-mid" : "border-border"}
                          ${status === "idle" ? "opacity-50 pointer-events-none" : ""}`}>

              {/* Card header */}
              <div className={`flex items-center justify-between px-[18px] py-3 min-h-[52px]
                               ${status === "active" ? "bg-primary-light" : ""}`}>
                <div className="flex items-center gap-2.5">
                  <span className={`text-[0.58rem] font-medium px-2 py-0.5 rounded w-[100px] text-center
                                    uppercase tracking-wide ${badgeClass(status)}`}>
                    {label}
                  </span>
                  <span className={`font-display text-[0.88rem] font-semibold
                                    ${status === "idle" ? "text-muted"
                      : status === "active" ? "text-primary"
                        : "text-ink"}`}>
                    {status === "idle" ? STEP_TITLES_WAITING[i]
                      : status === "active" ? STEP_TITLES_ACTIVE[i]
                        : STEP_TITLES_DONE[i]}
                  </span>
                </div>
                {status === "active" && (
                  <span className="text-[0.6rem] text-primary">
                    {STEP_METAS[i](state)}
                  </span>
                )}
              </div>

              {/* Card body */}
              {(status === "active" || status === "done") && (
                <div className="px-[18px] py-4 text-[0.74rem] leading-relaxed text-ink-soft
                                border-t border-border-light">
                  <CardContent stepIndex={i} state={state} />
                </div>
              )}

            </div>
          );
        })}
      </div>
    </div>
  );
}