"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import {
  Settings,
  ChevronDown,
  ChevronUp,
  CheckCircle,
  Pencil,
  X,
  Plus,
  Download,
} from "lucide-react";

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
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editDraft, setEditDraft] = useState<Agent | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchAgents();
  }, []);

  const fetchAgents = async () => {
    try {
      const response = await apiFetch("/api/agents");
      const data = await response.json();
      setAgents(data);
    } catch (error) {
      console.error("Failed to fetch agents:", error);
    } finally {
      setLoading(false);
    }
  };

  const toggleExpanded = (id: number) => {
    if (editingId === id) return; // don't collapse while editing
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

  const startEdit = (agent: Agent) => {
    setEditingId(agent.id);
    setEditDraft(JSON.parse(JSON.stringify(agent))); // deep copy
    setExpandedAgents((prev) => new Set(prev).add(agent.id));
  };

  const cancelEdit = () => {
    setEditingId(null);
    setEditDraft(null);
  };

  const saveEdit = async () => {
    if (!editDraft) return;
    setSaving(true);
    try {
      const res = await apiFetch(
        `/api/agents/${editDraft.id}`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            name: editDraft.name,
            description: editDraft.description,
            max_score: editDraft.max_score,
            criteria: editDraft.criteria,
          }),
        }
      );
      if (!res.ok) throw new Error("Lagring feilet");
      await fetchAgents();
      setEditingId(null);
      setEditDraft(null);
    } catch (error) {
      console.error("Failed to save agent:", error);
      alert("Kunne ikke lagre endringene. Prøv igjen.");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <div className="px-4">Laster...</div>;
  }

  const totalMaxScore = agents.reduce((sum, a) => sum + a.max_score, 0);

  const exportCriteriaPdf = async () => {
    try {
      const response = await apiFetch("/api/agents/export-criteria-pdf");
      if (!response.ok) return;
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "vurderingskriterier.pdf";
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      a.remove();
    } catch (error) {
      console.error("Failed to export criteria PDF:", error);
    }
  };

  return (
    <div className="px-4">
      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Vurderingsagenter</h1>
          <p className="text-gray-600 mt-1">
            {agents.length} agenter | Total maks score: {totalMaxScore}
          </p>
        </div>
        <button
          onClick={exportCriteriaPdf}
          className="flex items-center gap-2 px-4 py-2 border rounded-md hover:bg-gray-50 text-sm text-gray-700"
        >
          <Download className="w-4 h-4" />
          Eksporter vurderingskriterier
        </button>
      </div>

      <div className="space-y-4">
        {agents.map((agent) => (
          <AgentCard
            key={agent.id}
            agent={agent}
            expanded={expandedAgents.has(agent.id)}
            onToggle={() => toggleExpanded(agent.id)}
            editing={editingId === agent.id}
            draft={editingId === agent.id ? editDraft : null}
            onDraftChange={setEditDraft}
            onEdit={() => startEdit(agent)}
            onCancel={cancelEdit}
            onSave={saveEdit}
            saving={saving}
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
  editing,
  draft,
  onDraftChange,
  onEdit,
  onCancel,
  onSave,
  saving,
}: {
  agent: Agent;
  expanded: boolean;
  onToggle: () => void;
  editing: boolean;
  draft: Agent | null;
  onDraftChange: (draft: Agent) => void;
  onEdit: () => void;
  onCancel: () => void;
  onSave: () => Promise<void>;
  saving: boolean;
}) {
  const criteria = agent.criteria?.checkItems || [];

  const updateDraftField = (field: keyof Agent, value: unknown) => {
    if (!draft) return;
    onDraftChange({ ...draft, [field]: value });
  };

  const updateDraftCriterion = (
    index: number,
    field: keyof Criterion,
    value: string | number
  ) => {
    if (!draft) return;
    const items = [...draft.criteria.checkItems];
    items[index] = { ...items[index], [field]: value };
    onDraftChange({ ...draft, criteria: { ...draft.criteria, checkItems: items } });
  };

  const addCriterion = () => {
    if (!draft) return;
    const newItem: Criterion = {
      id: `criterion_${Date.now()}`,
      label: "",
      weight: 0,
      description: "",
    };
    onDraftChange({
      ...draft,
      criteria: {
        ...draft.criteria,
        checkItems: [...draft.criteria.checkItems, newItem],
      },
    });
  };

  const removeCriterion = (index: number) => {
    if (!draft) return;
    const items = draft.criteria.checkItems.filter((_, i) => i !== index);
    onDraftChange({ ...draft, criteria: { ...draft.criteria, checkItems: items } });
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border">
      {/* Header */}
      <div className="p-4">
        <div className="flex items-center justify-between">
          <div
            className="flex items-center gap-3 flex-1 cursor-pointer hover:opacity-80"
            onClick={onToggle}
          >
            <Settings className="w-5 h-5 text-blue-600 flex-shrink-0" />
            <div>
              <h3 className="font-medium text-gray-900">{agent.name}</h3>
              <p className="text-sm text-gray-600">
                {agent.description || "Ingen beskrivelse"}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-lg font-semibold text-blue-600">
              {agent.max_score}p
            </span>
            {!editing && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onEdit();
                }}
                className="p-1.5 rounded-md text-gray-400 hover:text-blue-600 hover:bg-blue-50 transition-colors"
                title="Rediger"
              >
                <Pencil className="w-4 h-4" />
              </button>
            )}
            <button onClick={onToggle} className="text-gray-400">
              {expanded ? (
                <ChevronUp className="w-5 h-5" />
              ) : (
                <ChevronDown className="w-5 h-5" />
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Expanded: read-only */}
      {expanded && !editing && (
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

      {/* Expanded: edit form */}
      {expanded && editing && draft && (
        <div className="border-t px-4 py-4 bg-gray-50">
          <div className="space-y-4">
            {/* Name */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Navn
              </label>
              <input
                type="text"
                value={draft.name}
                onChange={(e) => updateDraftField("name", e.target.value)}
                className="w-full border rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* Description */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Beskrivelse
              </label>
              <textarea
                value={draft.description || ""}
                onChange={(e) => updateDraftField("description", e.target.value)}
                rows={2}
                className="w-full border rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* Max score */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Maks score (poeng)
              </label>
              <input
                type="number"
                min="0"
                step="0.5"
                value={draft.max_score}
                onChange={(e) =>
                  updateDraftField("max_score", parseFloat(e.target.value) || 0)
                }
                className="w-32 border rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* Check items */}
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-2">
                Kriterier
              </h4>
              <div className="space-y-2">
                {draft.criteria.checkItems.map((item, index) => (
                  <div
                    key={item.id}
                    className="bg-white border rounded-md p-3 space-y-2"
                  >
                    <div className="flex gap-2 items-start">
                      <div className="flex-1">
                        <input
                          type="text"
                          placeholder="Label"
                          value={item.label}
                          onChange={(e) =>
                            updateDraftCriterion(index, "label", e.target.value)
                          }
                          className="w-full border rounded px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                      </div>
                      <div className="w-20">
                        <input
                          type="number"
                          placeholder="Vekt"
                          value={item.weight}
                          onChange={(e) =>
                            updateDraftCriterion(
                              index,
                              "weight",
                              parseInt(e.target.value) || 0
                            )
                          }
                          className="w-full border rounded px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                      </div>
                      <button
                        onClick={() => removeCriterion(index)}
                        className="p-1 text-red-400 hover:text-red-600"
                        title="Fjern kriterie"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                    <textarea
                      placeholder="Beskrivelse"
                      value={item.description || ""}
                      onChange={(e) =>
                        updateDraftCriterion(index, "description", e.target.value)
                      }
                      rows={2}
                      className="w-full border rounded px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                ))}
              </div>
              <button
                onClick={addCriterion}
                className="mt-2 flex items-center gap-1 text-sm text-blue-600 hover:text-blue-800"
              >
                <Plus className="w-4 h-4" />
                Legg til kriterie
              </button>
            </div>

            {/* Scoring rubric */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Vurderingsmal (scoring rubric)
              </label>
              <textarea
                value={draft.criteria.scoringRubric || ""}
                onChange={(e) =>
                  onDraftChange({
                    ...draft,
                    criteria: {
                      ...draft.criteria,
                      scoringRubric: e.target.value,
                    },
                  })
                }
                rows={5}
                className="w-full border rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* Actions */}
            <div className="flex gap-2 pt-2">
              <button
                onClick={onSave}
                disabled={saving}
                className="px-4 py-2 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700 disabled:opacity-50"
              >
                {saving ? "Lagrer..." : "Lagre"}
              </button>
              <button
                onClick={onCancel}
                disabled={saving}
                className="px-4 py-2 bg-white text-gray-700 text-sm border rounded-md hover:bg-gray-50 disabled:opacity-50"
              >
                Avbryt
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
