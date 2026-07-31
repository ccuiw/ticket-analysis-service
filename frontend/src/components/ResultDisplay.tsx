import type { AnalysisState } from "../types/api";
import styles from "./ResultDisplay.module.css";

interface ResultDisplayProps {
  state: AnalysisState;
}

function ResultDisplay({ state }: ResultDisplayProps) {
  if (state.status === "idle") {
    return null;
  }

  if (state.status === "loading") {
    return (
      <div className={styles.loading}>
        <div className={styles.spinner} />
        <span>正在分析工单，请稍候...</span>
      </div>
    );
  }

  if (state.status === "error") {
    return (
      <div className={styles.error}>
        <strong>分析失败</strong>
        <p>{state.error}</p>
      </div>
    );
  }

  // success
  const { result } = state;

  const fields = [
    { label: "类别", value: result.category },
    { label: "优先级", value: result.priority },
    { label: "摘要", value: result.summary },
    {
      label: "标签",
      value: result.tags.length > 0 ? result.tags.join("、") : "无",
    },
    { label: "关联订单号", value: result.order_id ?? "不确定" },
    {
      label: "置信度",
      value: `${(result.confidence * 100).toFixed(0)}%`,
    },
    {
      label: "是否需要人工审核",
      value: result.need_human_review ? "是" : "否",
    },
    {
      label: "不确定字段",
      value:
        result.uncertain_fields.length > 0
          ? result.uncertain_fields.join("、")
          : "无",
    },
  ];

  return (
    <div className={styles.success}>
      <h2 className={styles.resultTitle}>分析结果</h2>

      <dl className={styles.fieldList}>
        {fields.map((f) => (
          <div key={f.label} className={styles.fieldRow}>
            <dt className={styles.fieldLabel}>{f.label}</dt>
            <dd className={styles.fieldValue}>{f.value}</dd>
          </div>
        ))}
      </dl>

      <details className={styles.rawJson}>
        <summary className={styles.rawSummary}>原始 JSON</summary>
        <pre className={styles.rawPre}>
          {JSON.stringify(result, null, 2)}
        </pre>
      </details>
    </div>
  );
}

export default ResultDisplay;
