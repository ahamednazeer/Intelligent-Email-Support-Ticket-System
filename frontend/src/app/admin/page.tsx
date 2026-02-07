'use client';

import React, { useEffect, useState } from 'react';

import { DataCard } from '@/components/DataCard';
import { api } from '@/lib/api';
import { Users, Pulse, Sparkle, Gauge, ArrowSquareOut, Ticket, ChartLineUp } from '@phosphor-icons/react';

interface AnalyticsSummary {
    total_tickets: number;
    open_tickets: number;
    resolved_tickets: number;
    avg_resolution_time_hours: number | null;
    tickets_by_category: Record<string, number>;
    tickets_by_priority: Record<string, number>;
}

export default function AdminDashboard() {
    const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
    const [agentCount, setAgentCount] = useState<number>(0);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        async function fetchData() {
            try {
                const [summaryData, agents] = await Promise.all([
                    api.getAnalyticsSummary(),
                    api.listAgents(),
                ]);
                setSummary(summaryData);
                setAgentCount((agents || []).length);
            } catch (error) {
                console.error('Failed to fetch data:', error);
            } finally {
                setLoading(false);
            }
        }
        fetchData();
    }, []);

    if (loading) {
        return (
            <div className="flex flex-col items-center justify-center h-64 gap-4">
                <div className="relative">
                    <div className="w-12 h-12 rounded-full border-2 border-slate-700 border-t-indigo-500 animate-spin" />
                    <Pulse size={24} className="absolute inset-0 m-auto text-indigo-400 animate-pulse" />
                </div>
                <p className="text-slate-500 font-mono text-xs uppercase tracking-widest animate-pulse">
                    Loading Admin Dashboard...
                </p>
            </div>
        );
    }

    return (
        <div className="space-y-8">
            <div>
                <h1 className="text-2xl font-chivo font-bold uppercase tracking-wider flex items-center gap-3">
                    <Gauge size={28} weight="duotone" className="text-indigo-400" />
                    Administration
                </h1>
                <p className="text-slate-500 mt-1">System overview and operational KPIs</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <DataCard title="Total Tickets" value={summary?.total_tickets || 0} icon={Ticket} />
                <DataCard title="Open Tickets" value={summary?.open_tickets || 0} icon={ChartLineUp} />
                <DataCard title="Resolved" value={summary?.resolved_tickets || 0} icon={Ticket} />
                <DataCard title="Active Agents" value={agentCount} icon={Users} />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="bg-slate-800/40 border border-slate-700/60 rounded-xl p-6 relative overflow-hidden">
                    <Sparkle size={80} weight="duotone" className="absolute -right-4 -top-4 text-slate-700/20" />
                    <h3 className="text-sm font-mono text-slate-400 uppercase tracking-widest mb-5 flex items-center gap-2">
                        <Ticket size={16} weight="duotone" />
                        Tickets by Priority
                    </h3>
                    <div className="space-y-3 relative z-10">
                        {summary?.tickets_by_priority && Object.entries(summary.tickets_by_priority).map(([priority, count]) => (
                            <div key={priority} className="flex items-center justify-between bg-slate-900/50 border border-slate-800/50 rounded-xl px-4 py-3 hover:bg-slate-800/50 transition-colors">
                                <span className="text-slate-400 text-sm font-mono uppercase tracking-wider">{priority}</span>
                                <span className="text-slate-100 font-bold font-mono text-lg">{count}</span>
                            </div>
                        ))}
                    </div>
                </div>

                <div className="bg-slate-800/40 border border-slate-700/60 rounded-xl p-6 relative overflow-hidden">
                    <Sparkle size={80} weight="duotone" className="absolute -right-4 -top-4 text-slate-700/20" />
                    <h3 className="text-sm font-mono text-slate-400 uppercase tracking-widest mb-5 flex items-center gap-2">
                        <ArrowSquareOut size={16} weight="duotone" />
                        Quick Actions
                    </h3>
                    <div className="grid grid-cols-2 gap-3 relative z-10">
                        <button
                            onClick={() => window.location.href = '/admin/tickets'}
                            className="bg-gradient-to-br from-blue-900/40 to-blue-950/60 border border-blue-700/30 hover:border-blue-600/50 rounded-xl px-4 py-3 text-blue-300 font-bold text-sm uppercase tracking-wider transition-all hover:scale-[1.02]"
                        >
                            View Tickets
                        </button>
                        <button
                            onClick={() => window.location.href = '/admin/agents'}
                            className="bg-gradient-to-br from-purple-900/40 to-purple-950/60 border border-purple-700/30 hover:border-purple-600/50 rounded-xl px-4 py-3 text-purple-300 font-bold text-sm uppercase tracking-wider transition-all hover:scale-[1.02]"
                        >
                            Manage Agents
                        </button>
                        <button
                            onClick={() => window.location.href = '/admin/analytics'}
                            className="bg-gradient-to-br from-green-900/40 to-green-950/60 border border-green-700/30 hover:border-green-600/50 rounded-xl px-4 py-3 text-green-300 font-bold text-sm uppercase tracking-wider transition-all hover:scale-[1.02]"
                        >
                            Analytics
                        </button>
                        <button
                            onClick={() => window.location.href = '/admin/retrain'}
                            className="bg-gradient-to-br from-orange-900/40 to-orange-950/60 border border-orange-700/30 hover:border-orange-600/50 rounded-xl px-4 py-3 text-orange-300 font-bold text-sm uppercase tracking-wider transition-all hover:scale-[1.02]"
                        >
                            Retrain Model
                        </button>
                    </div>
                    {summary?.avg_resolution_time_hours !== null && summary?.avg_resolution_time_hours !== undefined && (
                        <div className="mt-4 p-4 bg-slate-950/50 border border-slate-800 rounded-xl flex items-center gap-3">
                            <ChartLineUp size={20} weight="duotone" className="text-blue-400" />
                            <p className="text-blue-300 text-sm font-mono uppercase tracking-wider">
                                Avg resolution time: {summary.avg_resolution_time_hours.toFixed(1)} hrs
                            </p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
