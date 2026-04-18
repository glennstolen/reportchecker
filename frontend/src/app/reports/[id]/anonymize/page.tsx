"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";
import { ArrowLeft, UserX, Plus, Trash2, Download, Check, Loader2, AlertCircle } from "lucide-react";

interface MappingRow {
  candidate_number: string;
  name: string;
  initials: string;
}

interface ExtractedInfo {
  authors: Array<{ name: string; initials: string; candidate_number: string }>;
  medforfatterbidrag: Record<string, string[]>;
  ki_brukt: boolean;
  total_pages: number;
  suggested_pages_to_remove: number[];
  title: string;
  oppgave: string | null;
  dato: string | null;
}

interface AuthorMappingResult {
  name: string;
  initials: string;
  candidate_number: string;
}

function generateCandidateNumber(): string {
  return String(Math.floor(100000 + Math.random() * 900000));
}

export default function AnonymizePage() {
  const params = useParams();
  const router = useRouter();
  const reportId = params.id as string;

  const [loading, setLoading] = useState(true);
  const [anonymizing, setAnonymizing] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [title, setTitle] = useState("");
  const [dato, setDato] = useState("");
  const [oppgave, setOppgave] = useState("");
  const [mappings, setMappings] = useState<MappingRow[]>([]);
  const [medforfatterbidrag, setMedforfatterbidrag] = useState<Record<string, string[]>>({});
  const [kiBrukt, setKiBrukt] = useState(false);
  const [totalPages, setTotalPages] = useState(0);
  const [pagesToRemove, setPagesToRemove] = useState<string>("");

  const [resultMappings, setResultMappings] = useState<AuthorMappingResult[]>([]);

  const downloadFile = async (path: string, filename: string) => {
    const response = await apiFetch(path);
    const blob = await response.blob();
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(link.href);
  };

  useEffect(() => {
    const extractInfo = async () => {
      try {
        const response = await apiFetch(`/api/reports/${reportId}/extract-info`);
        if (!response.ok) {
          const err = await response.json();
          throw new Error(err.detail || "Kunne ikke hente rapport-info");
        }
        const data: ExtractedInfo = await response.json();

        setTitle(data.title);
        setDato(data.dato || "");
        setOppgave(data.oppgave || "");
        setMappings(
          data.authors.length > 0
            ? data.authors.map((a) => ({
                candidate_number: a.candidate_number,
                name: a.name,
                initials: a.initials,
              }))
            : [{ candidate_number: generateCandidateNumber(), name: "", initials: "" }]
        );
        setMedforfatterbidrag(data.medforfatterbidrag);
        setKiBrukt(data.ki_brukt);
        setTotalPages(data.total_pages);
        setPagesToRemove(data.suggested_pages_to_remove.join(", "));
      } catch (err) {
        setError(err instanceof Error ? err.message : "Noe gikk galt");
      } finally {
        setLoading(false);
      }
    };

    extractInfo();
  }, [reportId]);

  const addMapping = () => {
    setMappings([...mappings, { candidate_number: generateCandidateNumber(), name: "", initials: "" }]);
  };

  const removeMapping = (index: number) => {
    setMappings(mappings.filter((_, i) => i !== index));
  };

  const updateMapping = (index: number, field: "name" | "initials", value: string) => {
    const updated = [...mappings];
    updated[index][field] = value;
    setMappings(updated);
  };

  const updateMedforfatterbidragInitials = (section: string, value: string) => {
    const initials = value.split(",").map((s) => s.trim()).filter(Boolean);
    setMedforfatterbidrag({ ...medforfatterbidrag, [section]: initials });
  };

  const renameMedforfatterbidragSection = (oldSection: string, newSection: string) => {
    const entries = Object.entries(medforfatterbidrag);
    const updated: Record<string, string[]> = {};
    for (const [k, v] of entries) {
      updated[k === oldSection ? newSection : k] = v;
    }
    setMedforfatterbidrag(updated);
  };

  const addMedforfatterbidragSection = () => {
    const key = `__new_${Date.now()}`;
    setMedforfatterbidrag({ ...medforfatterbidrag, [key]: [] });
  };

  const removeMedforfatterbidragSection = (section: string) => {
    const updated = { ...medforfatterbidrag };
    delete updated[section];
    setMedforfatterbidrag(updated);
  };

  const handleAnonymize = async () => {
    if (mappings.some((m) => !m.name)) {
      alert("Fyll inn navn for alle rader");
      return;
    }

    setAnonymizing(true);
    setError(null);

    const pages = pagesToRemove
      .split(",")
      .map((p) => parseInt(p.trim()) - 1)
      .filter((p) => !isNaN(p) && p >= 0);

    try {
      const response = await apiFetch(`/api/reports/${reportId}/anonymize`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          mappings,
          pages_to_remove: pages,
          medforfatterbidrag: Object.keys(medforfatterbidrag).length > 0 ? medforfatterbidrag : null,
          ki_brukt: kiBrukt,
          title,
          dato,
          oppgave,
        }),
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || "Anonymisering feilet");
      }

      const result = await response.json();
      setResultMappings(result.mappings);
      setDone(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Noe gikk galt");
    } finally {
      setAnonymizing(false);
    }
  };

  if (loading) {
    return (
      <div className="px-4 max-w-3xl mx-auto py-12">
        <div className="flex items-center justify-center gap-3">
          <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
          <span className="text-gray-600">Analyserer rapport...</span>
        </div>
      </div>
    );
  }

  if (error && !done) {
    return (
      <div className="px-4 max-w-3xl mx-auto py-12">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <div className="flex items-center gap-3 text-red-700">
            <AlertCircle className="w-6 h-6" />
            <span>{error}</span>
          </div>
          <button onClick={() => router.back()} className="mt-4 text-blue-600 hover:underline">
            Tilbake
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="px-4 max-w-3xl mx-auto">
      <div className="flex items-center gap-4 mb-6">
        <button onClick={() => router.back()} className="p-2 hover:bg-gray-100 rounded-md">
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Anonymiser rapport</h1>
          <p className="text-gray-600">{title}</p>
        </div>
      </div>

      {done ? (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
              <Check className="w-6 h-6 text-green-600" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-gray-900">Rapport anonymisert!</h2>
              <p className="text-sm text-gray-600">
                Navn og initialer er erstattet med kandidatnumre gjennom hele rapporten.
              </p>
            </div>
          </div>

          <div className="mb-6">
            <h3 className="font-medium text-gray-900 mb-3">Kandidatmapping</h3>
            <table className="w-full border rounded-lg overflow-hidden">
              <thead className="bg-gray-50">
                <tr>
                  <th className="text-left px-4 py-2 text-sm font-medium text-gray-700">Navn</th>
                  <th className="text-left px-4 py-2 text-sm font-medium text-gray-700">Initialer</th>
                  <th className="text-left px-4 py-2 text-sm font-medium text-gray-700">Kandidatnummer</th>
                </tr>
              </thead>
              <tbody>
                {resultMappings.map((m, i) => (
                  <tr key={i} className="border-t">
                    <td className="px-4 py-2 text-sm">{m.name}</td>
                    <td className="px-4 py-2 text-sm">{m.initials}</td>
                    <td className="px-4 py-2 text-sm font-mono font-semibold text-blue-600">
                      {m.candidate_number}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 mb-6">
            <p className="text-sm text-amber-800">
              <strong>Sjekk PDF-en før bruk:</strong> Automatisk ekstraksjon kan misse navn som ikke
              følger standardformat. Last ned PDF-en og søk etter kjente navn for å verifisere at
              alle er erstattet. Hvis noe mangler, last opp rapporten på nytt og legg til navnene manuelt.
            </p>
          </div>

          <div className="flex gap-4">
            <button
              onClick={() => downloadFile(
                `/api/reports/${reportId}/mapping-file`,
                `kandidatmapping_${title.replace(/\s+/g, "_")}.txt`
              )}
              className="flex items-center gap-2 px-4 py-2 border rounded-md hover:bg-gray-50"
            >
              <Download className="w-4 h-4" />
              Last ned mapping-fil
            </button>
            <button
              onClick={() => downloadFile(
                `/api/reports/${reportId}/anonymized-pdf`,
                `${title.replace(/\s+/g, "_")}_anonym.pdf`
              )}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              <Download className="w-4 h-4" />
              Last ned anonymisert PDF
            </button>
          </div>

          <div className="mt-6 pt-6 border-t flex items-center justify-between">
            <button
              onClick={() => router.push(`/reports/${reportId}`)}
              className="text-blue-600 hover:underline"
            >
              Gå til rapport for evaluering
            </button>
            <button
              onClick={() => {
                setMappings(resultMappings.map(m => ({
                  candidate_number: m.candidate_number,
                  name: m.name,
                  initials: m.initials,
                })));
                setDone(false);
              }}
              className="flex items-center gap-2 px-4 py-2 border rounded-md hover:bg-gray-50 text-sm"
            >
              <UserX className="w-4 h-4" />
              Re-anonymiser
            </button>
          </div>
        </div>
      ) : (
        <div className="space-y-6">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <p className="text-sm text-blue-800">
              Navn og initialer er automatisk ekstrahert som forslag — sjekk og korriger om nødvendig.
              Hvert navn og initialer søkes opp og erstattes med kandidatnummeret gjennom hele rapporten.
              Kandidatnumre er faste og endres ikke ved ny opplasting av samme rapport.
            </p>
          </div>

          {/* Title and Date */}
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Tittel og dato
              <span className="text-sm font-normal text-gray-500 ml-2">(ekstrahert fra forside)</span>
            </h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Tittel</label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="w-full px-3 py-2 border rounded-md"
                  placeholder="Rapportens tittel"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Dato</label>
                <input
                  type="text"
                  value={dato}
                  onChange={(e) => setDato(e.target.value)}
                  className="w-full px-3 py-2 border rounded-md"
                  placeholder="DD.MM.YYYY"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Oppgave</label>
                <input
                  type="text"
                  value={oppgave}
                  onChange={(e) => setOppgave(e.target.value)}
                  className="w-full px-3 py-2 border rounded-md"
                  placeholder="f.eks. Labrapport i KJM1001 - Generell kjemi"
                />
              </div>
            </div>
          </div>

          {/* Mapping table */}
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-1">
              Navn og kandidatnumre
            </h2>
            <p className="text-sm text-gray-500 mb-4">
              Navn og initialer søkes opp og erstattes gjennom hele rapporten. Kandidatnummer er fast.
            </p>

            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-2 pr-3 text-sm font-medium text-gray-600 w-28">Kandidatnr</th>
                    <th className="text-left py-2 pr-3 text-sm font-medium text-gray-600">Navn (søkes etter)</th>
                    <th className="text-left py-2 pr-3 text-sm font-medium text-gray-600 w-32">Initialer (søkes etter)</th>
                    <th className="w-10"></th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {mappings.map((row, index) => (
                    <tr key={index}>
                      <td className="py-2 pr-3">
                        <span className="font-mono text-sm bg-gray-100 px-2 py-1 rounded text-gray-700">
                          {row.candidate_number}
                        </span>
                      </td>
                      <td className="py-2 pr-3">
                        <input
                          type="text"
                          value={row.name}
                          onChange={(e) => updateMapping(index, "name", e.target.value)}
                          className="w-full px-3 py-1.5 border rounded-md text-sm"
                          placeholder="Fullt navn, alternativt navn, ..."
                        />
                      </td>
                      <td className="py-2 pr-3">
                        <input
                          type="text"
                          value={row.initials}
                          onChange={(e) => updateMapping(index, "initials", e.target.value)}
                          className="w-full px-3 py-1.5 border rounded-md text-sm"
                          placeholder="F.N"
                        />
                      </td>
                      <td className="py-2">
                        <button
                          onClick={() => removeMapping(index)}
                          className="p-1.5 text-red-400 hover:text-red-600 hover:bg-red-50 rounded"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <button
              onClick={addMapping}
              className="mt-3 flex items-center gap-2 text-sm text-blue-600 hover:underline"
            >
              <Plus className="w-4 h-4" />
              Legg til person
            </button>
          </div>

          {/* Medforfatterbidrag */}
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Medforfatterbidrag
              <span className="text-sm font-normal text-gray-500 ml-2">(ekstrahert fra vedlegg)</span>
            </h2>

            {Object.keys(medforfatterbidrag).length > 0 ? (
              <div className="space-y-3">
                {Object.entries(medforfatterbidrag).map(([section, initials], idx) => (
                  <div key={idx} className="flex gap-3 items-start">
                    <div className="flex-1">
                      <input
                        type="text"
                        value={section}
                        onChange={(e) => renameMedforfatterbidragSection(section, e.target.value)}
                        className="w-full px-3 py-2 border rounded-md text-sm"
                        placeholder="Seksjonsname"
                      />
                    </div>
                    <div className="w-40">
                      <input
                        type="text"
                        placeholder="Initialer"
                        value={initials.join(", ")}
                        onChange={(e) => updateMedforfatterbidragInitials(section, e.target.value)}
                        className="w-full px-3 py-2 border rounded-md text-sm"
                      />
                    </div>
                    <button
                      onClick={() => removeMedforfatterbidragSection(section)}
                      className="p-2 text-red-400 hover:text-red-600 hover:bg-red-50 rounded-md"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-500 mb-3">
                Ingen medforfatterbidrag funnet i rapporten.
              </p>
            )}

            <button
              onClick={addMedforfatterbidragSection}
              className="mt-3 flex items-center gap-2 text-sm text-blue-600 hover:underline"
            >
              <Plus className="w-4 h-4" />
              Legg til seksjon
            </button>
          </div>

          {/* Pages to remove */}
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-2">Sider å fjerne</h2>
            <p className="text-sm text-gray-600 mb-4">
              Sidenummer (kommaseparert) som skal fjernes fra den anonymiserte rapporten.
              Rapporten har {totalPages} sider.
            </p>
            <input
              type="text"
              placeholder="f.eks. 1, 18"
              value={pagesToRemove}
              onChange={(e) => setPagesToRemove(e.target.value)}
              className="w-full px-3 py-2 border rounded-md"
            />
          </div>

          {/* KI-avklaring */}
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">KI-avklaring</h2>
            <label className="flex items-center gap-3">
              <input
                type="checkbox"
                checked={kiBrukt}
                onChange={(e) => setKiBrukt(e.target.checked)}
                className="w-5 h-5"
              />
              <span>Det er brukt KI-verktøy i denne rapporten</span>
            </label>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-red-700">{error}</p>
            </div>
          )}

          <div className="flex gap-4">
            <button
              onClick={() => router.back()}
              className="px-4 py-2 border rounded-md hover:bg-gray-50"
            >
              Avbryt
            </button>
            <button
              onClick={handleAnonymize}
              disabled={anonymizing}
              className="flex-1 flex items-center justify-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              {anonymizing ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Anonymiserer...
                </>
              ) : (
                <>
                  <UserX className="w-4 h-4" />
                  Bekreft og anonymiser
                </>
              )}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
