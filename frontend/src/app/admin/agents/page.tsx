'use client';

import React, { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import DataTable from '@/components/DataTable';
import { StatusBadge } from '@/components/StatusBadge';
import { Users, Pulse, PlusCircle } from '@phosphor-icons/react';

interface AgentItem {
    agent_id: string;
    name: string;
    email?: string;
    department?: string;
    skills: string[];
    tier?: string;
    active: boolean;
    workload: number;
}

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

export default function AdminAgentsPage() {
    const [agents, setAgents] = useState<AgentItem[]>([]);
    const [users, setUsers] = useState<UserItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [creating, setCreating] = useState(false);
    const [creatingUser, setCreatingUser] = useState(false);
    const [userMessage, setUserMessage] = useState<string | null>(null);
    const [passwordDrafts, setPasswordDrafts] = useState<Record<string, string>>({});
    const [resetting, setResetting] = useState<Record<string, boolean>>({});
    const [toggling, setToggling] = useState<Record<string, boolean>>({});
    const skillOptions = ['billing', 'technical', 'account', 'complaint', 'feature_request', 'general'];
    const [form, setForm] = useState({
        name: '',
        email: '',
        department: 'Engineering Support',
        skills: ['technical', 'billing', 'account'],
        tier: 'L1',
        active: true,
    });
    const [userForm, setUserForm] = useState({
        username: '',
        password: '',
        full_name: '',
        email: '',
        agent_id: '',
        role: 'TECHNICAL',
    });

    useEffect(() => {
        async function fetchAgents() {
            try {
                const [agentData, userData] = await Promise.all([
                    api.listAgents(),
                    api.listUsers(),
                ]);
                setAgents(agentData || []);
                setUsers(userData || []);
            } catch (error) {
                console.error('Failed to load agents', error);
            } finally {
                setLoading(false);
            }
        }
        fetchAgents();
    }, []);

    const handleCreate = async (e: React.FormEvent) => {
        e.preventDefault();
        setCreating(true);
        try {
            const payload = {
                name: form.name,
                email: form.email || undefined,
                department: form.department,
                skills: form.skills,
                tier: form.tier,
                active: form.active,
            };
            const created = await api.createAgent(payload);
            setAgents((prev) => [created, ...prev]);
            setForm({
                name: '',
                email: '',
                department: 'Engineering Support',
                skills: ['technical', 'billing', 'account'],
                tier: 'L1',
                active: true,
            });
        } catch (error) {
            console.error('Failed to create agent', error);
        } finally {
            setCreating(false);
        }
    };

    const handleCreateUser = async (e: React.FormEvent) => {
        e.preventDefault();
        setCreatingUser(true);
        setUserMessage(null);
        try {
            const payload = {
                username: userForm.username,
                password: userForm.password,
                role: userForm.role,
                full_name: userForm.full_name || undefined,
                email: userForm.email || undefined,
                agent_id: userForm.agent_id || undefined,
                active: true,
            };
            await api.createUser(payload);
            setUserMessage('Agent account created.');
            setUserForm({
                username: '',
                password: '',
                full_name: '',
                email: '',
                agent_id: '',
                role: 'TECHNICAL',
            });
            const updatedAgents = await api.listAgents();
            setAgents(updatedAgents || []);
            const updatedUsers = await api.listUsers();
            setUsers(updatedUsers || []);
        } catch (error: any) {
            setUserMessage(error.message || 'Failed to create agent account.');
        } finally {
            setCreatingUser(false);
        }
    };

    const handleReset = async (userId: string) => {
        const newPassword = passwordDrafts[userId];
        if (!newPassword) return;
        setResetting((prev) => ({ ...prev, [userId]: true }));
        setUserMessage(null);
        try {
            await api.resetUserPassword(userId, newPassword);
            setUserMessage('Password updated successfully.');
            setPasswordDrafts((prev) => ({ ...prev, [userId]: '' }));
        } catch (error: any) {
            setUserMessage(error.message || 'Failed to reset password.');
        } finally {
            setResetting((prev) => ({ ...prev, [userId]: false }));
        }
    };

    const handleToggleAgent = async (agentId: string, nextActive: boolean) => {
        const agentUser = users.find((u) => u.agent_id === agentId);
        const message = nextActive
            ? 'Reactivate this agent and linked login?'
            : agentUser
                ? 'Deactivate this agent and linked login?'
                : 'Deactivate this agent?';
        const confirmed = typeof window === 'undefined' ? true : window.confirm(message);
        if (!confirmed) return;
        setToggling((prev) => ({ ...prev, [agentId]: true }));
        setUserMessage(null);
        try {
            const result = await api.updateAgentActive(agentId, nextActive);
            setAgents((prev) =>
                prev.map((agent) =>
                    agent.agent_id === agentId ? { ...agent, active: result.active } : agent
                )
            );
            setUsers((prev) =>
                prev.map((user) =>
                    user.agent_id === agentId ? { ...user, active: result.active } : user
                )
            );
            setUserMessage(`Agent ${nextActive ? 'activated' : 'deactivated'}.`);
        } catch (error: any) {
            setUserMessage(error.message || 'Failed to update agent status.');
        } finally {
            setToggling((prev) => ({ ...prev, [agentId]: false }));
        }
    };

    if (loading) {
        return (
            <div className="flex flex-col items-center justify-center h-64 gap-4">
                <div className="relative">
                    <div className="w-12 h-12 rounded-full border-2 border-slate-700 border-t-purple-500 animate-spin" />
                    <Pulse size={24} className="absolute inset-0 m-auto text-purple-400 animate-pulse" />
                </div>
                <p className="text-slate-500 font-mono text-xs uppercase tracking-widest animate-pulse">
                    Loading Agents...
                </p>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between flex-wrap gap-4">
                <div>
                    <h1 className="text-2xl font-chivo font-bold uppercase tracking-wider flex items-center gap-3">
                        <Users size={28} weight="duotone" className="text-purple-400" />
                        Agent Directory
                    </h1>
                    <p className="text-slate-500 mt-1">Manage routing capacity and agent skills.</p>
                </div>
            </div>

            {userMessage && (
                <div className="text-xs text-slate-300 font-mono bg-slate-950/60 border border-slate-700 rounded-sm p-3">
                    {userMessage}
                </div>
            )}

            <form onSubmit={handleCreateUser} className="bg-slate-800/40 border border-slate-700/60 rounded-xl p-6 space-y-4">
                <div className="flex items-center gap-2 text-sm font-mono uppercase tracking-widest text-slate-400">
                    <PlusCircle size={16} /> Create Agent Login (auto links profile)
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <input
                        value={userForm.username}
                        onChange={(e) => setUserForm({ ...userForm, username: e.target.value })}
                        placeholder="Username"
                        className="bg-slate-950 border border-slate-700 rounded-sm px-3 py-2 text-sm text-slate-100"
                        required
                    />
                    <input
                        value={userForm.password}
                        onChange={(e) => setUserForm({ ...userForm, password: e.target.value })}
                        placeholder="Temporary Password"
                        className="bg-slate-950 border border-slate-700 rounded-sm px-3 py-2 text-sm text-slate-100"
                        required
                    />
                    <select
                        value={userForm.role}
                        onChange={(e) => setUserForm({ ...userForm, role: e.target.value })}
                        className="bg-slate-950 border border-slate-700 rounded-sm px-3 py-2 text-xs font-mono text-slate-100"
                    >
                        {skillOptions.map((skill) => (
                            <option key={skill} value={skill.toUpperCase()}>
                                {skill.replace('_', ' ').toUpperCase()}
                            </option>
                        ))}
                    </select>
                    <input
                        value={userForm.full_name}
                        onChange={(e) => setUserForm({ ...userForm, full_name: e.target.value })}
                        placeholder="Full name"
                        className="bg-slate-950 border border-slate-700 rounded-sm px-3 py-2 text-sm text-slate-100"
                    />
                    <input
                        value={userForm.email}
                        onChange={(e) => setUserForm({ ...userForm, email: e.target.value })}
                        placeholder="Email"
                        className="bg-slate-950 border border-slate-700 rounded-sm px-3 py-2 text-sm text-slate-100"
                    />
                    <select
                        value={userForm.agent_id}
                        onChange={(e) => setUserForm({ ...userForm, agent_id: e.target.value })}
                        className="bg-slate-950 border border-slate-700 rounded-sm px-3 py-2 text-xs font-mono text-slate-100 md:col-span-2"
                    >
                        <option value="">Auto-create agent profile</option>
                        {agents.map((agent) => (
                            <option key={agent.agent_id} value={agent.agent_id}>
                                Link to {agent.name} ({agent.agent_id.slice(0, 8)})
                            </option>
                        ))}
                    </select>
                </div>
                <button
                    type="submit"
                    disabled={creatingUser}
                    className="bg-blue-600 hover:bg-blue-500 text-white rounded-sm font-medium tracking-wide uppercase text-xs px-4 py-2 disabled:opacity-50"
                >
                    {creatingUser ? 'Creating...' : 'Create Agent Account'}
                </button>
                {userMessage && (
                    <div className="text-xs text-slate-300 font-mono bg-slate-950/60 border border-slate-700 rounded-sm p-3">
                        {userMessage}
                    </div>
                )}
            </form>

            <form onSubmit={handleCreate} className="bg-slate-800/40 border border-slate-700/60 rounded-xl p-6 space-y-4">
                <div className="flex items-center gap-2 text-sm font-mono uppercase tracking-widest text-slate-400">
                    <PlusCircle size={16} /> Add Agent Profile (no login)
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <input
                        value={form.name}
                        onChange={(e) => setForm({ ...form, name: e.target.value })}
                        placeholder="Full name"
                        className="bg-slate-950 border border-slate-700 rounded-sm px-3 py-2 text-sm text-slate-100"
                        required
                    />
                    <input
                        value={form.email}
                        onChange={(e) => setForm({ ...form, email: e.target.value })}
                        placeholder="Email"
                        className="bg-slate-950 border border-slate-700 rounded-sm px-3 py-2 text-sm text-slate-100"
                    />
                    <input
                        value={form.department}
                        onChange={(e) => setForm({ ...form, department: e.target.value })}
                        placeholder="Department"
                        className="bg-slate-950 border border-slate-700 rounded-sm px-3 py-2 text-sm text-slate-100"
                    />
                    <input
                        value={form.tier}
                        onChange={(e) => setForm({ ...form, tier: e.target.value })}
                        placeholder="Tier (L1/L2)"
                        className="bg-slate-950 border border-slate-700 rounded-sm px-3 py-2 text-sm text-slate-100"
                    />
                    <div className="md:col-span-2">
                        <div className="text-xs font-mono uppercase tracking-widest text-slate-500 mb-2">
                            Category Roles
                        </div>
                        <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                            {skillOptions.map((skill) => {
                                const checked = form.skills.includes(skill);
                                return (
                                    <label
                                        key={skill}
                                        className={`flex items-center gap-2 border rounded-sm px-3 py-2 text-xs font-mono uppercase tracking-wider ${
                                            checked
                                                ? 'border-blue-500/70 text-blue-200 bg-blue-950/40'
                                                : 'border-slate-700 text-slate-400 bg-slate-950/40'
                                        }`}
                                    >
                                        <input
                                            type="checkbox"
                                            checked={checked}
                                            onChange={(e) => {
                                                const next = e.target.checked
                                                    ? [...form.skills, skill]
                                                    : form.skills.filter((s) => s !== skill);
                                                setForm({ ...form, skills: next });
                                            }}
                                            className="accent-blue-500"
                                        />
                                        {skill.replace('_', ' ')}
                                    </label>
                                );
                            })}
                        </div>
                    </div>
                </div>
                <button
                    type="submit"
                    disabled={creating}
                    className="bg-purple-600 hover:bg-purple-500 text-white rounded-sm font-medium tracking-wide uppercase text-xs px-4 py-2 disabled:opacity-50"
                >
                    {creating ? 'Creating...' : 'Add Agent'}
                </button>
            </form>

            <DataTable
                data={agents.map((a) => ({ ...a, id: a.agent_id }))}
                columns={[
                    { key: 'name', label: 'Agent' },
                    { key: 'department', label: 'Department' },
                    {
                        key: 'skills',
                        label: 'Skills',
                        render: (item: any) => (
                            <div className="text-slate-400 text-xs font-mono">{(item.skills || []).join(', ')}</div>
                        ),
                    },
                    { key: 'tier', label: 'Tier' },
                    { key: 'workload', label: 'Workload' },
                    {
                        key: 'active',
                        label: 'Status',
                        render: (item: any) => <StatusBadge status={item.active ? 'ACTIVE' : 'INACTIVE'} />,
                    },
                    {
                        key: 'account',
                        label: 'Account',
                        render: (item: any) => {
                            const user = users.find((u) => u.agent_id === item.agent_id);
                            if (!user) {
                                return <span className="text-xs font-mono text-slate-500">No login</span>;
                            }
                            return (
                                <div className="text-xs font-mono text-slate-300">
                                    <div>{user.username}</div>
                                    <div className="text-slate-500">{user.role}</div>
                                </div>
                            );
                        },
                    },
                    {
                        key: 'reset',
                        label: 'Reset Password',
                        render: (item: any) => {
                            const user = users.find((u) => u.agent_id === item.agent_id);
                            if (!user) {
                                return <span className="text-xs font-mono text-slate-500">—</span>;
                            }
                            return (
                                <div className="flex items-center gap-2">
                                    <input
                                        value={passwordDrafts[user.user_id] || ''}
                                        onChange={(e) =>
                                            setPasswordDrafts((prev) => ({ ...prev, [user.user_id]: e.target.value }))
                                        }
                                        placeholder="New password"
                                        className="bg-slate-950 border border-slate-700 rounded-sm px-2 py-1 text-xs text-slate-100"
                                    />
                                    <button
                                        onClick={() => handleReset(user.user_id)}
                                        disabled={resetting[user.user_id] || !(passwordDrafts[user.user_id] || '').trim()}
                                        className="bg-blue-600 hover:bg-blue-500 text-white rounded-sm font-medium tracking-wide uppercase text-[10px] px-2 py-1 disabled:opacity-50"
                                    >
                                        {resetting[user.user_id] ? 'Resetting...' : 'Reset'}
                                    </button>
                                </div>
                            );
                        },
                    },
                    {
                        key: 'status_action',
                        label: 'Agent Status',
                        render: (item: any) => (
                            <button
                                onClick={() => handleToggleAgent(item.agent_id, !item.active)}
                                disabled={toggling[item.agent_id]}
                                className={`rounded-sm text-[10px] px-2 py-1 uppercase tracking-wider disabled:opacity-50 ${
                                    item.active
                                        ? 'bg-red-950/60 border border-red-700/60 text-red-300'
                                        : 'bg-emerald-950/60 border border-emerald-700/60 text-emerald-300'
                                }`}
                            >
                                {toggling[item.agent_id]
                                    ? 'Updating...'
                                    : item.active
                                        ? 'Deactivate'
                                        : 'Activate'}
                            </button>
                        ),
                    },
                ]}
                emptyMessage="No agents available"
            />
        </div>
    );
}
