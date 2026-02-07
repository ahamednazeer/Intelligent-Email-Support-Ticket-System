'use client';

import React, { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import DataTable from '@/components/DataTable';
import { StatusBadge } from '@/components/StatusBadge';
import { Users, Pulse } from '@phosphor-icons/react';

interface UserItem {
    user_id: string;
    username: string;
    role: string;
    full_name?: string;
    email?: string;
    agent_id?: string;
    active: boolean;
    created_at: string;
}

export default function AdminUsersPage() {
    const [users, setUsers] = useState<UserItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [passwordDrafts, setPasswordDrafts] = useState<Record<string, string>>({});
    const [resetting, setResetting] = useState<Record<string, boolean>>({});
    const [message, setMessage] = useState<string | null>(null);

    useEffect(() => {
        async function fetchUsers() {
            try {
                const data = await api.listUsers();
                setUsers(data || []);
            } catch (error) {
                console.error('Failed to load users', error);
            } finally {
                setLoading(false);
            }
        }
        fetchUsers();
    }, []);

    const handleReset = async (userId: string) => {
        const newPassword = passwordDrafts[userId];
        if (!newPassword) return;
        setResetting((prev) => ({ ...prev, [userId]: true }));
        setMessage(null);
        try {
            await api.resetUserPassword(userId, newPassword);
            setMessage('Password updated successfully.');
            setPasswordDrafts((prev) => ({ ...prev, [userId]: '' }));
        } catch (error: any) {
            setMessage(error.message || 'Failed to reset password.');
        } finally {
            setResetting((prev) => ({ ...prev, [userId]: false }));
        }
    };

    const handleToggleActive = async (userId: string, nextActive: boolean) => {
        setMessage(null);
        try {
            const updated = await api.updateUserActive(userId, nextActive);
            setUsers((prev) => prev.map((u) => (u.user_id === userId ? updated : u)));
            setMessage(`User ${nextActive ? 'activated' : 'deactivated'}.`);
        } catch (error: any) {
            setMessage(error.message || 'Failed to update user status.');
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
                    Loading Users...
                </p>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-2xl font-chivo font-bold uppercase tracking-wider flex items-center gap-3">
                    <Users size={28} weight="duotone" className="text-blue-400" />
                    User Directory
                </h1>
                <p className="text-slate-500 mt-1">Manage logins and reset credentials.</p>
            </div>

            {message && (
                <div className="text-xs text-slate-300 font-mono bg-slate-950/60 border border-slate-700 rounded-sm p-3">
                    {message}
                </div>
            )}

            <DataTable
                data={users.map((u) => ({ ...u, id: u.user_id }))}
                columns={[
                    {
                        key: 'username',
                        label: 'User',
                        render: (item: any) => (
                            <div>
                                <div className="text-slate-200 font-mono text-xs">{item.username}</div>
                                <div className="text-slate-500 text-xs">{item.email || '—'}</div>
                            </div>
                        ),
                    },
                    { key: 'role', label: 'Role', render: (item: any) => <StatusBadge status={item.role} /> },
                    {
                        key: 'agent_id',
                        label: 'Agent Id',
                        render: (item: any) => (
                            <div className="text-slate-400 text-xs font-mono">{item.agent_id || '—'}</div>
                        ),
                    },
                    {
                        key: 'active',
                        label: 'Status',
                        render: (item: any) => (
                            <div className="flex items-center gap-2">
                                <StatusBadge status={item.active ? 'ACTIVE' : 'INACTIVE'} />
                                <button
                                    onClick={() => handleToggleActive(item.user_id, !item.active)}
                                    className="bg-slate-900 border border-slate-700 text-slate-200 rounded-sm text-[10px] px-2 py-1 uppercase tracking-wider"
                                >
                                    {item.active ? 'Deactivate' : 'Activate'}
                                </button>
                            </div>
                        ),
                    },
                    {
                        key: 'reset',
                        label: 'Reset Password',
                        render: (item: any) => (
                            <div className="flex items-center gap-2">
                                <input
                                    value={passwordDrafts[item.user_id] || ''}
                                    onChange={(e) =>
                                        setPasswordDrafts((prev) => ({ ...prev, [item.user_id]: e.target.value }))
                                    }
                                    placeholder="New password"
                                    className="bg-slate-950 border border-slate-700 rounded-sm px-2 py-1 text-xs text-slate-100"
                                />
                                <button
                                    onClick={() => handleReset(item.user_id)}
                                    disabled={resetting[item.user_id] || !(passwordDrafts[item.user_id] || '').trim()}
                                    className="bg-blue-600 hover:bg-blue-500 text-white rounded-sm font-medium tracking-wide uppercase text-[10px] px-2 py-1 disabled:opacity-50"
                                >
                                    {resetting[item.user_id] ? 'Resetting...' : 'Reset'}
                                </button>
                            </div>
                        ),
                    },
                ]}
                emptyMessage="No users found"
            />
        </div>
    );
}
