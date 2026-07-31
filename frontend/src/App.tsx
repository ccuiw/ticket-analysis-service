import { useState } from "react";
import type { AnalysisState } from "./types/api";
import { analyzeTicket } from "./api/analyze";
import TicketInput from "./components/TicketInput";
import AnalyzeButton from "./components/AnalyzeButton";
import ResultDisplay from "./components/ResultDisplay";
import styles from "./App.module.css";

function App() {
  const [ticketText, setTicketText] = useState("");
  const [promptVersion, setPromptVersion] = useState<"v1" | "v2">("v1");
  const [state, setState] = useState<AnalysisState>({ status: "idle" });

  const handleAnalyze = async () => {
    if (!ticketText.trim()) {
      return;
    }

    setState({ status: "loading" });

    try {
      const result = await analyzeTicket(ticketText, promptVersion);
      setState({ status: "success", result });
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "分析请求失败，请稍后重试";
      setState({ status: "error", error: message });
    }
  };

  const isAnalyzing = state.status === "loading";
  const canAnalyze = ticketText.trim().length > 0 && !isAnalyzing;

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <h1 className={styles.title}>工单分析服务</h1>
        <p className={styles.subtitle}>
          输入工单文本，自动提取结构化分析结果
        </p>
      </header>

      <main className={styles.main}>
        <section className={styles.inputSection}>
          <TicketInput value={ticketText} onChange={setTicketText} />

          <div className={styles.controls}>
            <div className={styles.versionSelector}>
              <label className={styles.versionLabel}>
                提示词版本：
                <select
                  value={promptVersion}
                  onChange={(e) =>
                    setPromptVersion(e.target.value as "v1" | "v2")
                  }
                  className={styles.select}
                >
                  <option value="v1">v1 (Zero-shot)</option>
                  <option value="v2">v2 (Few-shot)</option>
                </select>
              </label>
            </div>

            <AnalyzeButton
              onClick={handleAnalyze}
              disabled={!canAnalyze}
              loading={isAnalyzing}
            />
          </div>
        </section>

        <section className={styles.resultSection}>
          <ResultDisplay state={state} />
        </section>
      </main>
    </div>
  );
}

export default App;
