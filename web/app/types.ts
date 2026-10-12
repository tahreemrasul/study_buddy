export type Difficulty = "Easy" | "Medium" | "Hard";

export type QAPair = {
  question:   string;
  answer:     string;
  difficulty: Difficulty;
};

export type StepStatus = "idle" | "active" | "done";

export type SourceDoc = {
  name:   string;
  status:     "reading" | "ready" | "error";
  error?:     string;
  truncated?: boolean;   // text was cut to the proxy's character limit
};

export type StudyState = {
  topic:       string;
  source:      SourceDoc | null;   // uploaded PDF, if any
  activeStep:  number;        // 0 = not started, 1-6 = current step
  overview:    string | null;
  queries:     string | null;
  search:      string | null;
  outline:     string | null;
  studyGuide:  string | null;
  qa:          QAPair[] | null;
  isStreaming: boolean;
};

export const INITIAL_STATE: StudyState = {
  topic:       "",
  source:      null,
  activeStep:  0,
  overview:    null,
  queries:     null,
  search:      null,
  outline:     null,
  studyGuide:  null,
  qa:          null,
  isStreaming: false,
};

export const STEP_LABELS = [
  "① Overview",
  "② Queries",
  "③ Search",
  "④ Outline",
  "⑤ Guide",
  "⑥ Q&A",
];