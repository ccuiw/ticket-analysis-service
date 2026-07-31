import styles from "./AnalyzeButton.module.css";

interface AnalyzeButtonProps {
  onClick: () => void;
  disabled: boolean;
  loading: boolean;
}

function AnalyzeButton({ onClick, disabled, loading }: AnalyzeButtonProps) {
  return (
    <button
      className={styles.button}
      onClick={onClick}
      disabled={disabled}
    >
      {loading ? "分析中..." : "开始分析"}
    </button>
  );
}

export default AnalyzeButton;
