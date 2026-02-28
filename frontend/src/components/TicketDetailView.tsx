'use client';

import React, { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { StatusBadge } from '@/components/StatusBadge';
import { ArrowLeft, ChatCircle, Pulse, Sparkle, ClipboardText } from '@phosphor-icons/react';
import Link from 'next/link';

interface TicketDetailViewProps {
    ticketId: string;
    backHref: string;
    enableAssignment?: boolean;
}

interface TicketItem {
    ticket_id: string;
    sender_email: string;
    subject?: string;
    body: string;
    status: string;
    priority_level?: string;
    category?: string;
    subcategory?: string;
    intent_label?: string;
    confidence_score?: number;
    urgency_score?: number;
    sla_deadline?: string;
    assigned_agent_id?: string;
    department?: string;
    suggested_agent_id?: string;
    review_required?: boolean;
    created_at: string;
    resolution_notes?: string | null;
    label_category?: string | null;
    label_subcategory?: string | null;
    label_intent?: string | null;
    label_updated_at?: string | null;
}

interface ResponseItem {
    response_id: number;
    ticket_id: string;
    author_username: string;
    author_role: string;
    message: string;
    is_internal: boolean;
    created_at: string;
}

const STATUS_OPTIONS = [
    'NEW',
    'QUEUED',
    'REVIEW_PENDING',
    'ASSIGNED',
    'IN_PROGRESS',
    'WAITING_FOR_CUSTOMER',
    'ESCALATED',
    'RESOLVED',
];
const CATEGORY_OPTIONS = ['billing', 'technical', 'account', 'complaint', 'feature_request', 'government', 'general'];

interface AgentItem {
    agent_id: string;
    name: string;
    department?: string;
    active: boolean;
}

export default function TicketDetailView({ ticketId, backHref, enableAssignment = false }: TicketDetailViewProps) {
    const [ticket, setTicket] = useState<TicketItem | null>(null);
    const [responses, setResponses] = useState<ResponseItem[]>([]);
    const [agents, setAgents] = useState<AgentItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [message, setMessage] = useState('');
    const [status, setStatus] = useState('IN_PROGRESS');
    const [resolutionNotes, setResolutionNotes] = useState('');
    const [isInternal, setIsInternal] = useState(false);
    const [submitting, setSubmitting] = useState(false);
    const [selectedAgentId, setSelectedAgentId] = useState('');
    const [assigning, setAssigning] = useState(false);
    const [labelCategory, setLabelCategory] = useState('general');
    const [labelSubcategory, setLabelSubcategory] = useState('');
    const [labelIntent, setLabelIntent] = useState('');
    const [labelSaving, setLabelSaving] = useState(false);
    const [labelMessage, setLabelMessage] = useState<string | null>(null);
    const suggestedAgent = agents.find((agent) => agent.agent_id === ticket?.suggested_agent_id);

    useEffect(() => {
        async function fetchDetail() {
            try {
                const [ticketData, responseData] = await Promise.all([
                    api.getTicket(ticketId),
                    api.listTicketResponses(ticketId),
                ]);
                setTicket(ticketData);
                setResponses(responseData || []);
                setStatus(ticketData.status || 'IN_PROGRESS');
                setResolutionNotes(ticketData.resolution_notes || '');
                setSelectedAgentId(ticketData.assigned_agent_id || '');
                setLabelCategory(ticketData.label_category || ticketData.category || 'general');
                setLabelSubcategory(ticketData.label_subcategory || ticketData.subcategory || '');
                setLabelIntent(ticketData.label_intent || ticketData.intent_label || '');

                if (enableAssignment) {
                    const agentData = await api.listAgents();
                    setAgents(agentData || []);
                }
            } catch (error) {
                console.error('Failed to load ticket', error);
            } finally {
                setLoading(false);
            }
        }
        fetchDetail();
    }, [ticketId, enableAssignment]);

    const handleSubmit = async () => {
        if (!message.trim()) return;
        setSubmitting(true);
        try {
            const payload = {
                message,
                status,
                resolution_notes: resolutionNotes || undefined,
                is_internal: isInternal,
            };
            const created = await api.addTicketResponse(ticketId, payload);
            setResponses((prev) => [...prev, created]);
            setMessage('');
            const updatedTicket = await api.getTicket(ticketId);
            setTicket(updatedTicket);
        } catch (error) {
            console.error('Failed to send response', error);
        } finally {
            setSubmitting(false);
        }
    };

    const handleAssign = async () => {
        setAssigning(true);
        try {
            const updated = await api.assignTicket(ticketId, selectedAgentId || null);
            setTicket(updated);
        } catch (error) {
            console.error('Failed to assign ticket', error);
        } finally {
            setAssigning(false);
        }
    };

    const handleApproveSuggestion = async () => {
        if (!ticket?.suggested_agent_id) return;
        setAssigning(true);
        try {
            const updated = await api.assignTicket(ticketId, ticket.suggested_agent_id);
            setTicket(updated);
            setSelectedAgentId(updated.assigned_agent_id || '');
        } catch (error) {
            console.error('Failed to approve suggestion', error);
        } finally {
            setAssigning(false);
        }
    };

    const handleSaveLabel = async () => {
        setLabelSaving(true);
        setLabelMessage(null);
        try {
            const updated = await api.updateTicketLabel(ticketId, {
                label_category: labelCategory,
                label_subcategory: labelSubcategory || undefined,
                label_intent: labelIntent || undefined,
            });
            setTicket(updated);
            setLabelMessage('Label saved.');
        } catch (error: any) {
            setLabelMessage(error.message || 'Failed to save label.');
        } finally {
            setLabelSaving(false);
        }
    };

    if (loading) {
        return (
            <div className="flex flex-col items-center justify-center h-64 gap-4">
                <div className="relative">
                    <div className="w-12 h-12 rounded-full border-2 border-slate-700 border-t-blue-500 animate-spin" />
                    <Pulse size={24} className="absolute inset-0 m-auto text-blue-400 animate-pulse" />
                </div>
                <p className="text-slate-500 font-mono text-xs uppercase tracking-widest animate-pulse">
                    Loading Ticket...
                </p>
            </div>
        );
    }

    if (!ticket) {
        return (
            <div className="text-slate-400 font-mono text-sm">Ticket not found.</div>
        );
    }

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between flex-wrap gap-4">
                <div>
                    <Link href={backHref} className="inline-flex items-center gap-2 text-blue-400 text-sm font-mono hover:text-blue-300">
                        <ArrowLeft size={16} /> Back to tickets
                    </Link>
                    <h1 className="text-2xl font-chivo font-bold uppercase tracking-wider mt-2">Ticket {ticket.ticket_id.slice(0, 8)}</h1>
                    <p className="text-slate-500 mt-1">{ticket.subject || 'No subject'}</p>
                </div>
                <div className="flex items-center gap-2">
                    <StatusBadge status={ticket.priority_level || 'LOW'} />
                    <StatusBadge status={ticket.status} />
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2 space-y-6">
                    <div className="bg-slate-800/40 border border-slate-700/60 rounded-xl p-6 relative overflow-hidden">
                        <Sparkle size={80} weight="duotone" className="absolute -right-4 -top-4 text-slate-700/20" />
                        <h3 className="text-sm font-mono text-slate-400 uppercase tracking-widest mb-4 flex items-center gap-2">
                            <ChatCircle size={16} weight="duotone" />
                            Ticket Detail
                        </h3>
                        <div className="space-y-3 text-sm text-slate-300">
                            <div><span className="text-slate-500 font-mono">From:</span> {ticket.sender_email}</div>
                            <div><span className="text-slate-500 font-mono">Department:</span> {ticket.department || 'General'}</div>
                            <div><span className="text-slate-500 font-mono">Category:</span> {ticket.category || 'general'} / {ticket.subcategory || 'general'}</div>
                            <div><span className="text-slate-500 font-mono">Intent:</span> {ticket.intent_label || 'general'}</div>
                            <div><span className="text-slate-500 font-mono">Confidence:</span> {ticket.confidence_score ?? 0}</div>
                            <div><span className="text-slate-500 font-mono">Urgency:</span> {ticket.urgency_score ?? 0}</div>
                            <div><span className="text-slate-500 font-mono">SLA Deadline:</span> {ticket.sla_deadline || '—'}</div>
                            <div><span className="text-slate-500 font-mono">Assigned Agent:</span> {ticket.assigned_agent_id || '—'}</div>
                            <div><span className="text-slate-500 font-mono">Review Required:</span> {ticket.review_required ? 'Yes' : 'No'}</div>
                            <div>
                                <span className="text-slate-500 font-mono">Suggested Agent:</span>{' '}
                                {suggestedAgent ? suggestedAgent.name : ticket.suggested_agent_id || '—'}
                            </div>
                        </div>
                        <div className="mt-4 bg-slate-950/60 border border-slate-800 rounded-sm p-4 text-sm text-slate-200 whitespace-pre-line">
                            {ticket.body}
                        </div>
                    </div>

                    <div className="bg-slate-800/40 border border-slate-700/60 rounded-xl p-6">
                        <h3 className="text-sm font-mono text-slate-400 uppercase tracking-widest mb-4 flex items-center gap-2">
                            <ClipboardText size={16} weight="duotone" />
                            Responses
                        </h3>
                        <div className="space-y-3">
                            {responses.length === 0 && (
                                <div className="text-slate-500 text-sm font-mono">No responses yet.</div>
                            )}
                            {responses.map((resp) => (
                                <div key={resp.response_id} className="bg-slate-950/60 border border-slate-800 rounded-sm p-4">
                                    <div className="flex items-center justify-between text-xs text-slate-500 font-mono uppercase tracking-wider">
                                        <span>{resp.author_role} · {resp.author_username}</span>
                                        <span>{new Date(resp.created_at).toLocaleString()}</span>
                                    </div>
                                    <p className="text-slate-200 text-sm mt-2 whitespace-pre-line">{resp.message}</p>
                                    {resp.is_internal && (
                                        <div className="mt-2 text-[10px] font-mono uppercase tracking-wider text-amber-400">Internal Note</div>
                                    )}
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                <div className="space-y-6">
                    {enableAssignment && (
                        <div className="bg-slate-800/40 border border-slate-700/60 rounded-xl p-6">
                            <h3 className="text-sm font-mono text-slate-400 uppercase tracking-widest mb-4">Assign Agent</h3>
                            <div className="space-y-3">
                                {ticket.review_required && ticket.suggested_agent_id && (
                                    <div className="bg-slate-950/60 border border-slate-800 rounded-sm p-3 text-xs text-slate-200 space-y-2">
                                        <div className="font-mono uppercase tracking-widest text-slate-500">Review Pending</div>
                                        <div className="text-slate-300">
                                            Suggested: {suggestedAgent ? suggestedAgent.name : ticket.suggested_agent_id}
                                        </div>
                                        <button
                                            onClick={handleApproveSuggestion}
                                            disabled={assigning}
                                            className="text-[11px] font-mono uppercase tracking-wider text-blue-300 hover:text-blue-200"
                                        >
                                            Approve Suggested Assignment
                                        </button>
                                    </div>
                                )}
                                <select
                                    value={selectedAgentId}
                                    onChange={(e) => setSelectedAgentId(e.target.value)}
                                    className="w-full bg-slate-950 border border-slate-700 text-slate-200 text-xs font-mono rounded-sm px-2 py-2"
                                >
                                    <option value="">Unassigned</option>
                                    {agents.map((agent) => (
                                        <option key={agent.agent_id} value={agent.agent_id}>
                                            {agent.name} {agent.department ? `· ${agent.department}` : ''}
                                        </option>
                                    ))}
                                </select>
                                <button
                                    onClick={handleAssign}
                                    disabled={assigning}
                                    className="w-full bg-purple-600 hover:bg-purple-500 text-white rounded-sm font-medium tracking-wide uppercase text-xs px-4 py-2 disabled:opacity-50"
                                >
                                    {assigning ? 'Saving...' : 'Save Assignment'}
                                </button>
                            </div>
                        </div>
                    )}
                    {enableAssignment && (
                        <div className="bg-slate-800/40 border border-slate-700/60 rounded-xl p-6">
                            <h3 className="text-sm font-mono text-slate-400 uppercase tracking-widest mb-4">Label Ticket</h3>
                            <div className="space-y-3">
                                <select
                                    value={labelCategory}
                                    onChange={(e) => setLabelCategory(e.target.value)}
                                    className="w-full bg-slate-950 border border-slate-700 text-slate-200 text-xs font-mono rounded-sm px-2 py-2"
                                >
                                    {CATEGORY_OPTIONS.map((opt) => (
                                        <option key={opt} value={opt}>{opt.replace('_', ' ')}</option>
                                    ))}
                                </select>
                                <input
                                    value={labelSubcategory}
                                    onChange={(e) => setLabelSubcategory(e.target.value)}
                                    placeholder="Subcategory (optional)"
                                    className="w-full bg-slate-950 border border-slate-700 rounded-sm px-3 py-2 text-xs text-slate-100"
                                />
                                <input
                                    value={labelIntent}
                                    onChange={(e) => setLabelIntent(e.target.value)}
                                    placeholder="Intent label (optional)"
                                    className="w-full bg-slate-950 border border-slate-700 rounded-sm px-3 py-2 text-xs text-slate-100"
                                />
                                <button
                                    onClick={handleSaveLabel}
                                    disabled={labelSaving}
                                    className="w-full bg-indigo-600 hover:bg-indigo-500 text-white rounded-sm font-medium tracking-wide uppercase text-xs px-4 py-2 disabled:opacity-50"
                                >
                                    {labelSaving ? 'Saving...' : 'Save Label'}
                                </button>
                                {labelMessage && (
                                    <div className="text-xs text-slate-300 font-mono bg-slate-950/60 border border-slate-700 rounded-sm p-3">
                                        {labelMessage}
                                    </div>
                                )}
                            </div>
                        </div>
                    )}
                    <div className="bg-slate-800/40 border border-slate-700/60 rounded-xl p-6">
                        <h3 className="text-sm font-mono text-slate-400 uppercase tracking-widest mb-4">Send Response</h3>
                        <div className="space-y-3">
                            <textarea
                                value={message}
                                onChange={(e) => setMessage(e.target.value)}
                                placeholder="Type your response..."
                                className="w-full bg-slate-950 border border-slate-700 rounded-sm px-3 py-2 text-sm text-slate-100 min-h-[140px]"
                            />
                            <label className="block text-xs font-mono uppercase tracking-wider text-slate-500">Update Status</label>
                            <select
                                value={status}
                                onChange={(e) => setStatus(e.target.value)}
                                className="w-full bg-slate-950 border border-slate-700 text-slate-200 text-xs font-mono rounded-sm px-2 py-2"
                            >
                                {STATUS_OPTIONS.map((opt) => (
                                    <option key={opt} value={opt}>{opt.replace('_', ' ')}</option>
                                ))}
                            </select>
                            <label className="block text-xs font-mono uppercase tracking-wider text-slate-500">Resolution Notes</label>
                            <textarea
                                value={resolutionNotes}
                                onChange={(e) => setResolutionNotes(e.target.value)}
                                placeholder="Optional resolution notes..."
                                className="w-full bg-slate-950 border border-slate-700 rounded-sm px-3 py-2 text-xs text-slate-100 min-h-[100px]"
                            />
                            <label className="flex items-center gap-2 text-xs font-mono uppercase tracking-wider text-slate-500">
                                <input
                                    type="checkbox"
                                    checked={isInternal}
                                    onChange={(e) => setIsInternal(e.target.checked)}
                                    className="accent-blue-500"
                                />
                                Internal Note
                            </label>
                            <button
                                onClick={handleSubmit}
                                disabled={submitting}
                                className="w-full bg-blue-600 hover:bg-blue-500 text-white rounded-sm font-medium tracking-wide uppercase text-xs px-4 py-2 disabled:opacity-50"
                            >
                                {submitting ? 'Sending...' : 'Send Response'}
                            </button>
                        </div>
                    </div>

                    {ticket.resolution_notes && (
                        <div className="bg-slate-800/40 border border-slate-700/60 rounded-xl p-6">
                            <h3 className="text-sm font-mono text-slate-400 uppercase tracking-widest mb-3">Resolution Notes</h3>
                            <p className="text-slate-200 text-sm whitespace-pre-line">{ticket.resolution_notes}</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
