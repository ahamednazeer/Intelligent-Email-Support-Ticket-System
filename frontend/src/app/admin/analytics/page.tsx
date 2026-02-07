'use client';

import React, { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { DataCard } from '@/components/DataCard';
import { ChartLineUp, Pulse, Sparkle, Ticket, WarningCircle } from '@phosphor-icons/react';

interface AnalyticsSummary {
    total_tickets: number;
    open_tickets: number;
    resolved_tickets: number;
    avg_resolution_time_hours: number | null;
    tickets_by_category: Record<string, number>;
    tickets_by_priority: Record<string, number>;
}

export default function AnalyticsPage() {
    const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        async function fetchAnalytics() {
            try {
                const data = await api.getAnalyticsSummary();
                setSummary(data);
            } catch (error) {
                console.error('Failed to load analytics', error);
            } finally {
                setLoading(false);
            }
        }
        fetchAnalytics();
    }, []);

    if (loading) {
        return (
            <div className="flex flex-col items-center justify-center h-64 gap-4">
                <div className="relative">
                    <div className="w-12 h-12 rounded-full border-2 border-slate-700 border-t-green-500 animate-spin" />
                    <Pulse size={24} className="absolute inset-0 m-auto text-green-400 animate-pulse" />
                </div>
                <p className="text-slate-500 font-mono text-xs uppercase tracking-widest animate-pulse">
                    Loading Analytics...
                </p>
            </div>
        );
    }

    return (
        <div className="space-y-8">
            <div>
                <h1 className="text-2xl font-chivo font-bold uppercase tracking-wider flex items-center gap-3">
                    <ChartLineUp size={28} weight="duotone" className="text-green-400" />
                    Analytics & Monitoring
                </h1>
                <p className="text-slate-500 mt-1">Operational health and SLA visibility.</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <DataCard title="Total Tickets" value={summary?.total_tickets || 0} icon={Ticket} />
                <DataCard title="Open" value={summary?.open_tickets || 0} icon={WarningCircle} />
                <DataCard title="Resolved" value={summary?.resolved_tickets || 0} icon={Ticket} />
                <DataCard
                    title="Avg Resolution (hrs)"
                    value={summary?.avg_resolution_time_hours ? summary.avg_resolution_time_hours.toFixed(1) : '—'}
                    icon={ChartLineUp}
                />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="bg-slate-800/40 border border-slate-700/60 rounded-xl p-6 relative overflow-hidden">
                    <Sparkle size={80} weight="duotone" className="absolute -right-4 -top-4 text-slate-700/20" />
                    <h3 className="text-sm font-mono text-slate-400 uppercase tracking-widest mb-5 flex items-center gap-2">
                        <Ticket size={16} weight="duotone" />
                        Tickets by Category
                    </h3>
                    <div className="space-y-3 relative z-10">
                        {summary?.tickets_by_category && Object.entries(summary.tickets_by_category).map(([category, count]) => (
                            <div key={category} className="flex items-center justify-between bg-slate-900/50 border border-slate-800/50 rounded-xl px-4 py-3">
                                <span className="text-slate-400 text-sm font-mono uppercase tracking-wider">{category}</span>
                                <span className="text-slate-100 font-bold font-mono text-lg">{count}</span>
                            </div>
                        ))}
                    </div>
                </div>

                <div className="bg-slate-800/40 border border-slate-700/60 rounded-xl p-6 relative overflow-hidden">
                    <Sparkle size={80} weight="duotone" className="absolute -right-4 -top-4 text-slate-700/20" />
                    <h3 className="text-sm font-mono text-slate-400 uppercase tracking-widest mb-5 flex items-center gap-2">
                        <WarningCircle size={16} weight="duotone" />
                        Tickets by Priority
                    </h3>
                    <div className="space-y-3 relative z-10">
                        {summary?.tickets_by_priority && Object.entries(summary.tickets_by_priority).map(([priority, count]) => (
                            <div key={priority} className="flex items-center justify-between bg-slate-900/50 border border-slate-800/50 rounded-xl px-4 py-3">
                                <span className="text-slate-400 text-sm font-mono uppercase tracking-wider">{priority}</span>
                                <span className="text-slate-100 font-bold font-mono text-lg">{count}</span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
}
