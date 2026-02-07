'use client';

import React, { useEffect, useRef, useState } from 'react';
import { api } from '@/lib/api';
import DataTable from '@/components/DataTable';
import { StatusBadge } from '@/components/StatusBadge';
import Toast from '@/components/Toast';
import { ClipboardText, Pulse } from '@phosphor-icons/react';
import { useRouter } from 'next/navigation';

interface TicketItem {
    ticket_id: string;
    sender_email: string;
    subject?: string;
    status: string;
    priority_level?: string;
    assigned_agent_id?: string;
    suggested_agent_id?: string;
    review_required?: boolean;
    sla_deadline?: string;
    created_at: string;
}

interface AgentItem {
    agent_id: string;
    name: string;
    department?: string;
    active: boolean;
}

const STATUS_OPTIONS = ['ASSIGNED', 'IN_PROGRESS', 'WAITING_FOR_CUSTOMER', 'RESOLVED'];
const REFRESH_INTERVAL_MS = 30000;

export default function AgentTicketsPage() {
    const router = useRouter();
    const [tickets, setTickets] = useState<TicketItem[]>([]);
    const [agents, setAgents] = useState<AgentItem[]>([]);
    const [role, setRole] = useState<string>('GENERAL');
    const [loading, setLoading] = useState(true);
    const [updating, setUpdating] = useState<string | null>(null);
    const [assigning, setAssigning] = useState<string | null>(null);
    const [toastMessage, setToastMessage] = useState<string | null>(null);
    const knownTicketIds = useRef<Set<string>>(new Set());
    const refreshingRef = useRef(false);
    const hasLoaded = useRef(false);
    const [refreshing, setRefreshing] = useState(false);

    const refreshTickets = async (showToast: boolean) => {
        if (refreshingRef.current) return;
        if (typeof document !== 'undefined' && document.visibilityState === 'hidden') return;
        refreshingRef.current = true;
        setRefreshing(true);
        try {
            const data = await api.listTickets();
            const incoming = data || [];
            const newTickets = incoming.filter((ticket) => !knownTicketIds.current.has(ticket.ticket_id));
            setTickets(incoming);
            if (hasLoaded.current && showToast && newTickets.length > 0) {
                const count = newTickets.length;
                setToastMessage(`${count} new ticket${count === 1 ? '' : 's'} in queue`);
            }
            knownTicketIds.current = new Set(incoming.map((ticket) => ticket.ticket_id));
        } catch (error) {
            console.error('Failed to refresh tickets', error);
        } finally {
            refreshingRef.current = false;
            setRefreshing(false);
        }
    };

    useEffect(() => {
        async function fetchTickets() {
            try {
                const user = await api.getMe();
                setRole(user.role);
                const data = await api.listTickets();
                setTickets(data || []);
                knownTicketIds.current = new Set((data || []).map((ticket) => ticket.ticket_id));
                if (user.role === 'SUPERVISOR') {
                    const agentData = await api.listAgents();
                    setAgents(agentData || []);
                }
            } catch (error) {
                console.error('Failed to load tickets', error);
            } finally {
                hasLoaded.current = true;
                setLoading(false);
            }
        }
        fetchTickets();

        const interval = setInterval(() => {
            refreshTickets(true);
        }, REFRESH_INTERVAL_MS);

        return () => clearInterval(interval);
    }, []);

    const handleStatusChange = async (ticketId: string, status: string) => {
        setUpdating(ticketId);
        try {
            const updated = await api.updateTicketStatus(ticketId, status);
            setTickets((prev) => prev.map((t) => (t.ticket_id === ticketId ? updated : t)));
        } catch (error) {
            console.error('Failed to update status', error);
        } finally {
            setUpdating(null);
        }
    };

    const handleAssignmentChange = async (ticketId: string, agentId: string) => {
        setAssigning(ticketId);
        try {
            const updated = await api.assignTicket(ticketId, agentId || null);
            setTickets((prev) => prev.map((t) => (t.ticket_id === ticketId ? updated : t)));
        } catch (error) {
            console.error('Failed to assign ticket', error);
        } finally {
            setAssigning(null);
        }
    };

    const isSupervisor = role === 'SUPERVISOR';

    if (loading) {
        return (
            <div className="flex flex-col items-center justify-center h-64 gap-4">
                <div className="relative">
                    <div className="w-12 h-12 rounded-full border-2 border-slate-700 border-t-blue-500 animate-spin" />
                    <Pulse size={24} className="absolute inset-0 m-auto text-blue-400 animate-pulse" />
                </div>
                <p className="text-slate-500 font-mono text-xs uppercase tracking-widest animate-pulse">
                    Loading Tickets...
                </p>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {toastMessage && (
                <Toast
                    message={toastMessage}
                    onClose={() => setToastMessage(null)}
                    actionLabel="View latest"
                    onAction={() => {
                        if (typeof window !== 'undefined') {
                            window.scrollTo({ top: 0, behavior: 'smooth' });
                        }
                        setToastMessage(null);
                    }}
                />
            )}
            <div className="flex items-center justify-between flex-wrap gap-4">
                <div>
                    <h1 className="text-2xl font-chivo font-bold uppercase tracking-wider flex items-center gap-3">
                        <ClipboardText size={28} weight="duotone" className="text-blue-400" />
                        {isSupervisor ? 'Team Ticket Queue' : 'My Ticket Queue'}
                    </h1>
                    <p className="text-slate-500 mt-1">
                        {isSupervisor ? 'Assign and track team tickets.' : 'Track and resolve assigned tickets.'}
                    </p>
                </div>
                <button
                    onClick={() => refreshTickets(false)}
                    disabled={refreshing}
                    className="bg-slate-900 border border-slate-700 text-slate-200 rounded-sm text-xs font-mono uppercase tracking-wider px-3 py-2 hover:border-blue-500/60 disabled:opacity-50"
                >
                    {refreshing ? 'Refreshing…' : 'Refresh Now'}
                </button>
            </div>

            <DataTable
                data={tickets.map((t) => ({ ...t, id: t.ticket_id }))}
                columns={[
                    {
                        key: 'ticket_id',
                        label: 'Ticket',
                        render: (item: any) => (
                            <div>
                                <div className="text-slate-200 font-mono text-xs">{item.ticket_id.slice(0, 8)}</div>
                                <div className="text-slate-500 text-xs">{item.sender_email}</div>
                            </div>
                        ),
                    },
                    {
                        key: 'subject',
                        label: 'Subject',
                        render: (item: any) => (
                            <div className="text-slate-200 max-w-[280px] truncate">{item.subject || 'No subject'}</div>
                        ),
                    },
                    {
                        key: 'priority_level',
                        label: 'Priority',
                        render: (item: any) => <StatusBadge status={item.priority_level || 'LOW'} />,
                    },
                    {
                        key: 'status',
                        label: 'Status',
                        render: (item: any) => <StatusBadge status={item.status} />,
                    },
                    ...(isSupervisor
                        ? [
                              {
                                  key: 'review',
                                  label: 'Review',
                                  render: (item: any) => {
                                      if (!item.review_required) {
                                          return <span className="text-slate-500 text-xs font-mono">—</span>;
                                      }
                                      const suggested = agents.find((agent) => agent.agent_id === item.suggested_agent_id);
                                      return (
                                          <div className="flex flex-col gap-1">
                                              <StatusBadge status="REVIEW_PENDING" />
                                              <span className="text-[10px] font-mono text-slate-500">
                                                  Suggested: {suggested ? suggested.name : item.suggested_agent_id?.slice(0, 8) || '—'}
                                              </span>
                                              {item.suggested_agent_id && (
                                                  <button
                                                      onClick={(e) => {
                                                          e.stopPropagation();
                                                          handleAssignmentChange(item.ticket_id, item.suggested_agent_id);
                                                      }}
                                                      disabled={assigning === item.ticket_id}
                                                      className="text-[10px] font-mono uppercase tracking-wider text-blue-300 hover:text-blue-200"
                                                  >
                                                      Approve
                                                  </button>
                                              )}
                                          </div>
                                      );
                                  },
                              },
                              {
                                  key: 'assigned_agent_id',
                                  label: 'Agent',
                                  render: (item: any) => (
                                      <select
                                          value={item.assigned_agent_id || ''}
                                          onClick={(e) => e.stopPropagation()}
                                          onChange={(e) => {
                                              e.stopPropagation();
                                              handleAssignmentChange(item.ticket_id, e.target.value);
                                          }}
                                          disabled={assigning === item.ticket_id}
                                          className="bg-slate-950 border border-slate-700 text-slate-200 text-xs font-mono rounded-sm px-2 py-1"
                                      >
                                          <option value="">Unassigned</option>
                                          {agents.map((agent) => (
                                              <option key={agent.agent_id} value={agent.agent_id}>
                                                  {agent.name} {agent.department ? `· ${agent.department}` : ''}
                                              </option>
                                          ))}
                                      </select>
                                  ),
                              },
                          ]
                        : []),
                    {
                        key: 'status_action',
                        label: 'Update',
                        render: (item: any) => (
                            <select
                                value={item.status}
                                onClick={(e) => e.stopPropagation()}
                                onChange={(e) => {
                                    e.stopPropagation();
                                    handleStatusChange(item.ticket_id, e.target.value);
                                }}
                                disabled={updating === item.ticket_id}
                                className="bg-slate-950 border border-slate-700 text-slate-200 text-xs font-mono rounded-sm px-2 py-1"
                            >
                                {STATUS_OPTIONS.map((opt) => (
                                    <option key={opt} value={opt}>{opt.replace('_', ' ')}</option>
                                ))}
                            </select>
                        ),
                    },
                ]}
                onRowClick={(item) => router.push(`/dashboard/agent/tickets/${item.ticket_id}`)}
                emptyMessage="No tickets assigned yet"
            />
        </div>
    );
}
