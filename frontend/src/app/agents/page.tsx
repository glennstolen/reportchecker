"use client";

import { useEffect, useState } from "react";
import { Settings, Plus, Trash2, Copy } from "lucide-react";

interface Agent {
  id: number;
  name: string;
  description: string | null;
  max_score: number;
  is_template: boolean;
  created_at: string;
}

export default function AgentsPage() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);

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

  const deleteAgent = async (id: number) => {
    if (!confirm("Er du sikker på at du vil slette denne agenten?")) return;

    try {
      await fetch(`http://localhost:8000/api/agents/${id}`, {
        method: "DELETE",
      });
      setAgents(agents.filter((a) => a.id !== id));
    } catch (error) {
      console.error("Failed to delete agent:", error);
    }
  };

  const duplicateAgent = async (agent: Agent) => {
    try {
      const response = await fetch(`http://localhost:8000/api/agents/${agent.id}`);
      const fullAgent = await response.json();

      const newAgent = {
        name: `${fullAgent.name} (kopi)`,
        description: fullAgent.description,
        criteria: fullAgent.criteria,
        max_score: fullAgent.max_score,
        prompt_template: fullAgent.prompt_template,
      };

      const createResponse = await fetch("http://localhost:8000/api/agents", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(newAgent),
      });

      const created = await createResponse.json();
      setAgents([created, ...agents]);
    } catch (error) {
      console.error("Failed to duplicate agent:", error);
    }
  };

  const templates = agents.filter((a) => a.is_template);
  const customAgents = agents.filter((a) => !a.is_template);

  if (loading) {
    return <div className="px-4">Laster...</div>;
  }

  return (
    <div className="px-4">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Agenter</h1>
        <a
          href="/agents/new"
          className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
        >
          <Plus className="w-4 h-4" />
          Ny agent
        </a>
      </div>

      {/* Custom agents */}
      <div className="mb-8">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Mine agenter</h2>
        {customAgents.length === 0 ? (
          <div className="bg-white rounded-lg shadow-sm border p-6 text-center text-gray-600">
            Du har ingen egne agenter ennå. Lag en ny eller dupliser en template.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {customAgents.map((agent) => (
              <AgentCard
                key={agent.id}
                agent={agent}
                onDelete={deleteAgent}
                onDuplicate={duplicateAgent}
              />
            ))}
          </div>
        )}
      </div>

      {/* Templates */}
      <div>
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Templates</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {templates.map((agent) => (
            <AgentCard
              key={agent.id}
              agent={agent}
              onDelete={deleteAgent}
              onDuplicate={duplicateAgent}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

function AgentCard({
  agent,
  onDelete,
  onDuplicate,
}: {
  agent: Agent;
  onDelete: (id: number) => void;
  onDuplicate: (agent: Agent) => void;
}) {
  return (
    <div className="bg-white rounded-lg shadow-sm border p-4">
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2">
          <Settings className="w-5 h-5 text-gray-400" />
          <h3 className="font-medium text-gray-900">{agent.name}</h3>
        </div>
        {agent.is_template && (
          <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded">
            Template
          </span>
        )}
      </div>

      <p className="text-sm text-gray-600 mb-3 line-clamp-2">
        {agent.description || "Ingen beskrivelse"}
      </p>

      <div className="text-sm text-gray-500 mb-4">
        Maks score: {agent.max_score}
      </div>

      <div className="flex gap-2">
        <a
          href={`/agents/${agent.id}`}
          className="flex-1 text-center px-3 py-1.5 border rounded-md text-sm hover:bg-gray-50"
        >
          {agent.is_template ? "Se" : "Rediger"}
        </a>
        <button
          onClick={() => onDuplicate(agent)}
          className="px-3 py-1.5 border rounded-md hover:bg-gray-50"
          title="Dupliser"
        >
          <Copy className="w-4 h-4" />
        </button>
        {!agent.is_template && (
          <button
            onClick={() => onDelete(agent.id)}
            className="px-3 py-1.5 border border-red-200 text-red-600 rounded-md hover:bg-red-50"
            title="Slett"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
  );
}
