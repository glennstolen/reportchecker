"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import { FileText, Settings, ArrowRight } from "lucide-react";

interface Stats {
  reports: number;
  agents: number;
  evaluations: number;
}

export default function Home() {
  const [stats, setStats] = useState<Stats>({ reports: 0, agents: 0, evaluations: 0 });

  useEffect(() => {
    // Fetch basic stats
    Promise.all([
      apiFetch("/api/reports").then((r) => r.json()),
      apiFetch("/api/agents").then((r) => r.json()),
      apiFetch("/api/evaluations/count").then((r) => r.json()),
    ])
      .then(([reports, agents, evalCount]) => {
        setStats({
          reports: reports.length,
          agents: agents.length,
          evaluations: evalCount.count,
        });
      })
      .catch(() => {});
  }, []);

  return (
    <div className="px-4">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">
          Velkommen til ReportChecker
        </h1>
        <p className="mt-2 text-gray-600">
          Bruk AI-agenter til å evaluere studenters labrapporter
        </p>
      </div>

      {/* Quick actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        <a
          href="/reports/upload"
          className="bg-white p-6 rounded-lg shadow-sm border hover:border-blue-500 transition-colors"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <div className="bg-blue-100 p-3 rounded-lg">
                <FileText className="w-6 h-6 text-blue-600" />
              </div>
              <div className="ml-4">
                <h3 className="text-lg font-semibold text-gray-900">
                  Last opp rapport
                </h3>
                <p className="text-sm text-gray-600">
                  Last opp en PDF eller Word-fil for evaluering
                </p>
              </div>
            </div>
            <ArrowRight className="w-5 h-5 text-gray-400" />
          </div>
        </a>

        <a
          href="/agents"
          className="bg-white p-6 rounded-lg shadow-sm border hover:border-blue-500 transition-colors"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <div className="bg-green-100 p-3 rounded-lg">
                <Settings className="w-6 h-6 text-green-600" />
              </div>
              <div className="ml-4">
                <h3 className="text-lg font-semibold text-gray-900">
                  Konfigurer agenter
                </h3>
                <p className="text-sm text-gray-600">
                  Tilpass hva AI skal sjekke
                </p>
              </div>
            </div>
            <ArrowRight className="w-5 h-5 text-gray-400" />
          </div>
        </a>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <p className="text-sm text-gray-600">Rapporter</p>
          <p className="text-2xl font-bold text-gray-900">{stats.reports}</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <p className="text-sm text-gray-600">Agenter</p>
          <p className="text-2xl font-bold text-gray-900">{stats.agents}</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <p className="text-sm text-gray-600">Evalueringer</p>
          <p className="text-2xl font-bold text-gray-900">{stats.evaluations}</p>
        </div>
      </div>
    </div>
  );
}
