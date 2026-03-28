"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Plus, Trash2 } from "lucide-react";

interface Criterion {
  id: string;
  label: string;
  weight: number;
  description: string;
}

export default function NewAgentPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [maxScore, setMaxScore] = useState(10);
  const [criteria, setCriteria] = useState<Criterion[]>([
    { id: "criterion_1", label: "", weight: 1.0, description: "" },
  ]);
  const [scoringRubric, setScoringRubric] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!name.trim()) {
      setError("Navn er påkrevd");
      return;
    }

    setSaving(true);
    setError("");

    try {
      const response = await fetch("http://localhost:8000/api/agents", {
        method: "POST",
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
        throw new Error("Failed to create agent");
      }

      router.push("/agents");
    } catch {
      setError("Kunne ikke opprette agent");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="px-4 max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Ny agent</h1>

      <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow-sm border p-6">
        {/* Basic info */}
        <div className="space-y-4 mb-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Navn *
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="F.eks. Metodesjekker"
              className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Beskrivelse
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Hva sjekker denne agenten?"
              rows={2}
              className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
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
              min={1}
              max={100}
              className="w-32 px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        {/* Criteria */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-3">
            <label className="text-sm font-medium text-gray-700">
              Evalueringskriterier
            </label>
            <button
              type="button"
              onClick={addCriterion}
              className="flex items-center gap-1 text-sm text-blue-600 hover:text-blue-800"
            >
              <Plus className="w-4 h-4" />
              Legg til
            </button>
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
                      placeholder="Kriterienavn, f.eks. 'Metodebeskrivelse er komplett'"
                      className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                    <div className="flex gap-4">
                      <div className="flex-1">
                        <input
                          type="text"
                          value={criterion.description}
                          onChange={(e) => updateCriterion(index, "description", e.target.value)}
                          placeholder="Beskrivelse (valgfritt)"
                          className="w-full px-3 py-2 border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                      </div>
                      <div className="w-24">
                        <input
                          type="number"
                          value={criterion.weight}
                          onChange={(e) => updateCriterion(index, "weight", parseFloat(e.target.value))}
                          step={0.5}
                          min={0.5}
                          max={5}
                          placeholder="Vekt"
                          className="w-full px-3 py-2 border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                      </div>
                    </div>
                  </div>
                  {criteria.length > 1 && (
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
            Vurderingsmal (valgfritt)
          </label>
          <textarea
            value={scoringRubric}
            onChange={(e) => setScoringRubric(e.target.value)}
            placeholder="Instruksjoner for hvordan AI skal vurdere, f.eks. 'Fullt poeng krever at alle kriterier er oppfylt'"
            rows={3}
            className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
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
            Avbryt
          </button>
          <button
            type="submit"
            disabled={saving}
            className="flex-1 bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50"
          >
            {saving ? "Lagrer..." : "Opprett agent"}
          </button>
        </div>
      </form>
    </div>
  );
}
