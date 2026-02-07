'use client';

import React, { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import DataTable from '@/components/DataTable';
import { StatusBadge } from '@/components/StatusBadge';
import { ClipboardText, Pulse } from '@phosphor-icons/react';

interface AuditLogItem {
    log_id: number;
    action: string;
    target_type: string;
    target_id: string;
    actor_username: string;
    actor_role: string;
    metadata: Record<string, any>;
    created_at: string;
}

export default function AuditLogPage() {
    const [logs, setLogs] = useState<AuditLogItem[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        async function fetchLogs() {
            try {
                const data = await api.getAuditLogs();
                setLogs(data || []);
            } catch (error) {
                console.error('Failed to load audit logs', error);
            } finally {
                setLoading(false);
            }
        }
        fetchLogs();
    }, []);

    if (loading) {
        return (
            <div className="flex flex-col items-center justify-center h-64 gap-4">
                <div className="relative">
                    <div className="w-12 h-12 rounded-full border-2 border-slate-700 border-t-blue-500 animate-spin" />
                    <Pulse size={24} className="absolute inset-0 m-auto text-blue-400 animate-pulse" />
                </div>
                <p className="text-slate-500 font-mono text-xs uppercase tracking-widest animate-pulse">
                    Loading Audit Logs...
                </p>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-2xl font-chivo font-bold uppercase tracking-wider flex items-center gap-3">
                    <ClipboardText size={28} weight="duotone" className="text-blue-400" />
                    Audit Log
                </h1>
                <p className="text-slate-500 mt-1">Password resets and ticket assignments.</p>
            </div>

            <DataTable
                data={logs.map((l) => ({ ...l, id: l.log_id }))}
                columns={[
                    {
                        key: 'action',
                        label: 'Action',
                        render: (item: any) => <StatusBadge status={item.action} />,
                    },
                    {
                        key: 'actor',
                        label: 'Actor',
                        render: (item: any) => (
                            <div>
                                <div className="text-slate-200 font-mono text-xs">{item.actor_username}</div>
                                <div className="text-slate-500 text-xs">{item.actor_role}</div>
                            </div>
                        ),
                    },
                    {
                        key: 'target',
                        label: 'Target',
                        render: (item: any) => (
                            <div className="text-slate-400 text-xs font-mono">
                                {item.target_type} · {item.target_id.slice(0, 8)}
                            </div>
                        ),
                    },
                    {
                        key: 'metadata',
                        label: 'Details',
                        render: (item: any) => (
                            <div className="text-slate-400 text-xs font-mono">
                                {item.metadata && Object.keys(item.metadata).length > 0
                                    ? JSON.stringify(item.metadata)
                                    : '—'}
                            </div>
                        ),
                    },
                    {
                        key: 'created_at',
                        label: 'Time',
                        render: (item: any) => (
                            <div className="text-slate-400 text-xs font-mono">
                                {new Date(item.created_at).toLocaleString()}
                            </div>
                        ),
                    },
                ]}
                emptyMessage="No audit entries yet"
            />
        </div>
    );
}
