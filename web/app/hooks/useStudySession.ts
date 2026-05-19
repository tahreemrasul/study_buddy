import { useState, useCallback } from "react";
import { StudyState, INITIAL_STATE, QAPair } from "../types";

const BASE_URL   = "http://localhost:8001";
const APP_NAME   = "study_guide";
const USER_ID    = "u_001";

// Map functionCall names to step numbers
const STEP_MAP: Record<string, number> = {
  topic_overview_agent:  1,
  search_query_agent:    2,
  search_agent:          3,
  outline_agent:         4,
  study_guide_agent:     5,
  question_answer_agent: 6,
};

function parseQA(raw: string): QAPair[] {
  try {
    // Strip markdown code fences
    const clean = raw
      .replace(/```json\n?/g, "")
      .replace(/```\n?/g, "")
      .trim();

    const parsed = JSON.parse(clean);

    // Handle { "study_guide_qa": [...] } wrapper
    if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) {
      const key = Object.keys(parsed)[0];
      const arr = parsed[key];
      if (Array.isArray(arr)) return arr;
    }

    // Handle root array
    if (Array.isArray(parsed)) return parsed;

    return [];
  } catch {
    return [];
  }
}

export function useStudySession() {
  const [state, setState] = useState<StudyState>(INITIAL_STATE);

  const generate = useCallback(async (topic: string) => {
    if (!topic.trim()) return;

    // Reset state and mark as streaming
    setState({ ...INITIAL_STATE, topic, isStreaming: true });

    // Generate a unique session ID per run
    const sessionId = `s_${Date.now()}`;

    try {
      // 1. Create session
      await fetch(`${BASE_URL}/apps/${APP_NAME}/users/${USER_ID}/sessions/${sessionId}`, {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify({}),
      });

      // 2. Open SSE stream
      const response = await fetch(`${BASE_URL}/run_sse`, {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          appName:    APP_NAME,
          userId:     USER_ID,
          sessionId,
          newMessage: {
            role:  "user",
            parts: [{ text: topic }],
          },
          streaming: false,
        }),
      });

      if (!response.body) throw new Error("No response body");

      // 3. Read the stream
      const reader  = response.body.getReader();
      const decoder = new TextDecoder();
      let   buffer  = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() ?? "";

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          const raw = line.slice(6).trim();
          if (!raw) continue;

          try {
            const event = JSON.parse(raw);
            const parts = event?.content?.parts ?? [];
            const delta = event?.actions?.stateDelta ?? {};

            // Detect which agent is active via functionCall
            for (const part of parts) {
              if (part.functionCall?.name) {
                const step = STEP_MAP[part.functionCall.name];
                if (step) setState(s => ({ ...s, activeStep: Math.max(s.activeStep, step) }));
              }
            }

            // Populate state from stateDelta
            if (delta.topic_overview) {
              setState(s => ({ ...s, overview: delta.topic_overview }));
            }
            if (delta.search_queries) {
              setState(s => ({ ...s, queries: delta.search_queries }));
            }
            if (delta.search) {
              setState(s => ({ ...s, search: delta.search }));
            }
            if (delta.outline) {
              setState(s => ({ ...s, outline: delta.outline }));
            }
            if (delta.study_guide) {
              setState(s => ({ ...s, studyGuide: delta.study_guide }));
            }
              if (delta.question_answer) {
                  const qa = parseQA(delta.question_answer);
                  if (Array.isArray(qa) && qa.length > 0) {
                      setState(s => ({ ...s, qa }));
                  }
              }

          } catch {
            // skip malformed events
          }
        }
      }

    } catch (err) {
      console.error("Stream error:", err);
    } finally {
        setState(s => ({
            ...s,
            isStreaming: false,
            activeStep: s.qa ? 7 : s.activeStep,
        }));
    }
  }, []);

  return { state, generate };
}