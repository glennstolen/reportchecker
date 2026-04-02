"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Play, CheckCircle, XCircle, Clock, AlertCircle, ChevronDown, ChevronUp, Loader2, UserX, Download } from "lucide-react";

interface Report {
  id: number;
  title: string;
  filename: string;
  status: string;
  content_text: string | null;
  created_at: string;
  anonymized_file_path: string | null;
  mapping_file_path: string | null;
}

interface Agent {
  id: number;
  name: string;
  description: string;
  max_score: number;
  default_enabled: boolean;
}

interface CriterionDetail {
  criterion: string;
  comment: string;
  // New format with scores
  score?: number;
  max_score?: number;
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
}

interface Evaluation {
  id: number;
  status: string;
  total_score: number | null;
  max_possible_score: number | null;
  summary: string | null;
  agent_results: AgentResult[];
  created_at: string;
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
  const [selectedAgents, setSelectedAgents] = useState<number[]>([]);
  const [evaluation, setEvaluation] = useState<Evaluation | null>(null);
  const [evaluating, setEvaluating] = useState(false);
  const [loading, setLoading] = useState(true);

  // Streaming state
  const [streamingAgents, setStreamingAgents] = useState<Map<number, StreamingAgent>>(new Map());
  const [expandedResults, setExpandedResults] = useState<Set<number>>(new Set());

  const downloadFile = async (url: string, filename: string) => {
    const response = await fetch(url);
    const blob = await response.blob();
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(link.href);
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
      fetch(`http://localhost:8000/api/reports/${reportId}`).then((r) => r.json()),
      fetch("http://localhost:8000/api/agents").then((r) => r.json()),
      fetch(`http://localhost:8000/api/evaluations/report/${reportId}`).then((r) => r.json()),
    ])
      .then(([reportData, agentsData, evaluationsData]) => {
        setReport(reportData);
        setAgents(agentsData);
        // Pre-select agents that are enabled by default
        setSelectedAgents(agentsData.filter((a: Agent) => a.default_enabled).map((a: Agent) => a.id));
        // Show latest evaluation if exists
        if (evaluationsData.length > 0) {
          setEvaluation(evaluationsData[0]);
        }
      })
      .finally(() => setLoading(false));
  }, [reportId]);

  const toggleAgent = (id: number) => {
    setSelectedAgents((prev) =>
      prev.includes(id) ? prev.filter((a) => a !== id) : [...prev, id]
    );
  };

  const runEvaluation = async () => {
    if (selectedAgents.length === 0) return;

    setEvaluating(true);
    setStreamingAgents(new Map());
    setEvaluation(null);

    try {
      const response = await fetch("http://localhost:8000/api/evaluations/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          report_id: parseInt(reportId),
          agent_config_ids: selectedAgents,
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
                    const evalResponse = await fetch(
                      `http://localhost:8000/api/evaluations/${evaluationId}`
                    );
                    const evalData = await evalResponse.json();
                    setEvaluation(evalData);
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
            <p className="text-gray-600">
              {report.filename} - {new Date(report.created_at).toLocaleDateString("no-NO")}
            </p>
          </div>
          <div className="flex gap-2">
            {report.anonymized_file_path ? (
              <>
                <button
                  onClick={() => downloadFile(
                    `http://localhost:8000/api/reports/${reportId}/anonymized-pdf`,
                    `${report.title.replace(/\s+/g, "_")}_anonym.pdf`
                  )}
                  className="flex items-center gap-2 px-3 py-2 border rounded-md hover:bg-gray-50 text-sm"
                >
                  <Download className="w-4 h-4" />
                  Anonym PDF
                </button>
                <button
                  onClick={() => downloadFile(
                    `http://localhost:8000/api/reports/${reportId}/mapping-file`,
                    `kandidatmapping_${report.title.replace(/\s+/g, "_")}.txt`
                  )}
                  className="flex items-center gap-2 px-3 py-2 border rounded-md hover:bg-gray-50 text-sm"
                >
                  <Download className="w-4 h-4" />
                  Mapping
                </button>
              </>
            ) : (
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
        {report.anonymized_file_path && (
          <div className="mt-2 inline-flex items-center gap-2 px-2 py-1 bg-green-100 text-green-700 rounded text-sm">
            <CheckCircle className="w-4 h-4" />
            Anonymisert
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left column: Agent selection */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-lg shadow-sm border p-4">
            <h2 className="text-lg font-semibold mb-4">Velg agenter</h2>

            <div className="space-y-2">
              {agents.map((agent) => (
                <label
                  key={agent.id}
                  className="flex items-start gap-3 p-3 rounded-md hover:bg-gray-50 cursor-pointer"
                >
                  <input
                    type="checkbox"
                    checked={selectedAgents.includes(agent.id)}
                    onChange={() => toggleAgent(agent.id)}
                    className="mt-1"
                  />
                  <div>
                    <p className="font-medium text-gray-900">{agent.name}</p>
                    <p className="text-sm text-gray-600">{agent.description}</p>
                  </div>
                </label>
              ))}
            </div>

            <button
              onClick={runEvaluation}
              disabled={selectedAgents.length === 0 || evaluating || report.status.toUpperCase() !== "READY" || !report.anonymized_file_path}
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
                  /* Initial loading - show selected agents as pending */
                  selectedAgents.map((agentId) => {
                    const agentInfo = agents.find((a) => a.id === agentId);
                    return (
                      <div
                        key={agentId}
                        className="flex items-center gap-4 p-4 rounded-lg border bg-gray-50 border-gray-200 animate-pulse"
                      >
                        <Clock className="w-6 h-6 text-gray-400" />
                        <div className="flex-1 min-w-0">
                          <p className="font-medium text-gray-900">{agentInfo?.name}</p>
                          <p className="text-sm text-gray-600 truncate">{agentInfo?.description}</p>
                        </div>
                      </div>
                    );
                  })
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
                    {agent.status === "completed" && agent.score !== undefined && (
                      <div className="flex-shrink-0 text-right">
                        <p className="text-lg font-bold text-gray-900">
                          {agent.score?.toFixed(1)} / {agent.max_score}
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
                <div className="bg-gray-50 rounded-lg p-4 mb-6">
                  <p className="text-sm text-gray-600 mb-1">Total score</p>
                  <p className="text-3xl font-bold text-gray-900">
                    {evaluation.total_score.toFixed(1)} / {evaluation.max_possible_score?.toFixed(1)}
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
                        {result.score !== null && (
                          <span className="font-semibold">
                            {result.score.toFixed(1)} / {result.max_score?.toFixed(1)}
                          </span>
                        )}
                      </div>
                    </div>

                    {result.feedback && (
                      <p className="text-gray-600 text-sm mb-3">{result.feedback}</p>
                    )}

                    {result.details && result.details.length > 0 && (
                      <div className="space-y-2">
                        {result.details.map((detail, idx) => {
                          // Check if we have score-based format or legacy passed format
                          const hasScore = detail.score !== undefined && detail.max_score !== undefined;
                          const isPassing = hasScore
                            ? detail.score! >= detail.max_score! * 0.5
                            : detail.passed;

                          return (
                            <div
                              key={idx}
                              className="flex items-start gap-2 text-sm"
                            >
                              {isPassing ? (
                                <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                              ) : (
                                <XCircle className="w-4 h-4 text-red-500 mt-0.5 flex-shrink-0" />
                              )}
                              <div className="flex-1">
                                <div className="flex items-center gap-2">
                                  <span className="font-medium">{detail.criterion}</span>
                                  {hasScore && (
                                    <span className="text-xs px-1.5 py-0.5 rounded bg-gray-100 text-gray-600">
                                      {detail.score} av {detail.max_score}
                                    </span>
                                  )}
                                </div>
                                <span className="text-gray-600">{detail.comment}</span>
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
