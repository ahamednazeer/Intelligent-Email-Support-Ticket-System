'use client';

import React, { useEffect, useMemo, useState } from 'react';
import { api } from '@/lib/api';
import { DataCard } from '@/components/DataCard';
import { StatusBadge } from '@/components/StatusBadge';
import {
    ClipboardText,
    Pulse,
    Sparkle,
    Gauge,
    Ticket,
    WarningCircle,
    HourglassLow,
    CheckCircle,
    ArrowRight
} from '@phosphor-icons/react';
import Link from 'next/link';

interface TicketItem {
    ticket_id: string;
    sender_email: string;
    subject?: string;
    status: string;
    priority_level?: string;
    created_at: string;
    sla_deadline?: string;
}

export default function AgentDashboardPage() {
    const [user, setUser] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [tickets, setTickets] = useState<TicketItem[]>([]);

    useEffect(() => {
        async function fetchData() {
            try {
                const [userData, ticketData] = await Promise.all([
                    api.getMe(),
                    api.listTickets(),
                ]);
                setUser(userData);
                setTickets(ticketData || []);
            } catch (error) {
                console.error('Failed to fetch dashboard data:', error);
            } finally {
                setLoading(false);
            }
        }
        fetchData();
    }, []);

    const stats = useMemo(() => {
        const assigned = tickets.length;
        const inProgress = tickets.filter(t => ['ASSIGNED', 'IN_PROGRESS'].includes(t.status)).length;
        const waiting = tickets.filter(t => t.status === 'WAITING_FOR_CUSTOMER').length;
        const critical = tickets.filter(t => t.priority_level === 'CRITICAL').length;
        return { assigned, inProgress, waiting, critical };
    }, [tickets]);

    const priorityCounts = useMemo(() => {
        const counts: Record<string, number> = { CRITICAL: 0, HIGH: 0, MEDIUM: 0, LOW: 0 };
        tickets.forEach(t => {
            const key = t.priority_level || 'LOW';
            counts[key] = (counts[key] || 0) + 1;
        });
        return counts;
    }, [tickets]);

    const recentTickets = tickets.slice(0, 6);

    if (loading) {
        return (
            <div className="flex flex-col items-center justify-center h-64 gap-4">
                <div className="relative">
                    <div className="w-12 h-12 rounded-full border-2 border-slate-700 border-t-blue-500 animate-spin" />
                    <Pulse size={24} className="absolute inset-0 m-auto text-blue-400 animate-pulse" />
                </div>
                <p className="text-slate-500 font-mono text-xs uppercase tracking-widest animate-pulse">
                    Loading Dashboard...
                </p>
            </div>
        );
    }

    return (
        <div className="space-y-8">
            <div className="flex items-center justify-between flex-wrap gap-4">
                <div>
                    <h1 className="text-2xl font-chivo font-bold uppercase tracking-wider flex items-center gap-3">
                        <Gauge size={28} weight="duotone" className="text-blue-400" />
                        Agent Dashboard
                    </h1>
                    <p className="text-slate-500 mt-1">
                        Welcome back, <span className="text-slate-300 font-medium">{user?.full_name || user?.username || 'Agent'}</span>!
                        Here is your live ticket snapshot.
                    </p>
                </div>
                <Link
                    href="/dashboard/agent/tickets"
                    className="flex items-center gap-2 px-4 py-2 bg-gradient-to-br from-blue-950/40 to-blue-900/20 border border-blue-700/50 rounded-xl hover:border-blue-500/70 transition-all"
                >
                    <ClipboardText size={20} weight="duotone" className="text-blue-400" />
                    <span className="text-blue-300 font-bold text-sm uppercase tracking-wider">View My Tickets</span>
                </Link>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <DataCard title="Assigned" value={stats.assigned} icon={Ticket} />
                <DataCard title="In Progress" value={stats.inProgress} icon={HourglassLow} />
                <DataCard title="Waiting" value={stats.waiting} icon={ClipboardText} />
                <DataCard title="Critical" value={stats.critical} icon={WarningCircle} />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="bg-slate-800/40 border border-slate-700/60 rounded-xl p-6 relative overflow-hidden">
                    <Sparkle size={80} weight="duotone" className="absolute -right-4 -top-4 text-slate-700/20" />
                    <h3 className="text-sm font-mono text-slate-400 uppercase tracking-widest mb-5 flex items-center gap-2">
                        <WarningCircle size={16} weight="duotone" />
                        Priority Snapshot
                    </h3>
                    <div className="grid grid-cols-2 gap-4 relative z-10">
                        {Object.entries(priorityCounts).map(([priority, count]) => (
                            <div key={priority} className="bg-slate-900/50 border border-slate-800/50 rounded-xl p-4">
                                <div className="flex items-center justify-between">
                                    <StatusBadge status={priority} />
                                    <span className="text-slate-100 font-mono text-xl font-bold">{count}</span>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                <div className="bg-slate-800/40 border border-slate-700/60 rounded-xl p-6 relative overflow-hidden">
                    <Sparkle size={80} weight="duotone" className="absolute -right-4 -top-4 text-slate-700/20" />
                    <h3 className="text-sm font-mono text-slate-400 uppercase tracking-widest mb-5 flex items-center gap-2">
                        <CheckCircle size={16} weight="duotone" />
                        Recent Tickets
                    </h3>
                    {recentTickets.length > 0 ? (
                        <div className="space-y-2 relative z-10">
                            {recentTickets.map((ticket) => (
                                <div key={ticket.ticket_id} className="flex items-center justify-between p-3 bg-slate-900/50 border border-slate-800/50 rounded-xl">
                                    <div className="flex flex-col">
                                        <span className="text-slate-300 text-sm truncate max-w-[240px]">{ticket.subject || 'No subject'}</span>
                                        <span className="text-xs text-slate-500 font-mono">{ticket.sender_email}</span>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <StatusBadge status={ticket.priority_level || 'LOW'} />
                                        <StatusBadge status={ticket.status} />
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="text-slate-500 text-sm font-mono">No tickets assigned yet.</div>
                    )}
                    <Link
                        href="/dashboard/agent/tickets"
                        className="mt-4 flex items-center justify-center gap-2 text-sm text-blue-400 hover:text-blue-300 transition-colors"
                    >
                        Open full queue <ArrowRight size={16} />
                    </Link>
                </div>
            </div>
        </div>
    );
}
