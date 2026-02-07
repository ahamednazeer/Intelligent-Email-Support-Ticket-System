'use client';

import React, { useEffect } from 'react';
import { BellRinging, X } from '@phosphor-icons/react';

interface ToastProps {
    message: string;
    onClose: () => void;
    actionLabel?: string;
    onAction?: () => void;
    durationMs?: number;
}

export default function Toast({ message, onClose, actionLabel, onAction, durationMs = 6000 }: ToastProps) {
    useEffect(() => {
        const timer = setTimeout(onClose, durationMs);
        return () => clearTimeout(timer);
    }, [message, onClose, durationMs]);

    return (
        <div className="fixed top-6 right-6 z-50 max-w-sm w-[320px]">
            <div className="bg-slate-950/90 border border-slate-700/70 rounded-sm px-4 py-3 shadow-[0_18px_40px_rgba(15,23,42,0.45)] backdrop-blur animate-[slideUp_0.35s_ease]">
                <div className="flex items-start gap-3">
                    <div className="mt-0.5">
                        <BellRinging size={18} weight="duotone" className="text-blue-400" />
                    </div>
                    <div className="flex-1">
                        <div className="text-[10px] font-mono uppercase tracking-widest text-slate-400">New activity</div>
                        <div className="text-sm text-slate-100 mt-1">{message}</div>
                        {actionLabel && onAction && (
                            <button
                                onClick={onAction}
                                className="mt-2 text-xs font-mono uppercase tracking-wider text-blue-300 hover:text-blue-200"
                            >
                                {actionLabel}
                            </button>
                        )}
                    </div>
                    <button
                        onClick={onClose}
                        className="text-slate-500 hover:text-slate-200 transition-colors"
                        aria-label="Dismiss"
                    >
                        <X size={16} />
                    </button>
                </div>
            </div>
        </div>
    );
}
