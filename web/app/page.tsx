"use client";

import { useState } from "react";
import Header from "./components/Header";
import InputSection from "./components/InputSection";
import TabNav, { type Tab } from "./components/TabNav";
import ProgressTab from "./components/ProgressTab";
import StudyGuideTab from "./components/StudyGuideTab";
import QATab from "./components/QATab";
import { useStudySession } from "./hooks/useStudySession";

export default function Home() {
  const [activeTab, setActiveTab] = useState<Tab>("progress");
  const { state, generate }       = useStudySession();

  async function handleGenerate(topic: string) {
    setActiveTab("progress");
    generate(topic);
  }

  return (
    <>
      <Header />
      <main className="max-w-[780px] mx-auto px-10 pt-12 pb-20">
        <InputSection onGenerate={handleGenerate} isStreaming={state.isStreaming} />
        <TabNav active={activeTab} onChange={setActiveTab} />
        {activeTab === "progress" && <ProgressTab state={state} />}
        {activeTab === "guide"    && <StudyGuideTab state={state} />}
        {activeTab === "qa"       && <QATab state={state} />}
      </main>
    </>
  );
}