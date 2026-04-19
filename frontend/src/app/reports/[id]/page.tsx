"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { apiFetch, API_BASE, patchAgentResult } from "@/lib/api";
import { Play, CheckCircle, XCircle, Clock, AlertCircle, ChevronDown, ChevronUp, Loader2, UserX, List, Minus, Pencil } from "lucide-react";

interface CandidateMapping {
  name: string;
  initials: string;
  candidate_number: string;
}

interface Report {
  id: number;
  title: string;
  filename: string;
  status: string;
  content_text: string | null;
  created_at: string;
  anonymized_file_path: string | null;
  mapping_file_path: string | null;
  candidate_mappings: CandidateMapping[] | null;
  kandidater: number[] | null;
}

interface Agent {
  id: number;
  name: string;
  description: string;
  max_score: number;
}

interface CriterionDetail {
  criterion: string;
  comment: string;
  score?: number;
  max_score?: number;
  applicable?: boolean;
  // Legacy format with passed boolean
  passed?: boolean;
}

interface AgentResult {
  id: number;
  agent_config_id: number;
  agent_name: string;
  score: number | null;
  max_score: number | null;
  feedback: string | null;
  details: CriterionDetail[] | null;
  status: string;
  prompt_used?: string | null;
  raw_response?: string | null;
  instructor_score: number | null;
  instructor_comment: string | null;
}

interface Evaluation {
  id: number;
  status: string;
  total_score: number | null;
  max_possible_score: number | null;
  summary: string | null;
  agent_results: AgentResult[];
  created_at: string;
  instructor_total_score: number | null;
}

interface StreamingAgent {
  id: number;
  name: string;
  description: string;
  max_score: number;
  status: "pending" | "running" | "completed" | "error";
  score?: number | null;
  feedback?: string | null;
  details?: CriterionDetail[] | null;
}

export default function ReportDetailPage() {
  const params = useParams();
  const router = useRouter();
  const reportId = params.id as string;

  const [report, setReport] = useState<Report | null>(null);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [selectedAgentIds, setSelectedAgentIds] = useState<Set<number>>(new Set());
  const [evaluation, setEvaluation] = useState<Evaluation | null>(null);
  const [evaluating, setEvaluating] = useState(false);
  const [loading, setLoading] = useState(true);

  // Streaming state
  const [streamingAgents, setStreamingAgents] = useState<Map<number, StreamingAgent>>(new Map());
  const [expandedResults, setExpandedResults] = useState<Set<number>>(new Set());

  // Instructor override state: agentResultId -> { score, comment }
  const [editingResultId, setEditingResultId] = useState<number | null>(null);
  const [editScore, setEditScore] = useState<string>("");
  const [editComment, setEditComment] = useState<string>("");
  const [savingOverride, setSavingOverride] = useState(false);

  const sortedEvaluation = (eval_: Evaluation): Evaluation => ({
    ...eval_,
    agent_results: [...eval_.agent_results].sort((a, b) => {
      const ia = agents.findIndex((ag) => ag.id === a.agent_config_id);
      const ib = agents.findIndex((ag) => ag.id === b.agent_config_id);
      return (ia === -1 ? 999 : ia) - (ib === -1 ? 999 : ib);
    }),
  });

  const startEditing = (result: AgentResult) => {
    setEditingResultId(result.id);
    setEditScore(result.instructor_score !== null ? String(result.instructor_score) : "");
    setEditComment(result.instructor_comment ?? "");
  };

  const cancelEditing = () => {
    setEditingResultId(null);
    setEditScore("");
    setEditComment("");
  };

  const saveOverride = async (evaluationId: number, agentResultId: number) => {
    if (!evaluation) return;
    setSavingOverride(true);
    try {
      const parsedScore = editScore.trim() !== "" ? parseFloat(editScore) : null;
      const updatedEvaluation = await patchAgentResult(evaluationId, agentResultId, {
        instructor_score: parsedScore,
        instructor_comment: editComment.trim() !== "" ? editComment.trim() : null,
      });
      setEvaluation(sortedEvaluation(updatedEvaluation));
      setEditingResultId(null);
    } catch {
      alert("Kunne ikke lagre endringen. Prøv igjen.");
    } finally {
      setSavingOverride(false);
    }
  };

  const toggleResultExpanded = (resultId: number) => {
    setExpandedResults((prev) => {
      const next = new Set(prev);
      if (next.has(resultId)) {
        next.delete(resultId);
      } else {
        next.add(resultId);
      }
      return next;
    });
  };

  useEffect(() => {
    Promise.all([
      apiFetch(`/api/reports/${reportId}`).then((r) => r.json()),
      apiFetch("/api/agents").then((r) => r.json()),
      apiFetch(`/api/evaluations/report/${reportId}`).then((r) => r.json()),
    ])
      .then(([reportData, agentsData, evaluationsData]) => {
        setReport(reportData);
        setAgents(agentsData);
        setSelectedAgentIds(new Set(agentsData.map((a: Agent) => a.id)));
        if (evaluationsData.length > 0) {
          const ev = evaluationsData[0];
          setEvaluation({
            ...ev,
            agent_results: [...ev.agent_results].sort((a: AgentResult, b: AgentResult) => {
              const ia = agentsData.findIndex((ag: Agent) => ag.id === a.agent_config_id);
              const ib = agentsData.findIndex((ag: Agent) => ag.id === b.agent_config_id);
              return (ia === -1 ? 999 : ia) - (ib === -1 ? 999 : ib);
            }),
          });
        }
      })
      .finally(() => setLoading(false));
  }, [reportId]);

  const runEvaluation = async () => {
    setEvaluating(true);
    setStreamingAgents(new Map());
    setEvaluation(null);

    try {
      const response = await fetch(`${API_BASE}/api/evaluations/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          report_id: parseInt(reportId),
          agent_ids: Array.from(selectedAgentIds),
        }),
      });

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) throw new Error("No reader available");

      let buffer = "";
      let evaluationId: number | null = null;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const data = JSON.parse(line.slice(6));

              switch (data.type) {
                case "start":
                  evaluationId = data.evaluation_id;
                  // Initialize all agents with pending status
                  setStreamingAgents(() => {
                    const next = new Map<number, StreamingAgent>();
                    for (const agent of data.agents) {
                      next.set(agent.id, {
                        id: agent.id,
                        name: agent.name,
                        description: agent.description,
                        max_score: agent.max_score,
                        status: "pending",
                      });
                    }
                    return next;
                  });
                  break;

                case "agent_start":
                  setStreamingAgents((prev) => {
                    const next = new Map(prev);
                    const agent = next.get(data.agent_id);
                    if (agent) {
                      next.set(data.agent_id, {
                        ...agent,
                        status: "running",
                      });
                    }
                    return next;
                  });
                  break;

                case "agent_complete":
                  setStreamingAgents((prev) => {
                    const next = new Map(prev);
                    const agent = next.get(data.agent_id);
                    if (agent) {
                      next.set(data.agent_id, {
                        ...agent,
                        status: "completed",
                        score: data.score,
                        feedback: data.feedback,
                        details: data.details,
                      });
                    }
                    return next;
                  });
                  break;

                case "agent_error":
                  setStreamingAgents((prev) => {
                    const next = new Map(prev);
                    const agent = next.get(data.agent_id);
                    if (agent) {
                      next.set(data.agent_id, {
                        ...agent,
                        status: "error",
                      });
                    }
                    return next;
                  });
                  break;

                case "complete":
                  // Fetch the complete evaluation for final display
                  if (evaluationId) {
                    const evalResponse = await apiFetch(
                      `/api/evaluations/${evaluationId}`
                    );
                    const evalData = await evalResponse.json();
                    setEvaluation(sortedEvaluation(evalData));
                  }
                  break;
              }
            } catch {
              // Skip invalid JSON
            }
          }
        }
      }
    } catch (error) {
      console.error("Evaluation failed:", error);
    } finally {
      setEvaluating(false);
    }
  };

  if (loading) {
    return <div className="px-4">Laster...</div>;
  }

  if (!report) {
    return <div className="px-4">Rapport ikke funnet</div>;
  }

  const getStatusIcon = (status: string) => {
    switch (status.toUpperCase()) {
      case "COMPLETED":
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case "RUNNING":
        return <Clock className="w-5 h-5 text-yellow-500 animate-spin" />;
      case "ERROR":
        return <XCircle className="w-5 h-5 text-red-500" />;
      default:
        return <AlertCircle className="w-5 h-5 text-gray-400" />;
    }
  };

  return (
    <div className="px-4">
      {/* Report header */}
      <div className="mb-6">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{report.title}</h1>
            {report.candidate_mappings && report.candidate_mappings.length > 0 && (
              <p className="text-gray-800 font-medium mt-0.5">
                {report.candidate_mappings.map((m) => `${m.name} (${m.candidate_number})`).join(", ")}
              </p>
            )}
            <p className="text-gray-500 text-sm mt-0.5 flex items-center gap-2">
              {report.filename}
              {report.anonymized_file_path && (
                <span className="inline-flex items-center gap-1 px-1.5 py-0.5 bg-green-100 text-green-700 rounded text-xs">
                  <CheckCircle className="w-3 h-3" />
                  Anonymisert
                </span>
              )}
              <span className="text-gray-400">·</span>
              {new Date(report.created_at).toLocaleDateString("no-NO")}
            </p>
          </div>
          <div className="flex gap-2">
            {!report.anonymized_file_path && (
              <button
                onClick={() => router.push(`/reports/${reportId}/anonymize`)}
                className="flex items-center gap-2 px-3 py-2 bg-orange-500 text-white rounded-md hover:bg-orange-600 text-sm"
              >
                <UserX className="w-4 h-4" />
                Anonymiser
              </button>
            )}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left column: Agents overview + start button */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-lg shadow-sm border p-4">
            <div className="flex items-center gap-2 mb-4">
              <List className="w-5 h-5 text-gray-500" />
              <h2 className="text-lg font-semibold">Sjekker</h2>
            </div>

            <div className="space-y-1">
              {agents.map((agent) => (
                <label key={agent.id} className="flex items-center gap-2 py-2 px-1 border-b last:border-0 cursor-pointer hover:bg-gray-50 rounded">
                  <input
                    type="checkbox"
                    checked={selectedAgentIds.has(agent.id)}
                    onChange={() => setSelectedAgentIds((prev) => {
                      const next = new Set(prev);
                      next.has(agent.id) ? next.delete(agent.id) : next.add(agent.id);
                      return next;
                    })}
                    className="w-4 h-4 accent-blue-600"
                  />
                  <div className="flex-1 flex items-center justify-between">
                    <p className="text-sm font-medium text-gray-900">{agent.name}</p>
                    <span className="text-xs text-gray-500 ml-2 shrink-0">{agent.max_score}%</span>
                  </div>
                </label>
              ))}
            </div>

            <button
              onClick={runEvaluation}
              disabled={evaluating || report.status.toUpperCase() !== "READY" || !report.anonymized_file_path || selectedAgentIds.size === 0}
              className="w-full mt-4 flex items-center justify-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Play className="w-4 h-4" />
              {evaluating ? "Evaluerer..." : "Start evaluering"}
            </button>

            {report.status.toUpperCase() !== "READY" && (
              <p className="text-sm text-yellow-600 mt-2">
                Rapporten behandles fortsatt. Vent til den er klar.
              </p>
            )}

            {report.status.toUpperCase() === "READY" && !report.anonymized_file_path && (
              <p className="text-sm text-orange-600 mt-2">
                Rapporten må anonymiseres før evaluering.{" "}
                <button
                  onClick={() => router.push(`/reports/${reportId}/anonymize`)}
                  className="underline hover:no-underline"
                >
                  Anonymiser nå
                </button>
              </p>
            )}
          </div>
        </div>

        {/* Right column: Results */}
        <div className="lg:col-span-2">
          {/* Streaming view - shows during evaluation */}
          {evaluating && (
            <div className="bg-white rounded-lg shadow-sm border p-6 mb-6">
              <div className="flex items-center gap-3 mb-6">
                <Loader2 className="w-6 h-6 text-blue-600 animate-spin" />
                <div>
                  <h2 className="text-lg font-semibold text-gray-900">Evaluerer rapport...</h2>
                  <p className="text-sm text-gray-500">
                    {streamingAgents.size > 0
                      ? `${Array.from(streamingAgents.values()).filter(a => a.status === "completed").length} av ${streamingAgents.size} agenter fullført`
                      : "Starter opp..."}
                  </p>
                </div>
              </div>

              {/* Agent list with status */}
              <div className="space-y-3">
                {streamingAgents.size === 0 ? (
                  /* Initial loading - show all agents as pending */
                  agents.map((agent) => (
                    <div
                      key={agent.id}
                      className="flex items-center gap-4 p-4 rounded-lg border bg-gray-50 border-gray-200 animate-pulse"
                    >
                      <Clock className="w-6 h-6 text-gray-400" />
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-gray-900">{agent.name}</p>
                        <p className="text-sm text-gray-600 truncate">{agent.description}</p>
                      </div>
                    </div>
                  ))
                ) : (
                  Array.from(streamingAgents.values()).map((agent) => (
                  <div
                    key={agent.id}
                    className={`flex items-center gap-4 p-4 rounded-lg border transition-all ${
                      agent.status === "completed"
                        ? "bg-green-50 border-green-200"
                        : agent.status === "running"
                          ? "bg-blue-50 border-blue-200"
                          : agent.status === "error"
                            ? "bg-red-50 border-red-200"
                            : "bg-gray-50 border-gray-200"
                    }`}
                  >
                    {/* Status icon */}
                    <div className="flex-shrink-0">
                      {agent.status === "completed" ? (
                        <CheckCircle className="w-6 h-6 text-green-600" />
                      ) : agent.status === "running" ? (
                        <Loader2 className="w-6 h-6 text-blue-600 animate-spin" />
                      ) : agent.status === "error" ? (
                        <XCircle className="w-6 h-6 text-red-600" />
                      ) : (
                        <Clock className="w-6 h-6 text-gray-400" />
                      )}
                    </div>

                    {/* Agent info */}
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-gray-900">{agent.name}</p>
                      <p className="text-sm text-gray-600 truncate">{agent.description}</p>
                    </div>

                    {/* Score (when completed) */}
                    {agent.status === "completed" && agent.score !== undefined && agent.score !== null && (
                      <div className="flex-shrink-0 text-right">
                        <p className="text-lg font-bold text-gray-900">
                          {((agent.score / 100) * agent.max_score).toFixed(1)} / {agent.max_score} p
                        </p>
                      </div>
                    )}
                  </div>
                  ))
                )}
              </div>

              {/* Progress bar */}
              <div className="mt-6">
                <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-green-500 transition-all duration-300"
                    style={{
                      width: `${streamingAgents.size > 0
                        ? (Array.from(streamingAgents.values()).filter(a => a.status === "completed").length / streamingAgents.size) * 100
                        : 0}%`
                    }}
                  />
                </div>
              </div>
            </div>
          )}

          {evaluation ? (
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold">Evalueringsresultater</h2>
                <div className="flex items-center gap-2">
                  {getStatusIcon(evaluation.status)}
                  <span className="text-sm text-gray-600">
                    {evaluation.status.toUpperCase() === "COMPLETED"
                      ? "Fullført"
                      : evaluation.status.toUpperCase() === "RUNNING"
                        ? "Kjører..."
                        : evaluation.status}
                  </span>
                </div>
              </div>

              {/* Total score */}
              {evaluation.total_score !== null && (
                <div className={`rounded-lg p-4 mb-6 ${evaluation.instructor_total_score !== null ? "grid grid-cols-2 gap-4" : "bg-gray-50"}`}>
                  {/* AI score */}
                  <div className={evaluation.instructor_total_score !== null ? "bg-blue-50 rounded-lg p-3" : ""}>
                    <p className="text-sm text-gray-600 mb-1">
                      {evaluation.instructor_total_score !== null ? "AI-score" : "Total score"}
                    </p>
                    <p className="text-3xl font-bold text-gray-900">
                      {evaluation.max_possible_score ? ((evaluation.total_score / evaluation.max_possible_score) * 100).toFixed(1) : evaluation.total_score.toFixed(1)} %
                    </p>
                    {evaluation.max_possible_score && (
                      <div className="mt-2 h-2 bg-gray-200 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-blue-600 rounded-full"
                          style={{
                            width: `${(evaluation.total_score / evaluation.max_possible_score) * 100}%`,
                          }}
                        />
                      </div>
                    )}
                  </div>

                  {/* Instructor score */}
                  {evaluation.instructor_total_score !== null && evaluation.max_possible_score && (
                    <div className="bg-orange-50 rounded-lg p-3">
                      <p className="text-sm text-orange-700 mb-1">Instruktørscore</p>
                      <p className="text-3xl font-bold text-gray-900">
                        {((evaluation.instructor_total_score / evaluation.max_possible_score) * 100).toFixed(1)} %
                      </p>
                      <div className="mt-2 h-2 bg-gray-200 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-orange-500 rounded-full"
                          style={{
                            width: `${(evaluation.instructor_total_score / evaluation.max_possible_score) * 100}%`,
                          }}
                        />
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Agent results */}
              <div className="space-y-4">
                {evaluation.agent_results.map((result) => (
                  <div key={result.id} className="border rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="font-medium text-gray-900">
                        {result.agent_name}
                      </h3>
                      <div className="flex items-center gap-2">
                        {getStatusIcon(result.status)}
                        {result.score !== null && result.max_score !== null && (
                          <div className="text-right">
                            <span className="font-semibold text-blue-700">
                              {((result.score / 100) * result.max_score).toFixed(1)} / {result.max_score} p
                            </span>
                            {result.instructor_score !== null && (
                              <span className="ml-2 font-semibold text-orange-600">
                                → {((result.instructor_score / 100) * result.max_score).toFixed(1)} p
                              </span>
                            )}
                          </div>
                        )}
                        {result.status.toUpperCase() === "COMPLETED" && editingResultId !== result.id && (
                          <button
                            onClick={() => startEditing(result)}
                            className="ml-1 p-1 text-gray-400 hover:text-gray-700 rounded"
                            title="Korriger score"
                          >
                            <Pencil className="w-4 h-4" />
                          </button>
                        )}
                      </div>
                    </div>

                    {result.feedback && (
                      <p className="text-gray-600 text-sm mb-3">{result.feedback}</p>
                    )}

                    {/* Instructor comment display */}
                    {result.instructor_comment && editingResultId !== result.id && (
                      <div className="mb-3 px-3 py-2 bg-orange-50 border border-orange-200 rounded text-sm text-orange-800">
                        <span className="font-medium">Instruktørkommentar: </span>
                        {result.instructor_comment}
                      </div>
                    )}

                    {/* Inline edit form */}
                    {editingResultId === result.id && (
                      <div className="mb-4 p-3 bg-orange-50 border border-orange-200 rounded-lg space-y-3">
                        <p className="text-sm font-medium text-orange-800">Korriger vurdering</p>
                        <div>
                          <label className="block text-xs text-gray-600 mb-1">
                            Score (0–100, tom = fjern overstyring)
                          </label>
                          <input
                            type="number"
                            min={0}
                            max={100}
                            step={1}
                            value={editScore}
                            onChange={(e) => setEditScore(e.target.value)}
                            placeholder={result.score !== null ? `AI: ${result.score.toFixed(0)}` : ""}
                            className="w-32 px-2 py-1 border rounded text-sm focus:outline-none focus:ring-2 focus:ring-orange-400"
                          />
                          {editScore !== "" && result.max_score !== null && !isNaN(parseFloat(editScore)) && (
                            <span className="ml-2 text-xs text-gray-500">
                              = {((parseFloat(editScore) / 100) * result.max_score).toFixed(1)} / {result.max_score} p
                            </span>
                          )}
                        </div>
                        <div>
                          <label className="block text-xs text-gray-600 mb-1">Kommentar (valgfri)</label>
                          <textarea
                            value={editComment}
                            onChange={(e) => setEditComment(e.target.value)}
                            rows={2}
                            className="w-full px-2 py-1 border rounded text-sm focus:outline-none focus:ring-2 focus:ring-orange-400 resize-none"
                            placeholder="Legg til kommentar til studenten..."
                          />
                        </div>
                        <div className="flex gap-2">
                          <button
                            onClick={() => saveOverride(evaluation.id, result.id)}
                            disabled={savingOverride}
                            className="px-3 py-1 bg-orange-500 text-white text-sm rounded hover:bg-orange-600 disabled:opacity-50"
                          >
                            {savingOverride ? "Lagrer..." : "Lagre"}
                          </button>
                          <button
                            onClick={cancelEditing}
                            disabled={savingOverride}
                            className="px-3 py-1 border text-sm rounded hover:bg-gray-50 disabled:opacity-50"
                          >
                            Avbryt
                          </button>
                        </div>
                      </div>
                    )}

                    {result.details && result.details.length > 0 && (
                      <div className="space-y-2">
                        {result.details.map((detail, idx) => {
                          const hasScore = detail.score !== undefined && detail.max_score !== undefined;
                          const isNA = detail.applicable === false;
                          const isPassing = hasScore
                            ? detail.score! >= detail.max_score! * 0.5
                            : detail.passed;

                          return (
                            <div
                              key={idx}
                              className="flex items-start gap-2 text-sm"
                            >
                              {isNA ? (
                                <Minus className="w-4 h-4 text-gray-400 mt-0.5 flex-shrink-0" />
                              ) : isPassing ? (
                                <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                              ) : (
                                <XCircle className="w-4 h-4 text-red-500 mt-0.5 flex-shrink-0" />
                              )}
                              <div className="flex-1">
                                <div className="flex items-center gap-2">
                                  <span className={`font-medium ${isNA ? "text-gray-400" : ""}`}>{detail.criterion}</span>
                                  {isNA ? (
                                    <span className="text-xs px-1.5 py-0.5 rounded bg-gray-100 text-gray-400">N/A</span>
                                  ) : hasScore && (
                                    <span className="text-xs px-1.5 py-0.5 rounded bg-gray-100 text-gray-600">
                                      {detail.score} av {detail.max_score}
                                    </span>
                                  )}
                                </div>
                                <span className={`${isNA ? "text-gray-400" : "text-gray-600"}`}>{detail.comment}</span>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    )}

                    {/* Expandable AI dialog section */}
                    {(result.prompt_used || result.raw_response) && (
                      <div className="mt-4 pt-4 border-t">
                        <button
                          onClick={() => toggleResultExpanded(result.id)}
                          className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700"
                        >
                          {expandedResults.has(result.id) ? (
                            <ChevronUp className="w-4 h-4" />
                          ) : (
                            <ChevronDown className="w-4 h-4" />
                          )}
                          Se AI-dialog
                        </button>

                        {expandedResults.has(result.id) && (
                          <div className="mt-3 space-y-3">
                            {result.prompt_used && (
                              <div>
                                <p className="text-xs font-medium text-gray-500 mb-1">Prompt:</p>
                                <pre className="bg-gray-50 rounded p-3 text-xs text-gray-700 max-h-48 overflow-auto whitespace-pre-wrap font-mono">
                                  {result.prompt_used}
                                </pre>
                              </div>
                            )}
                            {result.raw_response && (
                              <div>
                                <p className="text-xs font-medium text-gray-500 mb-1">AI-respons:</p>
                                <pre className="bg-gray-900 text-green-400 rounded p-3 text-xs max-h-48 overflow-auto whitespace-pre-wrap font-mono">
                                  {result.raw_response}
                                </pre>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="bg-white rounded-lg shadow-sm border p-8 text-center">
              <p className="text-gray-600">
                Velg agenter og klikk "Start evaluering" for å evaluere rapporten.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
