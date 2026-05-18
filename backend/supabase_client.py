"""
Strategy #1: Backend-as-a-Service — Supabase Integration
=========================================================
Replaces in-memory dicts with Supabase (managed PostgreSQL + instant REST API).

- Tickets, sessions, and employee data persist across restarts.
- Supabase dashboard gives judges a live view of the database.
- Falls back to in-memory storage if Supabase is not configured (demo-safe).

Setup: Create a Supabase project at https://supabase.com, then add
SUPABASE_URL and SUPABASE_KEY to your .env file.
"""

import os
import datetime
from typing import Optional

# Graceful import — Supabase is optional for local dev
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False


class SupabaseStore:
    """
    Unified data store that uses Supabase when configured,
    falls back to in-memory dicts for zero-config local dev.
    """

    def __init__(self):
        self.client: Optional[Client] = None
        self._memory_tickets: dict = {}
        self._memory_sessions: dict = {}
        self._memory_employees: dict = {}

        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")

        if SUPABASE_AVAILABLE and url and key:
            try:
                self.client = create_client(url, key)
                print("✅ Supabase connected — using managed PostgreSQL")
            except Exception as e:
                print(f"⚠️  Supabase init failed, falling back to in-memory: {e}")
                self.client = None
        else:
            mode = "supabase package not installed" if not SUPABASE_AVAILABLE else "SUPABASE_URL/KEY not set"
            print(f"ℹ️  Running in-memory mode ({mode})")

    @property
    def is_connected(self) -> bool:
        return self.client is not None

    # ─── Tickets ─────────────────────────────────────────────────────

    def create_ticket(self, ticket_id: str, employee_id: str, query: str,
                      priority: str, status: str = "OPEN") -> dict:
        """Create an escalation ticket."""
        ticket = {
            "ticket_id": ticket_id,
            "employee_id": employee_id,
            "query": query,
            "priority": priority,
            "status": status,
            "created_at": datetime.datetime.utcnow().isoformat(),
        }

        if self.client:
            try:
                self.client.table("tickets").insert(ticket).execute()
            except Exception as e:
                print(f"⚠️  Supabase ticket insert failed: {e}")
                self._memory_tickets[ticket_id] = ticket
        else:
            self._memory_tickets[ticket_id] = ticket

        return ticket

    def get_all_tickets(self) -> dict:
        """Retrieve all tickets."""
        if self.client:
            try:
                result = self.client.table("tickets") \
                    .select("*") \
                    .order("created_at", desc=True) \
                    .execute()
                # Return in the same format the frontend expects
                return {
                    row["ticket_id"]: {
                        "employee_id": row["employee_id"],
                        "query": row["query"],
                        "priority": row["priority"],
                        "status": row["status"],
                    }
                    for row in result.data
                }
            except Exception as e:
                print(f"⚠️  Supabase ticket fetch failed: {e}")
                return self._memory_tickets
        return self._memory_tickets

    def update_ticket_status(self, ticket_id: str, status: str) -> bool:
        """Update a ticket's status (OPEN → IN_PROGRESS → RESOLVED)."""
        if self.client:
            try:
                self.client.table("tickets") \
                    .update({"status": status}) \
                    .eq("ticket_id", ticket_id) \
                    .execute()
                return True
            except Exception:
                pass
        if ticket_id in self._memory_tickets:
            self._memory_tickets[ticket_id]["status"] = status
            return True
        return False

    # ─── Chat Sessions ──────────────────────────────────────────────

    def save_message(self, session_id: str, employee_id: str,
                     role: str, content: str, metadata: dict = None):
        """Persist a chat message."""
        msg = {
            "session_id": session_id,
            "employee_id": employee_id,
            "role": role,
            "content": content[:5000],  # Truncate for safety
            "metadata": metadata or {},
            "created_at": datetime.datetime.utcnow().isoformat(),
        }

        if self.client:
            try:
                self.client.table("chat_messages").insert(msg).execute()
            except Exception as e:
                print(f"⚠️  Supabase message insert failed: {e}")
                self._memory_sessions.setdefault(session_id, []).append(msg)
        else:
            self._memory_sessions.setdefault(session_id, []).append(msg)

    def get_session_history(self, session_id: str, limit: int = 20) -> list:
        """Retrieve recent messages for a session."""
        if self.client:
            try:
                result = self.client.table("chat_messages") \
                    .select("*") \
                    .eq("session_id", session_id) \
                    .order("created_at", desc=False) \
                    .limit(limit) \
                    .execute()
                return result.data
            except Exception:
                return self._memory_sessions.get(session_id, [])
        return self._memory_sessions.get(session_id, [])

    # ─── Employees ───────────────────────────────────────────────────

    def get_employee(self, employee_id: str) -> Optional[dict]:
        """Fetch employee profile (for context-aware responses)."""
        if self.client:
            try:
                result = self.client.table("employees") \
                    .select("*") \
                    .eq("employee_id", employee_id) \
                    .limit(1) \
                    .execute()
                return result.data[0] if result.data else None
            except Exception:
                return self._memory_employees.get(employee_id)
        return self._memory_employees.get(employee_id)

    # ─── Analytics (for admin dashboard) ─────────────────────────────

    def get_stats(self) -> dict:
        """Quick stats for the admin dashboard."""
        if self.client:
            try:
                tickets = self.client.table("tickets").select("*", count="exact").execute()
                messages = self.client.table("chat_messages").select("*", count="exact").execute()
                open_tickets = self.client.table("tickets") \
                    .select("*", count="exact") \
                    .eq("status", "OPEN") \
                    .execute()
                return {
                    "total_tickets": tickets.count or 0,
                    "open_tickets": open_tickets.count or 0,
                    "total_messages": messages.count or 0,
                    "data_source": "supabase",
                }
            except Exception:
                pass

        return {
            "total_tickets": len(self._memory_tickets),
            "open_tickets": sum(1 for t in self._memory_tickets.values() if t.get("status") == "OPEN"),
            "total_messages": sum(len(msgs) for msgs in self._memory_sessions.values()),
            "data_source": "in-memory",
        }


# ─── Singleton Instance ─────────────────────────────────────────────
store = SupabaseStore()


# ─── Supabase SQL Setup Script ──────────────────────────────────────
# Run this in the Supabase SQL Editor to create the required tables:
SUPABASE_SETUP_SQL = """
-- Tickets table
CREATE TABLE IF NOT EXISTS tickets (
    id BIGSERIAL PRIMARY KEY,
    ticket_id TEXT UNIQUE NOT NULL,
    employee_id TEXT NOT NULL,
    query TEXT NOT NULL,
    priority TEXT DEFAULT 'MEDIUM',
    status TEXT DEFAULT 'OPEN',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Chat messages table
CREATE TABLE IF NOT EXISTS chat_messages (
    id BIGSERIAL PRIMARY KEY,
    session_id TEXT NOT NULL,
    employee_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Employees table
CREATE TABLE IF NOT EXISTS employees (
    id BIGSERIAL PRIMARY KEY,
    employee_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    email TEXT,
    department TEXT DEFAULT 'General',
    role TEXT DEFAULT 'Employee',
    join_date DATE,
    leave_balance INTEGER DEFAULT 14,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_tickets_employee ON tickets(employee_id);
CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status);
CREATE INDEX IF NOT EXISTS idx_messages_session ON chat_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_employees_id ON employees(employee_id);

-- Row Level Security (RLS) — enable in production
-- ALTER TABLE tickets ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE chat_messages ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE employees ENABLE ROW LEVEL SECURITY;
"""
