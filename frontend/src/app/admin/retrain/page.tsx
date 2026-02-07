'use client';

import React, { useState } from 'react';
import { api } from '@/lib/api';
import { Brain, Sparkle } from '@phosphor-icons/react';

export default function RetrainPage() {
    const [reason, setReason] = useState('');
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState<string | null>(null);
    const [metrics, setMetrics] = useState<any | null>(null);

    const handleRetrain = async () => {
        setLoading(true);
        setMessage(null);
        setMetrics(null);
        try {
            const result = await api.retrain(reason || undefined);
            setMessage(result.message || 'Retraining queued.');
            if (result.metrics) {
                setMetrics(result.metrics);
            }
        } catch (error: any) {
            setMessage(error.message || 'Failed to start retraining.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-2xl font-chivo font-bold uppercase tracking-wider flex items-center gap-3">
                    <Brain size={28} weight="duotone" className="text-orange-400" />
                    Model Retraining
                </h1>
                <p className="text-slate-500 mt-1">Queue a new retraining job for the classifier pipeline.</p>
            </div>

            <div className="bg-slate-800/40 border border-slate-700/60 rounded-xl p-6 relative overflow-hidden">
                <Sparkle size={80} weight="duotone" className="absolute -right-4 -top-4 text-slate-700/20" />
                <div className="relative z-10 space-y-4">
                    <label className="block text-slate-400 text-xs uppercase tracking-wider font-mono">Reason (optional)</label>
                    <textarea
                        value={reason}
                        onChange={(e) => setReason(e.target.value)}
                        placeholder="Why are you retraining now?"
                        className="w-full bg-slate-950 border border-slate-700 rounded-sm px-3 py-2 text-sm text-slate-100 min-h-[120px]"
                    />
                    <button
                        onClick={handleRetrain}
                        disabled={loading}
                        className="bg-orange-600 hover:bg-orange-500 text-white rounded-sm font-medium tracking-wide uppercase text-xs px-4 py-2 disabled:opacity-50"
                    >
                        {loading ? 'Queuing...' : 'Queue Retraining'}
                    </button>
                    {message && (
                        <div className="text-xs text-slate-300 font-mono bg-slate-950/60 border border-slate-700 rounded-sm p-3">
                            {message}
                        </div>
                    )}
                    {metrics && (
                        <div className="text-xs text-slate-300 font-mono bg-slate-950/60 border border-slate-700 rounded-sm p-3">
                            {JSON.stringify(metrics)}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
