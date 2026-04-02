"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, UserX, Plus, Trash2, Download, Check, Loader2, AlertCircle } from "lucide-react";

interface Author {
  name: string;
  initials: string;
}

interface ExtractedInfo {
  authors: Author[];
  medforfatterbidrag: Record<string, string[]>;
  ki_brukt: boolean;
  total_pages: number;
  suggested_pages_to_remove: number[];
  title: string;
  oppgave: string | null;
  dato: string | null;
}

interface AuthorMapping {
  name: string;
  initials: string;
  candidate_number: string;
}

export default function AnonymizePage() {
  const params = useParams();
  const router = useRouter();
  const reportId = params.id as string;

  const [loading, setLoading] = useState(true);
  const [extracting, setExtracting] = useState(true);
  const [anonymizing, setAnonymizing] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Extracted/editable data
  const [title, setTitle] = useState("");
  const [dato, setDato] = useState("");
  const [oppgave, setOppgave] = useState("");
  const [authors, setAuthors] = useState<Author[]>([]);
  const [medforfatterbidrag, setMedforfatterbidrag] = useState<Record<string, string[]>>({});
  const [kiBrukt, setKiBrukt] = useState(false);
  const [totalPages, setTotalPages] = useState(0);
  const [pagesToRemove, setPagesToRemove] = useState<string>("");

  // Result state
  const [mappings, setMappings] = useState<AuthorMapping[]>([]);

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

  useEffect(() => {
    const extractInfo = async () => {
      try {
        const response = await fetch(`http://localhost:8000/api/reports/${reportId}/extract-info`);
        if (!response.ok) {
          const err = await response.json();
          throw new Error(err.detail || "Kunne ikke hente rapport-info");
        }
        const data: ExtractedInfo = await response.json();

        setTitle(data.title);
        setDato(data.dato || "");
        setOppgave(data.oppgave || "");
        setAuthors(data.authors.length > 0 ? data.authors : [{ name: "", initials: "" }]);
        setMedforfatterbidrag(data.medforfatterbidrag);
        setKiBrukt(data.ki_brukt);
        setTotalPages(data.total_pages);
        setPagesToRemove(data.suggested_pages_to_remove.join(", "));
      } catch (err) {
        setError(err instanceof Error ? err.message : "Noe gikk galt");
      } finally {
        setExtracting(false);
        setLoading(false);
      }
    };

    extractInfo();
  }, [reportId]);

  const addAuthor = () => {
    setAuthors([...authors, { name: "", initials: "" }]);
  };

  const removeAuthor = (index: number) => {
    setAuthors(authors.filter((_, i) => i !== index));
  };

  const updateAuthor = (index: number, field: keyof Author, value: string) => {
    const updated = [...authors];
    updated[index][field] = value;
    setAuthors(updated);
  };

  const updateMedforfatterbidrag = (section: string, value: string) => {
    const initials = value.split(",").map((s) => s.trim()).filter(Boolean);
    setMedforfatterbidrag({ ...medforfatterbidrag, [section]: initials });
  };

  const addMedforfatterbidragSection = () => {
    const newSection = `Ny seksjon ${Object.keys(medforfatterbidrag).length + 1}`;
    setMedforfatterbidrag({ ...medforfatterbidrag, [newSection]: [] });
  };

  const removeMedforfatterbidragSection = (section: string) => {
    const updated = { ...medforfatterbidrag };
    delete updated[section];
    setMedforfatterbidrag(updated);
  };

  const handleAnonymize = async () => {
    if (authors.some((a) => !a.name || !a.initials)) {
      alert("Fyll inn navn og initialer for alle forfattere");
      return;
    }

    setAnonymizing(true);
    setError(null);

    // Convert pages to 0-indexed array
    const pages = pagesToRemove
      .split(",")
      .map((p) => parseInt(p.trim()) - 1)
      .filter((p) => !isNaN(p) && p >= 0);

    try {
      const response = await fetch(`http://localhost:8000/api/reports/${reportId}/anonymize`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          authors,
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
      setMappings(result.mappings);
      setDone(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Noe gikk galt");
    } finally {
      setAnonymizing(false);
    }
  };

  if (loading || extracting) {
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
          <button
            onClick={() => router.back()}
            className="mt-4 text-blue-600 hover:underline"
          >
            Tilbake
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="px-4 max-w-3xl mx-auto">
      {/* Header */}
      <div className="flex items-center gap-4 mb-6">
        <button
          onClick={() => router.back()}
          className="p-2 hover:bg-gray-100 rounded-md"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Anonymiser rapport</h1>
          <p className="text-gray-600">{title}</p>
        </div>
      </div>

      {done ? (
        /* Success view */
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
              <Check className="w-6 h-6 text-green-600" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-gray-900">Rapport anonymisert!</h2>
              <p className="text-sm text-gray-600">
                Forsiden og vedleggene er erstattet med anonymisert informasjon.
              </p>
            </div>
          </div>

          {/* Mapping table */}
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
                {mappings.map((m, i) => (
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

          {/* Download buttons */}
          <div className="flex gap-4">
            <button
              onClick={() => downloadFile(
                `http://localhost:8000/api/reports/${reportId}/mapping-file`,
                `kandidatmapping_${title.replace(/\s+/g, "_")}.txt`
              )}
              className="flex items-center gap-2 px-4 py-2 border rounded-md hover:bg-gray-50"
            >
              <Download className="w-4 h-4" />
              Last ned mapping-fil
            </button>
            <button
              onClick={() => downloadFile(
                `http://localhost:8000/api/reports/${reportId}/anonymized-pdf`,
                `${title.replace(/\s+/g, "_")}_anonym.pdf`
              )}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              <Download className="w-4 h-4" />
              Last ned anonymisert PDF
            </button>
          </div>

          <div className="mt-6 pt-6 border-t">
            <button
              onClick={() => router.push(`/reports/${reportId}`)}
              className="text-blue-600 hover:underline"
            >
              Gå til rapport for evaluering
            </button>
          </div>
        </div>
      ) : (
        /* Confirmation form */
        <div className="space-y-6">
          {/* Info banner */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <p className="text-sm text-blue-800">
              Informasjonen nedenfor er automatisk ekstrahert fra rapporten.
              Bekreft at alt er korrekt, eller gjør endringer før du anonymiserer.
            </p>
          </div>

          {/* Title and Date section */}
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Tittel og dato
              <span className="text-sm font-normal text-gray-500 ml-2">
                (ekstrahert fra forside)
              </span>
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

          {/* Authors section */}
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Forfattere
              <span className="text-sm font-normal text-gray-500 ml-2">
                (ekstrahert fra forside)
              </span>
            </h2>

            <div className="space-y-3">
              {authors.map((author, index) => (
                <div key={index} className="flex gap-3 items-start">
                  <div className="flex-1">
                    <input
                      type="text"
                      placeholder="Fullt navn"
                      value={author.name}
                      onChange={(e) => updateAuthor(index, "name", e.target.value)}
                      className="w-full px-3 py-2 border rounded-md"
                    />
                  </div>
                  <div className="w-32">
                    <input
                      type="text"
                      placeholder="Initialer"
                      value={author.initials}
                      onChange={(e) => updateAuthor(index, "initials", e.target.value)}
                      className="w-full px-3 py-2 border rounded-md"
                    />
                  </div>
                  {authors.length > 1 && (
                    <button
                      onClick={() => removeAuthor(index)}
                      className="p-2 text-red-600 hover:bg-red-50 rounded-md"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  )}
                </div>
              ))}
            </div>

            <button
              onClick={addAuthor}
              className="mt-3 flex items-center gap-2 text-sm text-blue-600 hover:underline"
            >
              <Plus className="w-4 h-4" />
              Legg til forfatter
            </button>
          </div>

          {/* Medforfatterbidrag section */}
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Medforfatterbidrag
              <span className="text-sm font-normal text-gray-500 ml-2">
                (ekstrahert fra vedlegg)
              </span>
            </h2>

            {Object.keys(medforfatterbidrag).length > 0 ? (
              <div className="space-y-3">
                {Object.entries(medforfatterbidrag).map(([section, initials]) => (
                  <div key={section} className="flex gap-3 items-start">
                    <div className="flex-1">
                      <input
                        type="text"
                        value={section}
                        readOnly
                        className="w-full px-3 py-2 border rounded-md bg-gray-50"
                      />
                    </div>
                    <div className="w-40">
                      <input
                        type="text"
                        placeholder="Initialer"
                        value={initials.join(", ")}
                        onChange={(e) => updateMedforfatterbidrag(section, e.target.value)}
                        className="w-full px-3 py-2 border rounded-md"
                      />
                    </div>
                    <button
                      onClick={() => removeMedforfatterbidragSection(section)}
                      className="p-2 text-red-600 hover:bg-red-50 rounded-md"
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
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Sider å fjerne</h2>
            <p className="text-sm text-gray-600 mb-4">
              Sidenummer (kommaseparert) som skal fjernes. Rapporten har {totalPages} sider.
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

          {/* Error message */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-red-700">{error}</p>
            </div>
          )}

          {/* Submit button */}
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
