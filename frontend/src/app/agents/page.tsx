"use client";

import { useEffect, useState } from "react";
import { Settings, ChevronDown, ChevronUp, CheckCircle } from "lucide-react";

interface Criterion {
  id: string;
  label: string;
  weight: number;
  description?: string;
}

interface Agent {
  id: number;
  name: string;
  description: string | null;
  max_score: number;
  criteria: {
    checkItems: Criterion[];
    scoringRubric?: string;
  };
  created_at: string;
}

export default function AgentsPage() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedAgents, setExpandedAgents] = useState<Set<number>>(new Set());

  useEffect(() => {
    fetchAgents();
  }, []);

  const fetchAgents = async () => {
    try {
      const response = await fetch("http://localhost:8000/api/agents");
      const data = await response.json();
      setAgents(data);
    } catch (error) {
      console.error("Failed to fetch agents:", error);
    } finally {
      setLoading(false);
    }
  };

  const toggleExpanded = (id: number) => {
    setExpandedAgents((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  if (loading) {
    return <div className="px-4">Laster...</div>;
  }

  // Calculate total max score
  const totalMaxScore = agents.reduce((sum, a) => sum + a.max_score, 0);

  return (
    <div className="px-4">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Vurderingsagenter</h1>
        <p className="text-gray-600 mt-1">
          {agents.length} agenter | Total maks score: {totalMaxScore}
        </p>
      </div>

      <div className="space-y-4">
        {agents.map((agent) => (
          <AgentCard
            key={agent.id}
            agent={agent}
            expanded={expandedAgents.has(agent.id)}
            onToggle={() => toggleExpanded(agent.id)}
          />
        ))}
      </div>
    </div>
  );
}

function AgentCard({
  agent,
  expanded,
  onToggle,
}: {
  agent: Agent;
  expanded: boolean;
  onToggle: () => void;
}) {
  const criteria = agent.criteria?.checkItems || [];
  const totalWeight = criteria.reduce((sum, c) => sum + c.weight, 0);

  return (
    <div className="bg-white rounded-lg shadow-sm border">
      {/* Header - always visible */}
      <div
        className="p-4 cursor-pointer hover:bg-gray-50"
        onClick={onToggle}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Settings className="w-5 h-5 text-blue-600" />
            <div>
              <h3 className="font-medium text-gray-900">{agent.name}</h3>
              <p className="text-sm text-gray-600">
                {agent.description || "Ingen beskrivelse"}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-lg font-semibold text-blue-600">
              {agent.max_score}p
            </span>
            {expanded ? (
              <ChevronUp className="w-5 h-5 text-gray-400" />
            ) : (
              <ChevronDown className="w-5 h-5 text-gray-400" />
            )}
          </div>
        </div>
      </div>

      {/* Expanded criteria section */}
      {expanded && (
        <div className="border-t px-4 py-4 bg-gray-50">
          <h4 className="text-sm font-medium text-gray-700 mb-3">
            Kriterier ({criteria.length} sjekker)
          </h4>

          <div className="space-y-2">
            {criteria.map((criterion) => (
              <div
                key={criterion.id}
                className="flex items-start gap-3 bg-white rounded-md p-3 border"
              >
                <CheckCircle className="w-4 h-4 text-gray-400 mt-0.5 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-medium text-gray-900 text-sm">
                      {criterion.label}
                    </span>
                    <span className="text-xs text-gray-500 flex-shrink-0">
                      vekt: {criterion.weight}
                    </span>
                  </div>
                  {criterion.description && (
                    <p className="text-sm text-gray-600 mt-1">
                      {criterion.description}
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>

          {agent.criteria?.scoringRubric && (
            <div className="mt-4 p-3 bg-blue-50 rounded-md">
              <p className="text-sm text-blue-800">
                <span className="font-medium">Vurderingsmal: </span>
                {agent.criteria.scoringRubric}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
