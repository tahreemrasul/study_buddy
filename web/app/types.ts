export type Difficulty = "Easy" | "Medium" | "Hard";

export type QAPair = {
  question:   string;
  answer:     string;
  difficulty: Difficulty;
};

export type StepStatus = "idle" | "active" | "done";

export type StudyState = {
  topic:       string;
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