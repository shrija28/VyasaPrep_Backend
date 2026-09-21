import os

content = '''import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Chart as ChartJS, CategoryScale, LinearScale, BarElement, PointElement, LineElement, Title, Tooltip, Legend, Filler
} from 'chart.js';
import { Bar, Line } from 'react-chartjs-2';

ChartJS.register(CategoryScale, LinearScale, BarElement, PointElement, LineElement, Title, Tooltip, Legend, Filler);

const AdminDashboard = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchDashboard = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/admin/dashboard', { credentials: 'include' });
      if (res.ok) {
        const json = await res.json();
        setDashboardData(json);
      }
    } catch (err) {
      console.error('Failed to load admin dashboard:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboard();
  }, []);

  const chartOptions = {
    responsive: true, maintainAspectRatio: false,
    plugins: { legend: { display: false } },
    scales: {
      y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' } },
      x: { grid: { display: false }, ticks: { color: '#94a3b8' } }
    }
  };

  const kpis = dashboardData?.kpis || {};

  const qChartData = {
    labels: ['Physics', 'Chemistry', 'Mathematics', 'Biology'],
    datasets: [{
      label: 'Questions',
      data: [
        dashboardData?.admin_questions_by_subject?.Physics || 120,
        dashboardData?.admin_questions_by_subject?.Chemistry || 190,
        dashboardData?.admin_questions_by_subject?.Mathematics || 300,
        dashboardData?.admin_questions_by_subject?.Biology || 250
      ],
      borderColor: '#06b6d4', backgroundColor: 'rgba(6, 182, 212, 0.1)',
      fill: true, tension: 0.4
    }]
  };

  const examsChartData = {
    labels: ['Physics', 'Chemistry', 'Mathematics', 'Biology'],
    datasets: [{
      label: 'Exams',
      data: [
        dashboardData?.exams_by_subject?.Physics || 5,
        dashboardData?.exams_by_subject?.Chemistry || 8,
        dashboardData?.exams_by_subject?.Mathematics || 12,
        dashboardData?.exams_by_subject?.Biology || 6
      ],
      backgroundColor: 'rgba(124, 58, 237, 0.8)',
      borderRadius: 4
    }]
  };

  return (
    <>
      <style dangerouslySetInnerHTML={{ __html: `
    /* Clickable KPI cards */
    .kpi-grid { display:grid;grid-template-columns:repeat(auto-fit,minmax(175px,1fr));gap:14px;margin-bottom:24px; }

    .kpi-card {
      background:var(--card-bg);
      border:1px solid var(--border);
      border-radius:var(--r);
      padding:18px 20px;
      position:relative;
      overflow:hidden;
      cursor:pointer;
      text-decoration:none;
      display:block;
      transition:border-color 0.18s, transform 0.15s, box-shadow 0.18s;
    }
    .kpi-card:hover {
      border-color:rgba(255,255,255,0.18);
      transform:translateY(-2px);
      box-shadow:0 8px 24px rgba(0,0,0,0.25);
    }
    .kpi-card:hover .kpi-arrow { opacity:1; transform:translateX(0); }
    .kpi-card .kpi-val { font-size:2rem;font-weight:800;line-height:1;margin-bottom:4px;color:var(--text); }
    .kpi-card .kpi-lbl { font-size:0.78rem;color:var(--muted);text-transform:uppercase;letter-spacing:0.4px; }
    .kpi-card .kpi-sub { font-size:0.72rem;color:var(--muted2);margin-top:4px; }
    .kpi-card .kpi-accent { position:absolute;bottom:0;left:0;height:3px;width:100%;opacity:0.6; }
    .kpi-arrow {
      position:absolute;right:14px;bottom:14px;
      font-size:0.75rem;color:var(--muted);
      opacity:0;transform:translateX(-4px);
      transition:opacity 0.15s, transform 0.15s;
    }

    /* Quick actions */
    .quick-actions {
      display:flex;gap:10px;flex-wrap:wrap;margin-bottom:24px;
      padding:16px 20px;
      background:var(--card-bg);
      border:1px solid var(--border);
      border-radius:var(--r);
      align-items:center;
    }
    .quick-actions-label {
      font-size:0.72rem;text-transform:uppercase;letter-spacing:0.5px;
      color:var(--muted);font-weight:700;margin-right:4px;white-space:nowrap;
    }
    .qa-btn {
      display:inline-flex;align-items:center;gap:6px;
      padding:7px 14px;border-radius:var(--rs);
      font-size:0.82rem;font-weight:600;
      border:1px solid var(--border);
      color:var(--muted2);background:var(--s2);
      text-decoration:none;cursor:pointer;
      transition:border-color 0.15s, color 0.15s, background 0.15s, transform 0.12s;
    }
    .qa-btn:hover { border-color:rgba(255,255,255,0.2);color:var(--text);background:var(--s3);transform:translateY(-1px); }
    .qa-btn svg { width:13px;height:13px;flex-shrink:0; }

    /* Section headers with View All */
    .section-nav { display:flex;align-items:center;justify-content:space-between;width:100%; }
    .view-all-link {
      font-size:0.78rem;font-weight:600;color:var(--purple-l,#a78bfa);
      text-decoration:none;display:flex;align-items:center;gap:4px;
      transition:opacity 0.15s;white-space:nowrap;
    }
    .view-all-link:hover { opacity:0.75; }

    /* Alert items */
    .alert-item {
      display:flex;align-items:center;gap:10px;
      padding:10px 14px;border-radius:var(--rs);margin-bottom:6px;font-size:0.85rem;
      cursor:pointer;transition:opacity 0.15s;
    }
    .alert-item:hover { opacity:0.85; }
    .alert-warn  { background:rgba(217,119,6,0.12);border:1px solid rgba(217,119,6,0.3);color:var(--yellow-l); }
    .alert-error { background:rgba(220,38,38,0.12);border:1px solid rgba(220,38,38,0.3);color:var(--red-l); }
    .alert-info  { background:rgba(37,99,235,0.1);border:1px solid rgba(37,99,235,0.25);color:#60a5fa; }
    .alert-resolve { margin-left:auto;font-size:0.72rem;font-weight:700;white-space:nowrap; }

    /* Clickable institution rows */
    .inst-row { cursor:pointer;transition:background 0.12s; }
    .inst-row:hover td { background:rgba(255,255,255,0.03); }

    /* Clickable institution question bars */
    .inst-q-row {
      display:flex;align-items:center;gap:10px;
      padding:6px 0;cursor:pointer;border-radius:var(--rs);
      transition:background 0.12s;
    }
    .inst-q-row:hover { background:rgba(255,255,255,0.03); }

    /* Activity panel */
    .activity-item {
      display:flex;align-items:flex-start;gap:12px;
      padding:10px 0;border-bottom:1px solid rgba(255,255,255,0.04);
      cursor:pointer;transition:opacity 0.15s;text-decoration:none;
    }
    .activity-item:hover { opacity:0.75; }
    .activity-item:last-child { border-bottom:none; }
    .activity-dot {
      width:8px;height:8px;border-radius:50%;margin-top:5px;flex-shrink:0;
    }
    .activity-text { font-size:0.85rem;color:var(--text);line-height:1.4; }
    .activity-time { font-size:0.72rem;color:var(--muted);margin-top:2px; }

    /* Charts container */
    .charts-2col { display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:24px; }
    @media(max-width:900px) { .charts-2col { grid-template-columns:1fr; } }

    /* Sub-summary tiles */
    .sub-tile {
      border-radius:var(--rs);padding:14px;text-align:center;
      cursor:pointer;transition:transform 0.15s,opacity 0.15s;
      text-decoration:none;display:block;
    }
    .sub-tile:hover { transform:translateY(-2px);opacity:0.85; }
  ` }} />
      <div className="bg-mesh"></div>
      
      <div className="main-wrap">

    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
      <div>
        <h1 style={{ fontSize: '1.6rem', fontWeight: '800', margin: '0 0 3px' }}>Platform Dashboard</h1>
        <p style={{ color: 'var(--muted)', margin: '0', fontSize: '0.82rem' }} id="lastUpdated">
          {loading ? 'Refreshing...' : `Last updated: ${new Date().toLocaleTimeString()}`}
        </p>
      </div>
      <button className="btn-outline" id="refreshBtn" onClick={fetchDashboard} style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer' }}>
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ width: '14px', height: '14px' }}><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 11-2.12-9.36L23 10"/></svg>
        Refresh
      </button>
    </div>

    <div className="quick-actions">
      <span className="quick-actions-label">⚡ Quick Actions</span>
      <Link to="/admin/students" className="qa-btn">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
        Add Student
      </Link>
      <Link to="/admin/institutions" className="qa-btn">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
        Add Institution
      </Link>
      <Link to="/admin/upload" className="qa-btn">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
        Upload Question Paper
      </Link>
      <Link to="/admin/exams" className="qa-btn">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"/></svg>
        Create Exam
      </Link>
      <Link to="/admin/subscriptions" className="qa-btn">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="1" y="4" width="22" height="16" rx="2"/><line x1="1" y1="10" x2="23" y2="10"/></svg>
        Manage Subscriptions
      </Link>
      <Link to="/admin/syllabus" className="qa-btn">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M4 19.5A2.5 2.5 0 016.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 014 19.5v-15A2.5 2.5 0 016.5 2z"/></svg>
        Add KCET Topic
      </Link>
    </div>

    {dashboardData?.alerts && dashboardData.alerts.length > 0 && (
      <div id="alertsSection" style={{ marginBottom: '20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
          <span style={{ fontSize: '0.72rem', textTransform: 'uppercase', letterSpacing: '0.5px', color: 'var(--muted)', fontWeight: '700' }}>⚠️ Alerts</span>
          <Link to="/admin/subscriptions" className="view-all-link">Resolve All →</Link>
        </div>
        <div id="alertsList">
          {dashboardData.alerts.map((al, idx) => (
            <div key={idx} className={`alert-item alert-${al.severity}`}>
              <span>{al.message}</span>
              <span className="alert-resolve">Check →</span>
            </div>
          ))}
        </div>
      </div>
    )}

    <div style={{ fontSize: '0.72rem', textTransform: 'uppercase', letterSpacing: '0.5px', color: 'var(--muted)', marginBottom: '10px', fontWeight: '700' }}>Platform Overview</div>
    <div className="kpi-grid">
      <Link to="/admin/institutions" className="kpi-card">
        <div className="kpi-accent" style={{ background: 'linear-gradient(90deg,#2563eb,#0891b2)' }}></div>
        <div className="kpi-val" id="kpiInstitutions">{kpis.total_institutions ?? '—'}</div>
        <div className="kpi-lbl">Institutions</div>
        <div className="kpi-sub" id="kpiInstitutionsSub">{kpis.active_institutions ? `${kpis.active_institutions} active` : 'Active status'}</div>
        <span className="kpi-arrow">→</span>
      </Link>
      <Link to="/admin/students" className="kpi-card">
        <div className="kpi-accent" style={{ background: 'linear-gradient(90deg,#7c3aed,#4f46e5)' }}></div>
        <div className="kpi-val" id="kpiStudents">{kpis.total_students ?? '—'}</div>
        <div className="kpi-lbl">Total Students</div>
        <div className="kpi-sub" id="kpiStudentsSub">{kpis.institution_linked_students ? `${kpis.institution_linked_students} institutional` : 'Enrolled'}</div>
        <span className="kpi-arrow">→</span>
      </Link>
      <Link to="/admin/questions" className="kpi-card">
        <div className="kpi-accent" style={{ background: 'linear-gradient(90deg,#06b6d4,#0891b2)' }}></div>
        <div className="kpi-val" id="kpiQuestions">{(kpis.admin_questions_total || 0) + (kpis.institution_questions_total || 0)}</div>
        <div className="kpi-lbl">Total Questions</div>
        <div className="kpi-sub" id="kpiQuestionsSub">{kpis.admin_questions_total ? `${kpis.admin_questions_total} platform-wide` : 'Question bank'}</div>
        <span className="kpi-arrow">→</span>
      </Link>
      <Link to="/admin/exams" className="kpi-card">
        <div className="kpi-accent" style={{ background: 'linear-gradient(90deg,#e11d48,#be123c)' }}></div>
        <div className="kpi-val" id="kpiExams">{kpis.total_exams ?? '—'}</div>
        <div className="kpi-lbl">Exams</div>
        <div className="kpi-sub" id="kpiExamsSub">{kpis.published_exams ? `${kpis.published_exams} published` : 'Available'}</div>
        <span className="kpi-arrow">→</span>
      </Link>
      <Link to="/admin/analytics" className="kpi-card">
        <div className="kpi-accent" style={{ background: 'linear-gradient(90deg,#0891b2,#0d9488)' }}></div>
        <div className="kpi-val" id="kpiAttempts">{kpis.total_attempts ?? '—'}</div>
        <div className="kpi-lbl">Exam Attempts</div>
        <div className="kpi-sub" id="kpiAttemptsSub">{kpis.avg_score ? `Avg Score: ${kpis.avg_score}%` : 'Performance'}</div>
        <span className="kpi-arrow">→</span>
      </Link>
      <Link to="/admin/subscriptions" className="kpi-card">
        <div className="kpi-accent" style={{ background: 'linear-gradient(90deg,#059669,#16a34a)' }}></div>
        <div className="kpi-val" id="kpiActiveSubs">{kpis.active_subscriptions ?? '—'}</div>
        <div className="kpi-lbl">Active Subscriptions</div>
        <div className="kpi-sub" id="kpiActiveSubsSub">{kpis.overdue_subscriptions ? `${kpis.overdue_subscriptions} overdue` : 'Status'}</div>
        <span className="kpi-arrow">→</span>
      </Link>
    </div>

    <div className="charts-2col">
      <div className="section-card">
        <div className="section-card-header">
          <div className="section-nav">
            <div>
              <h3 style={{ margin: '0', fontSize: '1rem' }}>Admin Question Bank</h3>
              <p className="section-sub" style={{ margin: '0' }}>Questions grouped by subject</p>
            </div>
            <Link to="/admin/questions" className="view-all-link">Manage →</Link>
          </div>
        </div>
        <div className="section-body" style={{ height: '220px' }}>
          <div style={{ height: '200px' }}>
            <Line data={qChartData} options={chartOptions} />
          </div>
        </div>
      </div>

      <div className="section-card">
        <div className="section-card-header">
          <div className="section-nav">
            <div>
              <h3 style={{ margin: '0', fontSize: '1rem' }}>Exams by Subject</h3>
              <p className="section-sub" style={{ margin: '0' }}>Published platform exams</p>
            </div>
            <Link to="/admin/exams" className="view-all-link">View All →</Link>
          </div>
        </div>
        <div className="section-body" style={{ height: '220px' }}>
          <div style={{ height: '200px' }}>
            <Bar data={examsChartData} options={chartOptions} />
          </div>
        </div>
      </div>
    </div>

    <div className="charts-2col">
      {/* 1. Institution Question Banks */}
      <div className="section-card">
        <div className="section-card-header">
          <div className="section-nav">
            <div>
              <h3 style={{ margin: '0', fontSize: '1rem' }}>Institution Question Banks</h3>
              <p className="section-sub" style={{ margin: '0' }}>Questions created by institutions</p>
            </div>
            <Link to="/admin/institutions" className="view-all-link">Manage →</Link>
          </div>
        </div>
        <div className="section-body">
          <div id="instQList" style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {loading ? (
              <div style={{ color: 'var(--muted)', textAlign: 'center', padding: '20px' }}>Loading...</div>
            ) : (!dashboardData?.institution_question_counts || dashboardData.institution_question_counts.length === 0) ? (
              <div style={{ color: 'var(--muted)', textAlign: 'center', padding: '20px' }}>No institution question banks uploaded yet.</div>
            ) : (
              dashboardData.institution_question_counts.map((item, idx) => (
                <div key={idx} className="inst-q-row" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 12px', background: 'rgba(255,255,255,0.02)', borderRadius: '6px' }}>
                  <span style={{ fontWeight: 600, color: 'var(--text)' }}>{item.name}</span>
                  <span style={{ background: 'rgba(124,58,237,0.15)', color: 'var(--purple-l)', padding: '2px 8px', borderRadius: '12px', fontSize: '0.8rem', fontWeight: 600 }}>
                    {item.count} questions
                  </span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* 2. Recent Activity */}
      <div className="section-card">
        <div className="section-card-header">
          <div className="section-nav">
            <div>
              <h3 style={{ margin: '0', fontSize: '1rem' }}>Recent Activity</h3>
              <p className="section-sub" style={{ margin: '0' }}>Latest platform events</p>
            </div>
            <Link to="/admin/analytics" className="view-all-link">Full Log →</Link>
          </div>
        </div>
        <div className="section-body" style={{ paddingTop: '4px' }}>
          <div id="activityList">
            {loading ? (
              <div style={{ color: 'var(--muted)', textAlign: 'center', padding: '24px' }}>Loading...</div>
            ) : (!dashboardData?.recent_activity || dashboardData.recent_activity.length === 0) ? (
              <div style={{ color: 'var(--muted)', textAlign: 'center', padding: '24px' }}>No recent activity.</div>
            ) : (
              dashboardData.recent_activity.map((act) => (
                <div key={act.id} className="activity-item">
                  <div className="activity-dot" style={{ background: act.badge_color === 'purple' ? '#a78bfa' : act.badge_color === 'green' ? '#10b981' : '#3b82f6' }}></div>
                  <div>
                    <div className="activity-text">{act.title}</div>
                    <div className="activity-time">{act.subtitle} {act.timestamp ? `• ${new Date(act.timestamp).toLocaleTimeString()}` : ''}</div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>

    <div className="charts-2col" style={{ marginTop: '0' }}>
      {/* 3. Recent Institutions */}
      <div className="section-card">
        <div className="section-card-header">
          <div className="section-nav">
            <div><h3 style={{ margin: '0', fontSize: '1rem' }}>Recent Institutions</h3></div>
            <Link to="/admin/institutions" className="view-all-link">View All →</Link>
          </div>
        </div>
        <div className="section-body" style={{ padding: '0' }}>
          <table className="results-table" id="recentInstTable">
            <thead><tr><th>Institution</th><th>Status</th><th>Joined</th></tr></thead>
            <tbody id="recentInstBody">
              {loading ? (
                <tr><td colSpan="3" style={{ textAlign: 'center', color: 'var(--muted)', padding: '24px' }}>Loading...</td></tr>
              ) : (!dashboardData?.recent_institutions || dashboardData.recent_institutions.length === 0) ? (
                <tr><td colSpan="3" style={{ textAlign: 'center', color: 'var(--muted)', padding: '24px' }}>No registered institutions yet.</td></tr>
              ) : (
                dashboardData.recent_institutions.map((inst) => (
                  <tr key={inst.id} className="inst-row">
                    <td style={{ fontWeight: 600, color: 'var(--text)' }}>{inst.name}</td>
                    <td>
                      <span style={{ textTransform: 'capitalize', padding: '2px 8px', borderRadius: '4px', fontSize: '0.78rem', background: inst.status === 'active' ? 'rgba(16,185,129,0.15)' : 'rgba(239,68,68,0.15)', color: inst.status === 'active' ? 'var(--green-l)' : 'var(--red-l)' }}>
                        {inst.status}
                      </span>
                    </td>
                    <td style={{ color: 'var(--muted)', fontSize: '0.82rem' }}>
                      {inst.registered_at ? new Date(inst.registered_at).toLocaleDateString() : '—'}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      <div className="section-card">
        <div className="section-card-header">
          <div className="section-nav">
            <div><h3 style={{ margin: '0', fontSize: '1rem' }}>Subscription Overview</h3></div>
            <Link to="/admin/subscriptions" className="view-all-link">Manage →</Link>
          </div>
        </div>
        <div className="section-body">
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
            <Link to="/admin/subscriptions" className="sub-tile" style={{ background: 'rgba(5,150,105,0.12)', border: '1px solid rgba(5,150,105,0.3)' }}>
              <div style={{ fontSize: '1.6rem', fontWeight: '800', color: 'var(--green-l)' }} id="tilActiveSubs">{kpis.active_subscriptions ?? 0}</div>
              <div style={{ fontSize: '0.75rem', color: 'var(--muted)' }}>Active</div>
            </Link>
            <Link to="/admin/subscriptions" className="sub-tile" style={{ background: 'rgba(220,38,38,0.1)', border: '1px solid rgba(220,38,38,0.25)' }}>
              <div style={{ fontSize: '1.6rem', fontWeight: '800', color: 'var(--red-l)' }} id="tilExpiredSubs">{kpis.expired_subscriptions ?? 0}</div>
              <div style={{ fontSize: '0.75rem', color: 'var(--muted)' }}>Expired</div>
            </Link>
            <Link to="/admin/subscriptions" className="sub-tile" style={{ background: 'rgba(217,119,6,0.12)', border: '1px solid rgba(217,119,6,0.3)' }}>
              <div style={{ fontSize: '1.6rem', fontWeight: '800', color: 'var(--yellow-l)' }} id="tilOverdueSubs">{kpis.overdue_subscriptions ?? 0}</div>
              <div style={{ fontSize: '0.75rem', color: 'var(--muted)' }}>Overdue</div>
            </Link>
            <Link to="/admin/subscriptions" className="sub-tile" style={{ background: 'rgba(37,99,235,0.1)', border: '1px solid rgba(37,99,235,0.25)' }}>
              <div style={{ fontSize: '1.6rem', fontWeight: '800', color: '#60a5fa' }} id="tilNoSubs">{kpis.direct_students ?? 0}</div>
              <div style={{ fontSize: '0.75rem', color: 'var(--muted)' }}>Direct Students</div>
            </Link>
          </div>
        </div>
      </div>
    </div>

    {/* 4. Direct Subscriber Students */}
    <div className="section-card" style={{ marginTop: '20px' }}>
      <div className="section-card-header">
        <div className="section-nav">
          <div>
            <h3 style={{ margin: '0', fontSize: '1rem' }}>Direct Subscriber Students</h3>
            <p className="section-sub" style={{ margin: '0' }}>Personal/independent students</p>
          </div>
          <Link to="/admin/students" className="view-all-link">Manage All →</Link>
        </div>
      </div>
      <div className="section-body" style={{ padding: '0' }}>
        <table className="results-table" id="directSubTable">
          <thead>
            <tr>
              <th>Name</th>
              <th>KCET ID</th>
              <th>Email</th>
              <th>Subscription Status</th>
              <th>Joined</th>
            </tr>
          </thead>
          <tbody id="directSubBody">
            {loading ? (
              <tr><td colSpan="5" style={{ textAlign: 'center', color: 'var(--muted)', padding: '24px' }}>Loading...</td></tr>
            ) : (!dashboardData?.direct_students || dashboardData.direct_students.length === 0) ? (
              <tr><td colSpan="5" style={{ textAlign: 'center', color: 'var(--muted)', padding: '24px' }}>No direct subscriber students found.</td></tr>
            ) : (
              dashboardData.direct_students.map((stu) => (
                <tr key={stu.id}>
                  <td style={{ fontWeight: 600, color: 'var(--text)' }}>{stu.name}</td>
                  <td style={{ fontFamily: 'monospace', fontSize: '0.82rem', color: 'var(--purple-l)' }}>{stu.kcet_student_id}</td>
                  <td style={{ color: 'var(--muted)', fontSize: '0.85rem' }}>{stu.email}</td>
                  <td>
                    <span style={{ textTransform: 'capitalize', padding: '2px 8px', borderRadius: '4px', fontSize: '0.78rem', background: 'rgba(16,185,129,0.15)', color: 'var(--green-l)' }}>
                      {stu.subscription_status || 'Active'}
                    </span>
                  </td>
                  <td style={{ color: 'var(--muted)', fontSize: '0.82rem' }}>
                    {stu.created_at ? new Date(stu.created_at).toLocaleDateString() : '—'}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>

  </div>
    </>
  );
};

export default AdminDashboard;
'''

target_path = r"C:\Users\SHRIJA SANIL\VyasaPrep_Frontend\src\pages\auto\AdminDashboard.jsx"
with open(target_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Updated AdminDashboard.jsx successfully")
