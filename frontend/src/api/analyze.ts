import type { AnalyzeRequest, AnalysisResult } from "../types/api";

const API_BASE = "http://127.0.0.1:8000";
const REQUEST_TIMEOUT_MS = 30_000;

/**
 * 调用后端工单分析接口。
 *
 * @param ticketText - 工单文本
 * @param promptVersion - 提示词版本 ("v1" | "v2")
 * @returns 分析结果
 * @throws 网络错误、超时或后端返回错误时抛出
 */
export async function analyzeTicket(
  ticketText: string,
  promptVersion: "v1" | "v2"
): Promise<AnalysisResult> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  const body: AnalyzeRequest = {
    ticket_text: ticketText,
    prompt_version: promptVersion,
  };

  let response: Response;
  try {
    response = await fetch(`${API_BASE}/api/v1/tickets/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal: controller.signal,
    });
  } catch (err) {
    clearTimeout(timeoutId);
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new Error("请求超时，请稍后重试");
    }
    throw new Error("网络错误，无法连接到分析服务");
  } finally {
    clearTimeout(timeoutId);
  }

  if (!response.ok) {
    const errorText = await response.text();
    let errorMessage: string;
    try {
      const errorData = JSON.parse(errorText);
      errorMessage = errorData.detail || `服务器错误 (${response.status})`;
    } catch {
      errorMessage = `服务器错误 (${response.status})`;
    }
    throw new Error(errorMessage);
  }

  const result: AnalysisResult = await response.json();
  return result;
}
