import React, { useEffect, useState, useCallback } from 'react';
import { Search, X } from 'lucide-react';
import Header from '../components/layout/Header';
import DataTable from '../components/tables/DataTable';
import StatusBadge from '../components/common/StatusBadge';
import LoadingState from '../components/common/LoadingState';
import ErrorState from '../components/common/ErrorState';
import { fetchAppointments } from '../api/api';
import {
  formatDate,
  formatChannel,
  formatWeekday,
  formatProbability,
} from '../utils/formatters';

export default function AppointmentRegister() {
  const [items, setItems] = useState([]);
  const [pagination, setPagination] = useState({ total: 0, page: 1, per_page: 20, pages: 1 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Query state (default: deterministic appointment_datetime desc, secondary appointment_id)
  const [search, setSearch] = useState('');
  const [channel, setChannel] = useState('');
  const [noShowFilter, setNoShowFilter] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [sortBy, setSortBy] = useState('appointment_datetime');
  const [sortOrder, setSortOrder] = useState('desc');
  const [page, setPage] = useState(1);

  // Selected record for detail modal
  const [selectedRecord, setSelectedRecord] = useState(null);

  const loadAppointments = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetchAppointments({
        page,
        per_page: 15,
        search,
        booking_channel: channel,
        no_show: noShowFilter,
        start_date: startDate,
        end_date: endDate,
        sort_by: sortBy,
        sort_order: sortOrder,
      });
      setItems(res.items || []);
      setPagination(res.pagination || { total: 0, page: 1, per_page: 15, pages: 1 });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [page, search, channel, noShowFilter, startDate, endDate, sortBy, sortOrder]);

  useEffect(() => {
    loadAppointments();
  }, [loadAppointments]);

  const handleSort = (columnKey) => {
    if (sortBy === columnKey) {
      setSortOrder((prev) => (prev === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortBy(columnKey);
      setSortOrder('desc');
    }
    setPage(1);
  };

  const handleSearchChange = (e) => {
    setSearch(e.target.value);
    setPage(1);
  };

  const columns = [
    {
      key: 'appointment_id',
      label: 'Appointment ID',
      sortable: true,
      render: (r) => <strong style={{ color: 'var(--color-teal-deep)' }}>{r.appointment_id}</strong>,
    },
    {
      key: 'appointment_datetime',
      label: 'Scheduled Date',
      sortable: true,
      render: (r) => formatDate(r.appointment_datetime),
    },
    {
      key: 'booking_channel',
      label: 'Channel',
      sortable: true,
      render: (r) => formatChannel(r.booking_channel),
    },
    {
      key: 'booking_lead_days',
      label: 'Lead Days',
      sortable: true,
      numeric: true,
      render: (r) => (r.booking_lead_days !== null && !isNaN(r.booking_lead_days) ? `${Math.round(r.booking_lead_days)}d` : '—'),
    },
    {
      key: 'prior_appointments_count',
      label: 'Prior Appts',
      sortable: true,
      numeric: true,
      render: (r) => (r.prior_appointments_count !== null && !isNaN(r.prior_appointments_count) ? Math.round(r.prior_appointments_count) : '—'),
    },
    {
      key: 'prior_no_show_rate',
      label: 'Prior No-Show Rate',
      sortable: true,
      numeric: true,
      render: (r) => (r.prior_no_show_rate !== null && !isNaN(r.prior_no_show_rate) ? formatProbability(r.prior_no_show_rate, 0) : '—'),
    },
    {
      key: 'no_show',
      label: 'Outcome',
      sortable: true,
      render: (r) => <StatusBadge status={r.no_show} />,
    },
  ];

  return (
    <div>
      <Header
        category="APPOINTMENTS"
        title="Appointment Register"
        description="Search appointments and review booking details."
      />

      <div className="page-body">
        {/* Toolbar */}
        <div className="toolbar">
          <div style={{ flex: '1 1 240px', position: 'relative' }}>
            <Search
              size={16}
              style={{
                position: 'absolute',
                left: '10px',
                top: '50%',
                transform: 'translateY(-50%)',
                color: 'var(--color-ink-muted)',
              }}
            />
            <input
              type="text"
              className="form-control"
              style={{ paddingLeft: '32px' }}
              placeholder="Search appointment ID..."
              value={search}
              onChange={handleSearchChange}
              aria-label="Search Appointment ID"
            />
          </div>

          <div style={{ flex: '0 1 180px' }}>
            <select
              className="form-control"
              value={channel}
              onChange={(e) => {
                setChannel(e.target.value);
                setPage(1);
              }}
              aria-label="Filter by booking channel"
            >
              <option value="">All Channels</option>
              <option value="online">Online Portal</option>
              <option value="phone">Telephone Desk</option>
              <option value="in_person">In-Person Reception</option>
            </select>
          </div>

          <div style={{ flex: '0 1 180px' }}>
            <select
              className="form-control"
              value={noShowFilter}
              onChange={(e) => {
                setNoShowFilter(e.target.value);
                setPage(1);
              }}
              aria-label="Filter by outcome"
            >
              <option value="">All Outcomes</option>
              <option value="0">Attended</option>
              <option value="1">No-Show</option>
            </select>
          </div>

          <div style={{ flex: '0 1 160px' }}>
            <input
              type="date"
              className="form-control"
              value={startDate}
              onChange={(e) => {
                setStartDate(e.target.value);
                setPage(1);
              }}
              aria-label="Filter start date"
              title="Start appointment date"
            />
          </div>

          <div style={{ flex: '0 1 160px' }}>
            <input
              type="date"
              className="form-control"
              value={endDate}
              onChange={(e) => {
                setEndDate(e.target.value);
                setPage(1);
              }}
              aria-label="Filter end date"
              title="End appointment date"
            />
          </div>

          {(search || channel || noShowFilter || startDate || endDate) && (
            <button
              className="btn btn-secondary"
              onClick={() => {
                setSearch('');
                setChannel('');
                setNoShowFilter('');
                setStartDate('');
                setEndDate('');
                setPage(1);
              }}
            >
              Reset
            </button>
          )}
        </div>

        {/* Table Content */}
        {loading && <LoadingState message="Loading appointments..." />}
        {error && <ErrorState message={error} onRetry={loadAppointments} />}

        {!loading && !error && (
          <>
            <DataTable
              columns={columns}
              data={items}
              onRowClick={(row) => setSelectedRecord(row)}
              sortBy={sortBy}
              sortOrder={sortOrder}
              onSort={handleSort}
            />

            {/* Pagination */}
            <div className="pagination">
              <div style={{ color: 'var(--color-ink-muted)' }}>
                Page <strong>{pagination.page}</strong> of{' '}
                <strong>{pagination.pages}</strong> &middot; {pagination.total?.toLocaleString()} records
              </div>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <button
                  className="btn btn-secondary"
                  disabled={pagination.page <= 1}
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                >
                  Previous
                </button>
                <button
                  className="btn btn-secondary"
                  disabled={pagination.page >= pagination.pages}
                  onClick={() => setPage((p) => p + 1)}
                >
                  Next
                </button>
              </div>
            </div>
          </>
        )}
      </div>

      {/* Detail Modal */}
      {selectedRecord && (
        <div className="modal-backdrop" onClick={() => setSelectedRecord(null)}>
          <div
            className="modal-card"
            onClick={(e) => e.stopPropagation()}
            role="dialog"
            aria-modal="true"
            aria-labelledby="modal-title"
          >
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                borderBottom: '1px solid var(--color-border)',
                paddingBottom: '0.75rem',
                marginBottom: '1rem',
              }}
            >
              <div>
                <div className="page-header-meta">Appointment Details</div>
                <h2 id="modal-title">{selectedRecord.appointment_id}</h2>
              </div>
              <button
                className="btn btn-secondary"
                onClick={() => setSelectedRecord(null)}
                aria-label="Close detail dialog"
              >
                <X size={18} />
              </button>
            </div>

            <div style={{ marginBottom: '1rem' }}>
              Outcome: <StatusBadge status={selectedRecord.no_show} />
            </div>

            <table className="ledger-table">
              <tbody>
                <tr>
                  <th>Booking Created At</th>
                  <td>{formatDate(selectedRecord.booking_created_at)}</td>
                </tr>
                <tr>
                  <th>Scheduled Appointment</th>
                  <td>{formatDate(selectedRecord.appointment_datetime)}</td>
                </tr>
                <tr>
                  <th>Booking Lead Time</th>
                  <td>{selectedRecord.booking_lead_days} days</td>
                </tr>
                <tr>
                  <th>Appointment Weekday</th>
                  <td>{formatWeekday(selectedRecord.appointment_weekday)}</td>
                </tr>
                <tr>
                  <th>Appointment / Booking Hour</th>
                  <td>
                    {selectedRecord.appointment_hour}:00 / {selectedRecord.booking_hour}:00
                  </td>
                </tr>
                <tr>
                  <th>Booking Channel</th>
                  <td>{formatChannel(selectedRecord.booking_channel)}</td>
                </tr>
                <tr>
                  <th>Prior Appointments Count</th>
                  <td>{selectedRecord.prior_appointments_count}</td>
                </tr>
                <tr>
                  <th>Prior No-Show Count</th>
                  <td>{selectedRecord.prior_no_show_count}</td>
                </tr>
                <tr>
                  <th>Prior Cancellations Count</th>
                  <td>{selectedRecord.prior_cancellations_count}</td>
                </tr>
                <tr>
                  <th>Prior No-Show Rate</th>
                  <td>{formatProbability(selectedRecord.prior_no_show_rate, 1)}</td>
                </tr>
                <tr>
                  <th>Days Since Last Appointment</th>
                  <td>{selectedRecord.days_since_last_appointment} days</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

