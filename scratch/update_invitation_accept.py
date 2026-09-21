import os

code_text = '''import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate, Link } from 'react-router-dom';

const InvitationAccept = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const codeParam = searchParams.get('code') || '';

  const [code, setCode] = useState(codeParam);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleAccept = async (e) => {
    if (e) e.preventDefault();
    if (!code.trim()) {
      setError('Please enter an invitation code.');
      return;
    }

    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const res = await fetch('/api/institution/accept-invite', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ code: code.trim() }),
      });

      const data = await res.json();

      if (res.ok) {
        setSuccess('Successfully joined institution! Redirecting to dashboard...');
        setTimeout(() => {
          navigate('/student/institution/dashboard');
        }, 1500);
      } else {
        if (res.status === 401) {
          setError('Please log in or create an account first to join an institution.');
        } else {
          setError(data.detail?.message || data.message || 'Failed to accept invitation. Please check the code.');
        }
      }
    } catch (err) {
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (codeParam) {
      handleAccept();
    }
  }, [codeParam]);

  return (
    <>
      <div className="bg-mesh"></div>

      <main style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: 'calc(100vh - 60px)', padding: '20px' }}>
        <section className="section-card" style={{ maxWidth: '520px', width: '100%', padding: '32px' }} aria-labelledby="invitationTitle">
          <h1 id="invitationTitle" style={{ marginBottom: '8px' }}>Institution Invitation</h1>
          <p className="input-label" style={{ marginBottom: '24px', textTransform: 'none', fontSize: '0.9rem' }}>
            Enter your invitation code to link your account to your institution.
          </p>

          {error && (
            <div role="alert" style={{ background: 'rgba(220,38,38,0.1)', border: '1px solid var(--red)', borderRadius: 'var(--rs)', padding: '10px 14px', marginBottom: '16px', fontSize: '0.85rem', color: 'var(--red-l)' }}>
              {error}
              {error.includes('log in') && (
                <div style={{ marginTop: '8px' }}>
                  <Link to={`/login?redirect=/invitation/accept?code=${encodeURIComponent(code)}`} style={{ color: 'var(--purple-l)', fontWeight: 600 }}>Log In</Link> or {' '}
                  <Link to={`/register`} style={{ color: 'var(--purple-l)', fontWeight: 600 }}>Register</Link>
                </div>
              )}
            </div>
          )}

          {success && (
            <div role="status" style={{ background: 'rgba(5,150,105,0.1)', border: '1px solid var(--green)', borderRadius: 'var(--rs)', padding: '10px 14px', marginBottom: '16px', fontSize: '0.85rem', color: 'var(--green-l)' }}>
              {success}
            </div>
          )}

          <form onSubmit={handleAccept}>
            <div className="input-group" style={{ marginBottom: '24px' }}>
              <label className="input-label" htmlFor="invCode">Invitation Code</label>
              <input
                id="invCode"
                type="text"
                className="text-input"
                style={{ width: '100%', fontFamily: 'monospace', textTransform: 'uppercase' }}
                placeholder="e.g. SMVITM or INV-1234"
                value={code}
                onChange={(e) => setCode(e.target.value)}
                required
              />
            </div>

            <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
              <button
                type="submit"
                className="btn-primary"
                disabled={loading}
                style={{ flex: '1', minWidth: '140px', justifyContent: 'center' }}
              >
                {loading ? 'Joining Institution...' : 'Accept Invitation'}
              </button>
              <button
                type="button"
                className="btn-outline"
                onClick={() => navigate('/dashboard')}
                style={{ flex: '1', minWidth: '140px', justifyContent: 'center' }}
              >
                Cancel
              </button>
            </div>
          </form>
        </section>
      </main>
    </>
  );
};

export default InvitationAccept;
'''

target_path = r"C:\Users\SHRIJA SANIL\VyasaPrep_Frontend\src\pages\auto\InvitationAccept.jsx"
with open(target_path, "w", encoding="utf-8") as f:
    f.write(code_text)

print("Updated InvitationAccept.jsx successfully")
