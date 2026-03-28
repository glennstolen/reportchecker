"use client";

import { useEffect, useState } from "react";
import { FileText, Plus, Trash2 } from "lucide-react";

interface Report {
  id: number;
  title: string;
  filename: string;
  status: string;
  created_at: string;
}

export default function ReportsPage() {
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchReports();
  }, []);

  const fetchReports = async () => {
    try {
      const response = await fetch("http://localhost:8000/api/reports");
      const data = await response.json();
      setReports(data);
    } catch (error) {
      console.error("Failed to fetch reports:", error);
    } finally {
      setLoading(false);
    }
  };

  const deleteReport = async (id: number) => {
    if (!confirm("Er du sikker på at du vil slette denne rapporten?")) return;

    try {
      await fetch(`http://localhost:8000/api/reports/${id}`, {
        method: "DELETE",
      });
      setReports(reports.filter((r) => r.id !== id));
    } catch (error) {
      console.error("Failed to delete report:", error);
    }
  };

  const getStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      READY: "bg-green-100 text-green-800",
      PROCESSING: "bg-yellow-100 text-yellow-800",
      UPLOADED: "bg-blue-100 text-blue-800",
      ERROR: "bg-red-100 text-red-800",
    };
    const labels: Record<string, string> = {
      READY: "Klar",
      PROCESSING: "Behandles",
      UPLOADED: "Lastet opp",
      ERROR: "Feil",
    };
    return (
      <span
        className={`px-2 py-1 text-xs font-medium rounded-full ${styles[status] || "bg-gray-100"}`}
      >
        {labels[status] || status}
      </span>
    );
  };

  if (loading) {
    return <div className="px-4">Laster...</div>;
  }

  return (
    <div className="px-4">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Rapporter</h1>
        <a
          href="/reports/upload"
          className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
        >
          <Plus className="w-4 h-4" />
          Last opp
        </a>
      </div>

      {reports.length === 0 ? (
        <div className="bg-white rounded-lg shadow-sm border p-8 text-center">
          <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            Ingen rapporter ennå
          </h3>
          <p className="text-gray-600 mb-4">
            Last opp en rapport for å komme i gang
          </p>
          <a
            href="/reports/upload"
            className="inline-flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
          >
            <Plus className="w-4 h-4" />
            Last opp rapport
          </a>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow-sm border overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Tittel
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Filnavn
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Dato
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Handlinger
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {reports.map((report) => (
                <tr key={report.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <a
                      href={`/reports/${report.id}`}
                      className="text-blue-600 hover:text-blue-800 font-medium"
                    >
                      {report.title}
                    </a>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {report.filename}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {getStatusBadge(report.status)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {new Date(report.created_at).toLocaleDateString("no-NO")}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <button
                      onClick={() => deleteReport(report.id)}
                      className="text-red-600 hover:text-red-800"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
