import React, { useEffect, useState } from 'react';

type SessionUser = {
  email?: string;
  username?: string;
  name?: string;
  identity_provider?: string;
};

type SessionResponse = {
  authenticated: boolean;
  user?: SessionUser;
};

const authBaseUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const ReportPage: React.FC = () => {
  const [initialized, setInitialized] = useState(false);
  const [authenticated, setAuthenticated] = useState(false);
  const [user, setUser] = useState<SessionUser | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    const loadSession = async () => {
      try {
        const response = await fetch(`${authBaseUrl}/api/session`, {
          credentials: 'include'
        });

        if (!response.ok) {
          setAuthenticated(false);
          setUser(null);
          return;
        }

        const payload: SessionResponse = await response.json();
        setAuthenticated(payload.authenticated);
        setUser(payload.user || null);
      } catch (sessionError) {
        setError(sessionError instanceof Error ? sessionError.message : 'Failed to load session');
      } finally {
        setInitialized(true);
      }
    };

    loadSession();
  }, []);

  const login = (provider?: string) => {
    const target = provider
      ? `${authBaseUrl}/auth/login?provider=${encodeURIComponent(provider)}`
      : `${authBaseUrl}/auth/login`;

    window.location.assign(target);
  };

  const downloadReport = async () => {
    if (!authenticated) {
      setError('Session is not authenticated');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      setMessage(null);

      const response = await fetch(`${process.env.REACT_APP_API_URL}/reports`, {
        credentials: 'include'
      });

      if (!response.ok) {
        throw new Error(`Report request failed with ${response.status}`);
      }

      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const anchor = document.createElement('a');
      anchor.href = downloadUrl;
      anchor.download = 'usage-report.csv';
      anchor.click();
      window.URL.revokeObjectURL(downloadUrl);
      setMessage('Report generated and downloaded successfully.');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  if (!initialized) {
    return <div>Loading...</div>;
  }

  if (!authenticated) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-950 px-6 py-10 text-slate-50">
        <div className="w-full max-w-xl rounded-3xl border border-cyan-400/20 bg-slate-900/90 p-8 shadow-2xl shadow-cyan-950/40">
          <p className="mb-3 text-sm uppercase tracking-[0.35em] text-cyan-300">BionicPRO Secure Access</p>
          <h1 className="mb-4 text-4xl font-bold">Usage Reports</h1>
          <p className="mb-8 text-base text-slate-300">
            Аутентификация и токены вынесены в сервер `bionicpro-auth`. Фронтенд работает только через
            защищённую сессионную cookie.
          </p>

          <div className="flex flex-col gap-3 sm:flex-row">
            <button
              onClick={() => login()}
              className="rounded-xl bg-cyan-400 px-5 py-3 font-semibold text-slate-950 transition hover:bg-cyan-300"
            >
              Login with Keycloak
            </button>
            <button
              onClick={() => login('yandex')}
              className="rounded-xl border border-amber-300/60 px-5 py-3 font-semibold text-amber-100 transition hover:bg-amber-300/10"
            >
              Login with Yandex ID
            </button>
          </div>

          {error && (
            <div className="mt-6 rounded-xl border border-rose-400/40 bg-rose-500/10 p-4 text-rose-100">
              {error}
            </div>
          )}
        </div>
      </div>
    );
  }

  const displayName = user?.name || user?.email || user?.username || 'Authenticated user';

  const logout = async () => {
    try {
      setLoading(true);
      await fetch(`${authBaseUrl}/auth/logout`, {
        method: 'POST',
        credentials: 'include'
      });
      setAuthenticated(false);
      setUser(null);
      setMessage(null);
    } catch (logoutError) {
      setError(logoutError instanceof Error ? logoutError.message : 'Logout failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-[radial-gradient(circle_at_top,_rgba(34,211,238,0.22),_transparent_32%),linear-gradient(135deg,_#020617,_#111827_50%,_#172554)] px-6 py-10 text-slate-100">
      <div className="w-full max-w-2xl rounded-3xl border border-white/10 bg-slate-950/70 p-8 shadow-2xl shadow-slate-950/60 backdrop-blur">
        <div className="mb-8 flex flex-col gap-4 border-b border-white/10 pb-6 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-sm uppercase tracking-[0.35em] text-cyan-300">Session Managed by Backend</p>
            <h1 className="mt-3 text-4xl font-bold">Usage Reports</h1>
            <p className="mt-3 text-slate-300">
              {displayName}
              {user?.identity_provider ? ` via ${user.identity_provider}` : ''}
            </p>
          </div>
          <button
            onClick={logout}
            disabled={loading}
            className="rounded-xl border border-white/20 px-4 py-2 font-semibold text-white transition hover:bg-white/10 disabled:cursor-not-allowed disabled:opacity-60"
          >
            Logout
          </button>
        </div>

        <button
          onClick={downloadReport}
          disabled={loading}
          className={`rounded-2xl bg-cyan-400 px-5 py-3 font-semibold text-slate-950 transition hover:bg-cyan-300 ${
            loading ? 'cursor-not-allowed opacity-50' : ''
          }`}
        >
          {loading ? 'Generating Report...' : 'Download Report'}
        </button>

        {error && (
          <div className="mt-4 rounded-2xl border border-rose-400/40 bg-rose-500/10 p-4 text-rose-100">
            {error}
          </div>
        )}

        {message && (
          <div className="mt-4 rounded-2xl border border-emerald-400/40 bg-emerald-500/10 p-4 text-emerald-100">
            {message}
          </div>
        )}
      </div>
    </div>
  );
};

export default ReportPage;
