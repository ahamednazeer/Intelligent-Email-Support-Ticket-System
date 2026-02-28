import React from 'react';

interface StatusBadgeProps {
    status: string;
    className?: string;
}

const statusStyles: Record<string, string> = {
    NEW: 'text-blue-400 bg-blue-950/50 border-blue-800',
    QUEUED: 'text-slate-400 bg-slate-950/50 border-slate-800',
    REVIEW_PENDING: 'text-amber-400 bg-amber-950/50 border-amber-800',
    ASSIGNED: 'text-cyan-400 bg-cyan-950/50 border-cyan-800',
    IN_PROGRESS: 'text-indigo-400 bg-indigo-950/50 border-indigo-800',
    WAITING_FOR_CUSTOMER: 'text-amber-400 bg-amber-950/50 border-amber-800',
    ESCALATED: 'text-red-400 bg-red-950/50 border-red-800',
    RESOLVED: 'text-green-400 bg-green-950/50 border-green-800',
    LOW: 'text-slate-400 bg-slate-950/50 border-slate-800',
    MEDIUM: 'text-blue-400 bg-blue-950/50 border-blue-800',
    HIGH: 'text-amber-400 bg-amber-950/50 border-amber-800',
    CRITICAL: 'text-red-400 bg-red-950/50 border-red-800',
    PASSWORD_RESET: 'text-amber-400 bg-amber-950/50 border-amber-800',
    TICKET_ASSIGNMENT: 'text-cyan-400 bg-cyan-950/50 border-cyan-800',
    USER_STATUS_UPDATE: 'text-indigo-400 bg-indigo-950/50 border-indigo-800',
    TICKET_LABEL_UPDATE: 'text-purple-400 bg-purple-950/50 border-purple-800',
    TICKET_DEDUPE: 'text-amber-400 bg-amber-950/50 border-amber-800',
    AGENT_DELETE: 'text-red-400 bg-red-950/50 border-red-800',
    AGENT_STATUS_UPDATE: 'text-amber-400 bg-amber-950/50 border-amber-800',
    USER_DELETE: 'text-red-400 bg-red-950/50 border-red-800',
    ACTIVE: 'text-green-400 bg-green-950/50 border-green-800',
    INACTIVE: 'text-red-400 bg-red-950/50 border-red-800',
    PENDING: 'text-yellow-400 bg-yellow-950/50 border-yellow-800',
    APPROVED: 'text-green-400 bg-green-950/50 border-green-800',
    REJECTED: 'text-red-400 bg-red-950/50 border-red-800',
    SUCCESS: 'text-green-400 bg-green-950/50 border-green-800',
    FAILED: 'text-red-400 bg-red-950/50 border-red-800',
    PUBLISHED: 'text-blue-400 bg-blue-950/50 border-blue-800',
    DRAFT: 'text-slate-400 bg-slate-950/50 border-slate-800',
    ADMIN: 'text-purple-400 bg-purple-950/50 border-purple-800',
    SUPERVISOR: 'text-indigo-400 bg-indigo-950/50 border-indigo-800',
    BILLING: 'text-cyan-400 bg-cyan-950/50 border-cyan-800',
    TECHNICAL: 'text-blue-400 bg-blue-950/50 border-blue-800',
    ACCOUNT: 'text-indigo-400 bg-indigo-950/50 border-indigo-800',
    COMPLAINT: 'text-red-400 bg-red-950/50 border-red-800',
    FEATURE_REQUEST: 'text-purple-400 bg-purple-950/50 border-purple-800',
    GENERAL: 'text-slate-400 bg-slate-950/50 border-slate-800',
    GOVERNMENT: 'text-emerald-400 bg-emerald-950/50 border-emerald-800',
};

export function StatusBadge({ status, className = '' }: StatusBadgeProps) {
    const style = statusStyles[status] || 'text-slate-400 bg-slate-950/50 border-slate-800';

    return (
        <span
            className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-mono uppercase tracking-wider border ${style} ${className}`}
        >
            {status.replace(/_/g, ' ')}
        </span>
    );
}
