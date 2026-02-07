'use client';

import React from 'react';
import { useParams } from 'next/navigation';
import TicketDetailView from '@/components/TicketDetailView';

export default function AdminTicketDetailPage() {
    const params = useParams();
    const ticketId = params?.ticketId as string;

    if (!ticketId) {
        return <div className="text-slate-400 font-mono text-sm">Ticket not found.</div>;
    }

    return <TicketDetailView ticketId={ticketId} backHref="/admin/tickets" enableAssignment />;
}
