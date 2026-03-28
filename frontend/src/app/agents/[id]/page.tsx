"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Plus, Trash2, Save } from "lucide-react";

interface Criterion {
  id: string;
  label: string;
  weight: number;
  description: string;
}

interface Agent {
  id: number;
  name: string;
  description: string | null;
  criteria: {
    checkItems: Criterion[];
    scoringRubric?: string;
  };
  max_score: number;
  prompt_template: string | null;
  is_template: boolean;
}

export default function AgentDetailPage() {
  const params = useParams();
  const router = useRouter();
  const agentId = params.id as string;

  const [agent, setAgent] = useState<Agent | null>(null);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [maxScore, setMaxScore] = useState(10);
  const [criteria, setCriteria] = useState<Criterion[]>([]);
  const [scoringRubric, setScoringRubric] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch(`http://localhost:8000/api/agents/${agentId}`)
      .then((r) => r.json())
      .then((data) => {
        setAgent(data);
        setName(data.name);
        setDescription(data.description || "");
        setMaxScore(data.max_score);
        setCriteria(data.criteria?.checkItems || []);
        setScoringRubric(data.criteria?.scoringRubric || "");
      })
      .finally(() => setLoading(false));
  }, [agentId]);

  const addCriterion = () => {
    setCriteria([
      ...criteria,
      {
        id: `criterion_${Date.now()}`,
        label: "",
        weight: 1.0,
        description: "",
      },
    ]);
  };

  const removeCriterion = (index: number) => {
    setCriteria(criteria.filter((_, i) => i !== index));
  };

  const updateCriterion = (index: number, field: keyof Criterion, value: string | number) => {
    const updated = [...criteria];
    updated[index] = { ...updated[index], [field]: value };
    setCriteria(updated);
  };

  const handleSave = async () => {
    if (!name.trim()) {
      setError("Navn er påkrevd");
      return;
    }

    setSaving(true);
    setError("");

    try {
      const response = await fetch(`http://localhost:8000/api/agents/${agentId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name,
          description,
          max_score: maxScore,
          criteria: {
            checkItems: criteria.filter((c) => c.label.trim()),
            scoringRubric: scoringRubric || undefined,
          },
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to update agent");
      }

      router.push("/agents");
    } catch {
      setError("Kunne ikke lagre endringer");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <div className="px-4">Laster...</div>;
  }

  if (!agent) {
    return <div className="px-4">Agent ikke funnet</div>;
  }

  const isReadOnly = agent.is_template;

  return (
    <div className="px-4 max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">
        {isReadOnly ? agent.name : "Rediger agent"}
      </h1>

      <div className="bg-white rounded-lg shadow-sm border p-6">
        {isReadOnly && (
          <div className="mb-4 p-3 bg-blue-50 text-blue-700 rounded-md text-sm">
            Dette er en template og kan ikke redigeres. Dupliser den for å lage din egen versjon.
          </div>
        )}

        {/* Basic info */}
        <div className="space-y-4 mb-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Navn
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              disabled={isReadOnly}
              className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Beskrivelse
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              disabled={isReadOnly}
              rows={2}
              className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Maks score
            </label>
            <input
              type="number"
              value={maxScore}
              onChange={(e) => setMaxScore(parseFloat(e.target.value))}
              disabled={isReadOnly}
              className="w-32 px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50"
            />
          </div>
        </div>

        {/* Criteria */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-3">
            <label className="text-sm font-medium text-gray-700">
              Evalueringskriterier
            </label>
            {!isReadOnly && (
              <button
                type="button"
                onClick={addCriterion}
                className="flex items-center gap-1 text-sm text-blue-600 hover:text-blue-800"
              >
                <Plus className="w-4 h-4" />
                Legg til
              </button>
            )}
          </div>

          <div className="space-y-4">
            {criteria.map((criterion, index) => (
              <div key={criterion.id} className="border rounded-lg p-4">
                <div className="flex items-start gap-4">
                  <div className="flex-1 space-y-3">
                    <input
                      type="text"
                      value={criterion.label}
                      onChange={(e) => updateCriterion(index, "label", e.target.value)}
                      disabled={isReadOnly}
                      className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50"
                    />
                    <div className="flex gap-4">
                      <div className="flex-1">
                        <input
                          type="text"
                          value={criterion.description}
                          onChange={(e) => updateCriterion(index, "description", e.target.value)}
                          disabled={isReadOnly}
                          placeholder="Beskrivelse"
                          className="w-full px-3 py-2 border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50"
                        />
                      </div>
                      <div className="w-24">
                        <input
                          type="number"
                          value={criterion.weight}
                          onChange={(e) => updateCriterion(index, "weight", parseFloat(e.target.value))}
                          disabled={isReadOnly}
                          step={0.5}
                          className="w-full px-3 py-2 border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50"
                        />
                      </div>
                    </div>
                  </div>
                  {!isReadOnly && criteria.length > 1 && (
                    <button
                      type="button"
                      onClick={() => removeCriterion(index)}
                      className="p-2 text-red-500 hover:bg-red-50 rounded"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Scoring rubric */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Vurderingsmal
          </label>
          <textarea
            value={scoringRubric}
            onChange={(e) => setScoringRubric(e.target.value)}
            disabled={isReadOnly}
            rows={3}
            className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50"
          />
        </div>

        {/* Error */}
        {error && (
          <div className="mb-4 p-3 bg-red-50 text-red-700 rounded-md text-sm">
            {error}
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-4">
          <button
            type="button"
            onClick={() => router.back()}
            className="px-4 py-2 border rounded-md hover:bg-gray-50"
          >
            Tilbake
          </button>
          {!isReadOnly && (
            <button
              onClick={handleSave}
              disabled={saving}
              className="flex-1 flex items-center justify-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              <Save className="w-4 h-4" />
              {saving ? "Lagrer..." : "Lagre endringer"}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
