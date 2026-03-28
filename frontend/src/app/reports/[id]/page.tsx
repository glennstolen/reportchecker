"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Play, CheckCircle, XCircle, Clock, AlertCircle } from "lucide-react";

interface Report {
  id: number;
  title: string;
  filename: string;
  status: string;
  content_text: string | null;
  created_at: string;
}

interface Agent {
  id: number;
  name: string;
  description: string;
  max_score: number;
  is_template: boolean;
}

interface AgentResult {
  id: number;
  agent_config_id: number;
  agent_name: string;
  score: number | null;
  max_score: number | null;
  feedback: string | null;
  details: Array<{ criterion: string; passed: boolean; comment: string }> | null;
  status: string;
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

export default function ReportDetailPage() {
  const params = useParams();
  const reportId = params.id as string;

  const [report, setReport] = useState<Report | null>(null);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [selectedAgents, setSelectedAgents] = useState<number[]>([]);
  const [evaluation, setEvaluation] = useState<Evaluation | null>(null);
  const [evaluating, setEvaluating] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetch(`http://localhost:8000/api/reports/${reportId}`).then((r) => r.json()),
      fetch("http://localhost:8000/api/agents").then((r) => r.json()),
      fetch(`http://localhost:8000/api/evaluations/report/${reportId}`).then((r) => r.json()),
    ])
      .then(([reportData, agentsData, evaluationsData]) => {
        setReport(reportData);
        setAgents(agentsData);
        // Pre-select template agents
        setSelectedAgents(agentsData.filter((a: Agent) => a.is_template).map((a: Agent) => a.id));
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
    try {
      const response = await fetch("http://localhost:8000/api/evaluations", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          report_id: parseInt(reportId),
          agent_config_ids: selectedAgents,
        }),
      });
      const data = await response.json();
      setEvaluation(data);
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
        <h1 className="text-2xl font-bold text-gray-900">{report.title}</h1>
        <p className="text-gray-600">
          {report.filename} - {new Date(report.created_at).toLocaleDateString("no-NO")}
        </p>
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
                    {agent.is_template && (
                      <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded mt-1 inline-block">
                        Template
                      </span>
                    )}
                  </div>
                </label>
              ))}
            </div>

            <button
              onClick={runEvaluation}
              disabled={selectedAgents.length === 0 || evaluating || report.status.toUpperCase() !== "READY"}
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
          </div>
        </div>

        {/* Right column: Results */}
        <div className="lg:col-span-2">
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
                        {result.details.map((detail, idx) => (
                          <div
                            key={idx}
                            className="flex items-start gap-2 text-sm"
                          >
                            {detail.passed ? (
                              <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                            ) : (
                              <XCircle className="w-4 h-4 text-red-500 mt-0.5 flex-shrink-0" />
                            )}
                            <div>
                              <span className="font-medium">{detail.criterion}:</span>{" "}
                              <span className="text-gray-600">{detail.comment}</span>
                            </div>
                          </div>
                        ))}
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
