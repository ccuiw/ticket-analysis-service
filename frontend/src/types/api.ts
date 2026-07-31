/** 分析请求 */
export interface AnalyzeRequest {
  ticket_text: string;
  prompt_version: "v1" | "v2";
}

/** 分析结果 */
export interface AnalysisResult {
  category: string;
  priority: string;
  summary: string;
  tags: string[];
  order_id: string | null;
  confidence: number;
  need_human_review: boolean;
  uncertain_fields: string[];
}

/** API 错误响应 */
export interface ApiError {
  detail: string;
  error_type: string;
}

/** 前端分析状态 */
export type AnalysisState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "success"; result: AnalysisResult }
  | { status: "error"; error: string };
