import styles from "./TicketInput.module.css";

const MAX_LENGTH = 10000;

interface TicketInputProps {
  value: string;
  onChange: (value: string) => void;
}

function TicketInput({ value, onChange }: TicketInputProps) {
  return (
    <div className={styles.wrapper}>
      <label htmlFor="ticket-text" className={styles.label}>
        工单文本
      </label>
      <textarea
        id="ticket-text"
        className={styles.textarea}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="请在此输入工单内容，例如：我已经付款，但是会员还没有生效。"
        rows={6}
        maxLength={MAX_LENGTH}
      />
      <div className={styles.counter}>
        {value.length} / {MAX_LENGTH}
      </div>
    </div>
  );
}

export default TicketInput;
