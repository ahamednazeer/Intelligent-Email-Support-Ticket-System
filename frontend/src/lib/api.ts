const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class ApiClient {
    private token: string | null = null;

    setToken(token: string) {
        this.token = token;
        if (typeof window !== 'undefined') {
            localStorage.setItem('token', token);
        }
    }

    getToken() {
        if (!this.token && typeof window !== 'undefined') {
            this.token = localStorage.getItem('token');
        }
        return this.token;
    }

    clearToken() {
        this.token = null;
        if (typeof window !== 'undefined') {
            localStorage.removeItem('token');
        }
    }

    private async request(endpoint: string, options: RequestInit = {}) {
        const token = this.getToken();
        const headers: Record<string, string> = {
            'Content-Type': 'application/json',
            ...(options.headers as Record<string, string>),
        };

        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        const response = await fetch(`${API_URL}${endpoint}`, {
            ...options,
            headers,
            cache: 'no-store',
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: 'Request failed' }));
            throw new Error(error.detail || error.message || 'Request failed');
        }

        return response.json();
    }

    // Auth
    async login(username: string, password: string) {
        const data = await this.request('/auth/login', {
            method: 'POST',
            body: JSON.stringify({ username, password }),
        });
        this.setToken(data.access_token);
        return data;
    }

    async getMe() {
        return this.request('/auth/me');
    }

    // Tickets
    async listTickets(params: { status?: string; priority?: string; assigned_agent_id?: string } = {}) {
        const query = new URLSearchParams();
        if (params.status) query.set('status', params.status);
        if (params.priority) query.set('priority', params.priority);
        if (params.assigned_agent_id) query.set('assigned_agent_id', params.assigned_agent_id);
        const qs = query.toString();
        return this.request(`/tickets${qs ? `?${qs}` : ''}`);
    }

    async getTicket(ticketId: string) {
        return this.request(`/tickets/${ticketId}`);
    }

    async listTicketResponses(ticketId: string) {
        return this.request(`/tickets/${ticketId}/responses`);
    }

    async addTicketResponse(ticketId: string, payload: any) {
        return this.request(`/tickets/${ticketId}/responses`, {
            method: 'POST',
            body: JSON.stringify(payload),
        });
    }

    async updateTicketLabel(ticketId: string, payload: { label_category: string; label_subcategory?: string; label_intent?: string }) {
        return this.request(`/tickets/${ticketId}/label`, {
            method: 'POST',
            body: JSON.stringify(payload),
        });
    }

    async updateTicketStatus(ticketId: string, status: string, resolution_notes?: string) {
        return this.request(`/tickets/${ticketId}/status`, {
            method: 'POST',
            body: JSON.stringify({ status, resolution_notes }),
        });
    }

    async assignTicket(ticketId: string, agent_id?: string | null) {
        return this.request(`/tickets/${ticketId}/assign`, {
            method: 'POST',
            body: JSON.stringify({ agent_id: agent_id ?? null }),
        });
    }

    async ingestTicket(payload: any) {
        return this.request('/ingest/portal', {
            method: 'POST',
            body: JSON.stringify(payload),
        });
    }

    // Agents (admin)
    async listAgents() {
        return this.request('/agents');
    }

    async createAgent(payload: any) {
        return this.request('/agents', {
            method: 'POST',
            body: JSON.stringify(payload),
        });
    }

    async deleteAgent(agent_id: string) {
        return this.request(`/agents/${agent_id}`, { method: 'DELETE' });
    }

    async updateAgentActive(agent_id: string, active: boolean) {
        return this.request(`/agents/${agent_id}/active`, {
            method: 'POST',
            body: JSON.stringify({ active }),
        });
    }

    // Analytics (admin)
    async getAnalyticsSummary() {
        return this.request('/analytics/summary');
    }

    async retrain(reason?: string) {
        const query = reason ? `?reason=${encodeURIComponent(reason)}` : '';
        return this.request(`/retrain${query}`, { method: 'POST' });
    }

    // Users (admin)
    async listUsers() {
        return this.request('/users');
    }

    async createUser(payload: any) {
        return this.request('/users', {
            method: 'POST',
            body: JSON.stringify(payload),
        });
    }

    async resetUserPassword(user_id: string, new_password: string) {
        return this.request(`/users/${user_id}/password`, {
            method: 'POST',
            body: JSON.stringify({ new_password }),
        });
    }

    async updateUserActive(user_id: string, active: boolean) {
        return this.request(`/users/${user_id}/active`, {
            method: 'POST',
            body: JSON.stringify({ active }),
        });
    }

    async getAuditLogs(params: { limit?: number; offset?: number } = {}) {
        const query = new URLSearchParams();
        if (params.limit) query.set('limit', String(params.limit));
        if (params.offset) query.set('offset', String(params.offset));
        const qs = query.toString();
        return this.request(`/audit/logs${qs ? `?${qs}` : ''}`);
    }

    async pollImap() {
        return this.request('/maintenance/imap/poll', { method: 'POST' });
    }
}

export const api = new ApiClient();
