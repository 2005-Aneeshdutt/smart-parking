import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import {
  Container,
  Row,
  Col,
  Card,
  Table,
  Badge,
  Button,
  Spinner,
  Alert,
  Modal,
  Form,
} from "react-bootstrap";
import { useAuth } from "../context/AuthContext1";
import "../styles/AdminDashboard.css";

function AdminDashboard() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [lots, setLots] = useState([]);
  const [bookings, setBookings] = useState([]);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [activeTab, setActiveTab] = useState("overview");
  const [showEditModal, setShowEditModal] = useState(false);
  const [showCreateLotModal, setShowCreateLotModal] = useState(false);
  const [showCreateUserModal, setShowCreateUserModal] = useState(false);
  const [selectedLot, setSelectedLot] = useState(null);
  const [editForm, setEditForm] = useState({});
  const [createLotForm, setCreateLotForm] = useState({
    lot_name: "",
    location: "",
    total_spots: "",
    hourly_rate: "",
    status: "open"
  });
  const [createUserForm, setCreateUserForm] = useState({
    name: "",
    email: "",
    password: "",
    role: "driver"
  });
  const [analytics, setAnalytics] = useState(null);

  useEffect(() => {
    if (user?.role !== "admin") {
      navigate("/dashboard");
      return;
    }
    fetchDashboardData();
  }, [user]);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      setError(""); // Clear previous errors
      
      // Use Promise.allSettled to handle individual failures gracefully
      const results = await Promise.allSettled([
        axios.get("http://127.0.0.1:8000/admin/stats"),
        axios.get("http://127.0.0.1:8000/admin/lots/manage"),
        axios.get("http://127.0.0.1:8000/admin/bookings"),
        axios.get("http://127.0.0.1:8000/admin/users"),
        axios.get("http://127.0.0.1:8000/admin/analytics").catch(() => ({ data: null }))
      ]);

      // Handle each result
      if (results[0].status === 'fulfilled') {
        setStats(results[0].value.data);
      } else {
        console.error("Failed to load stats:", results[0].reason);
      }

      if (results[1].status === 'fulfilled') {
        setLots(results[1].value.data.lots || []);
      } else {
        console.error("Failed to load lots:", results[1].reason);
        setLots([]);
      }

      if (results[2].status === 'fulfilled') {
        setBookings(results[2].value.data.bookings || []);
      } else {
        console.error("Failed to load bookings:", results[2].reason);
        setBookings([]);
      }

      if (results[3].status === 'fulfilled') {
        setUsers(results[3].value.data.users || []);
      } else {
        console.error("Failed to load users:", results[3].reason);
        setUsers([]);
      }

      if (results[4].status === 'fulfilled' && results[4].value.data) {
        setAnalytics(results[4].value.data);
      }

      // Only show error if critical endpoints failed
      const criticalFailures = results.slice(0, 4).filter(r => r.status === 'rejected');
      if (criticalFailures.length > 0) {
        setError(`Failed to load some data. Check console for details.`);
      }
    } catch (err) {
      setError("Failed to load dashboard data: " + (err.message || "Unknown error"));
      console.error("Admin dashboard error:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleEditLot = (lot) => {
    setSelectedLot(lot);
    setEditForm({
      lot_name: lot.lot_name,
      location: lot.location,
      total_spots: lot.total_spots,
      hourly_rate: lot.hourly_rate,
      status: lot.status,
    });
    setShowEditModal(true);
  };

  const handleUpdateLot = async () => {
    try {
      await axios.put(
        `http://127.0.0.1:8000/admin/lots/${selectedLot.lot_id}`,
        editForm
      );
      setShowEditModal(false);
      fetchDashboardData();
    } catch (err) {
      alert("Failed to update lot");
    }
  };

  const handleCreateLot = async () => {
    try {
      await axios.post("http://127.0.0.1:8000/admin/lots", {
        ...createLotForm,
        total_spots: parseInt(createLotForm.total_spots),
        hourly_rate: parseFloat(createLotForm.hourly_rate)
      });
      setShowCreateLotModal(false);
      setCreateLotForm({
        lot_name: "",
        location: "",
        total_spots: "",
        hourly_rate: "",
        status: "open"
      });
      fetchDashboardData();
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to create lot");
    }
  };

  const handleDeleteLot = async (lotId) => {
    if (!window.confirm("Are you sure you want to delete this parking lot? This action cannot be undone.")) {
      return;
    }
    try {
      await axios.delete(`http://127.0.0.1:8000/admin/lots/${lotId}`);
      fetchDashboardData();
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to delete lot");
    }
  };

  const handleDeleteBooking = async (bookingId) => {
    if (!window.confirm("Are you sure you want to delete this booking?")) {
      return;
    }
    try {
      await axios.delete(`http://127.0.0.1:8000/admin/bookings/${bookingId}`);
      fetchDashboardData();
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to delete booking");
    }
  };

  const handleCreateUser = async () => {
    try {
      await axios.post("http://127.0.0.1:8000/admin/users", createUserForm);
      setShowCreateUserModal(false);
      setCreateUserForm({
        name: "",
        email: "",
        password: "",
        role: "driver"
      });
      fetchDashboardData();
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to create user");
    }
  };

  const handleDeleteUser = async (userId) => {
    if (!window.confirm("Are you sure you want to delete this user? All their bookings will also be deleted.")) {
      return;
    }
    try {
      await axios.delete(`http://127.0.0.1:8000/admin/users/${userId}`);
      fetchDashboardData();
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to delete user");
    }
  };

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  if (loading) {
    return (
      <div className="admin-loading">
        <Spinner animation="border" variant="primary" />
        <p>Loading admin dashboard...</p>
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="danger" className="mt-4 text-center">
        {error}
      </Alert>
    );
  }

  return (
    <div className="admin-dashboard">
      {/* Header */}
      <div className="admin-header">
        <Container fluid>
          <Row className="align-items-center">
            <Col>
              <h2 className="mb-0">
                <span className="admin-icon">🛡️</span> Admin Dashboard
              </h2>
              <p className="text-muted mb-0">Welcome back, {user?.name}</p>
            </Col>
            <Col xs="auto">
              <Button variant="outline-danger" onClick={handleLogout}>
                Logout
              </Button>
            </Col>
          </Row>
        </Container>
      </div>

      <Container fluid className="mt-4">
        {/* Navigation Tabs */}
        <div className="admin-tabs">
          <Button
            variant={activeTab === "overview" ? "primary" : "outline-primary"}
            onClick={() => setActiveTab("overview")}
            className="me-2"
          >
            📊 Overview
          </Button>
          <Button
            variant={activeTab === "lots" ? "primary" : "outline-primary"}
            onClick={() => setActiveTab("lots")}
            className="me-2"
          >
            🅿️ Parking Lots
          </Button>
          <Button
            variant={activeTab === "bookings" ? "primary" : "outline-primary"}
            onClick={() => setActiveTab("bookings")}
            className="me-2"
          >
            📅 Bookings
          </Button>
          <Button
            variant={activeTab === "users" ? "primary" : "outline-primary"}
            onClick={() => setActiveTab("users")}
            className="me-2"
          >
            👥 Users
          </Button>
          <Button
            variant={activeTab === "analytics" ? "primary" : "outline-primary"}
            onClick={() => setActiveTab("analytics")}
          >
            📈 Analytics
          </Button>
        </div>

        {/* Overview Tab */}
        {activeTab === "overview" && stats && (
          <Row className="mt-4">
            <Col md={3} className="mb-4">
              <Card className="stat-card stat-primary">
                <Card.Body>
                  <div className="stat-icon">🅿️</div>
                  <h3>{stats.total_lots}</h3>
                  <p className="text-muted">Total Lots</p>
                </Card.Body>
              </Card>
            </Col>
            <Col md={3} className="mb-4">
              <Card className="stat-card stat-success">
                <Card.Body>
                  <div className="stat-icon">✅</div>
                  <h3>{stats.available_spots}</h3>
                  <p className="text-muted">Available Spots</p>
                </Card.Body>
              </Card>
            </Col>
            <Col md={3} className="mb-4">
              <Card className="stat-card stat-warning">
                <Card.Body>
                  <div className="stat-icon">👥</div>
                  <h3>{stats.total_users}</h3>
                  <p className="text-muted">Total Users</p>
                </Card.Body>
              </Card>
            </Col>
            <Col md={3} className="mb-4">
              <Card className="stat-card stat-info">
                <Card.Body>
                  <div className="stat-icon">💰</div>
                  <h3>₹{stats.total_revenue}</h3>
                  <p className="text-muted">Total Revenue</p>
                </Card.Body>
              </Card>
            </Col>
            <Col md={6} className="mb-4">
              <Card className="stat-card">
                <Card.Body>
                  <h5>Occupancy Rate</h5>
                  <div className="progress-container">
                    <div
                      className="progress-bar-fill"
                      style={{ width: `${stats.occupancy_rate}%` }}
                    >
                      {stats.occupancy_rate}%
                    </div>
                  </div>
                  <p className="mt-2">
                    {stats.occupied_spots} / {stats.total_spots} spots occupied
                  </p>
                </Card.Body>
              </Card>
            </Col>
            <Col md={6} className="mb-4">
              <Card className="stat-card">
                <Card.Body>
                  <h5>Quick Stats</h5>
                  <Row>
                    <Col>
                      <p className="mb-1">
                        <strong>Total Spots:</strong> {stats.total_spots}
                      </p>
                      <p className="mb-1">
                        <strong>Occupied:</strong> {stats.occupied_spots}
                      </p>
                    </Col>
                    <Col>
                      <p className="mb-1">
                        <strong>Bookings:</strong> {stats.total_bookings}
                      </p>
                      <p className="mb-1">
                        <strong>Available:</strong> {stats.available_spots}
                      </p>
                    </Col>
                  </Row>
                </Card.Body>
              </Card>
            </Col>
          </Row>
        )}

        {/* Parking Lots Tab */}
        {activeTab === "lots" && (
          <Card className="mt-4">
            <Card.Header className="d-flex justify-content-between align-items-center">
              <h5 className="mb-0">Manage Parking Lots</h5>
              <Button
                variant="success"
                onClick={() => setShowCreateLotModal(true)}
              >
                + Add New Lot
              </Button>
            </Card.Header>
            <Card.Body>
              <Table responsive hover>
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Name</th>
                    <th>Location</th>
                    <th>Total Spots</th>
                    <th>Available</th>
                    <th>Rate/Hour</th>
                    <th>Status</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {lots.map((lot) => (
                    <tr key={lot.lot_id}>
                      <td>{lot.lot_id}</td>
                      <td>{lot.lot_name}</td>
                      <td>{lot.location}</td>
                      <td>{lot.total_spots}</td>
                      <td>
                        <Badge
                          bg={
                            lot.available_spots > 10
                              ? "success"
                              : lot.available_spots > 0
                              ? "warning"
                              : "danger"
                          }
                        >
                          {lot.available_spots}
                        </Badge>
                      </td>
                      <td>₹{lot.hourly_rate}</td>
                      <td>
                        <Badge bg={lot.status === "open" ? "success" : "danger"}>
                          {lot.status}
                        </Badge>
                      </td>
                      <td>
                        <div className="d-flex gap-2">
                          <Button
                            size="sm"
                            variant="outline-primary"
                            onClick={() => handleEditLot(lot)}
                          >
                            Edit
                          </Button>
                          <Button
                            size="sm"
                            variant="outline-danger"
                            onClick={() => handleDeleteLot(lot.lot_id)}
                          >
                            Delete
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </Table>
            </Card.Body>
          </Card>
        )}

        {/* Bookings Tab */}
        {activeTab === "bookings" && (
          <Card className="mt-4">
            <Card.Header>
              <h5 className="mb-0">All Bookings ({bookings.length})</h5>
            </Card.Header>
            <Card.Body>
              {bookings.length === 0 ? (
                <Alert variant="info">No bookings found.</Alert>
              ) : (
                <Table responsive hover>
                  <thead>
                    <tr>
                      <th>ID</th>
                      <th>User</th>
                      <th>Lot</th>
                      <th>Start Time</th>
                      <th>End Time</th>
                      <th>Cost</th>
                      <th>Status</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {bookings.map((booking) => (
                      <tr key={booking.reservation_id || booking.booking_id}>
                        <td>
                          {booking.reservation_id || booking.booking_id}
                        </td>
                        <td>{booking.user_name || "N/A"}</td>
                        <td>{booking.lot_name || "N/A"}</td>
                        <td>
                          {booking.start_time
                            ? new Date(booking.start_time).toLocaleString()
                            : "N/A"}
                        </td>
                        <td>
                          {booking.end_time
                            ? new Date(booking.end_time).toLocaleString()
                            : "N/A"}
                        </td>
                        <td className="fw-bold" style={{color: '#10b981', textShadow: '0 0 8px rgba(16, 185, 129, 0.4)'}}>₹{parseFloat(booking.total_cost || 0).toFixed(2)}</td>
                        <td>
                          <Badge bg={
                            booking.status === "active" ? "success" :
                            booking.status === "completed" ? "primary" :
                            booking.status === "cancelled" ? "danger" :
                            "info"
                          }>
                            {booking.status || "active"}
                          </Badge>
                        </td>
                        <td>
                          <Button
                            size="sm"
                            variant="outline-danger"
                            onClick={() => handleDeleteBooking(booking.reservation_id || booking.booking_id)}
                          >
                            Delete
                          </Button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </Table>
              )}
            </Card.Body>
          </Card>
        )}

        {/* Users Tab */}
        {activeTab === "users" && (
          <Card className="mt-4">
            <Card.Header className="d-flex justify-content-between align-items-center">
              <h5 className="mb-0">All Users</h5>
              <Button
                variant="success"
                onClick={() => setShowCreateUserModal(true)}
              >
                + Add New User
              </Button>
            </Card.Header>
            <Card.Body>
              <Table responsive hover>
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Name</th>
                    <th>Email</th>
                    <th>Role</th>
                    <th>Joined</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((u) => (
                    <tr key={u.user_id}>
                      <td>{u.user_id}</td>
                      <td>{u.name}</td>
                      <td>{u.email}</td>
                      <td>
                        <Badge bg={u.role === "admin" ? "danger" : "primary"}>
                          {u.role}
                        </Badge>
                      </td>
                      <td>
                        {new Date(u.created_at).toLocaleDateString()}
                      </td>
                      <td>
                        <Button
                          size="sm"
                          variant="outline-danger"
                          onClick={() => handleDeleteUser(u.user_id)}
                          disabled={u.user_id === user?.user_id}
                        >
                          Delete
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </Table>
            </Card.Body>
          </Card>
        )}

        {/* Analytics Tab */}
        {activeTab === "analytics" && analytics && (
          <Row className="mt-4">
            <Col md={6} className="mb-4">
              <Card className="shadow-lg">
                <Card.Header>
                  <h5 className="mb-0">📊 Top Parking Lots by Revenue</h5>
                </Card.Header>
                <Card.Body>
                  {analytics.top_parking_lots && analytics.top_parking_lots.length > 0 ? (
                    <Table striped hover>
                      <thead>
                        <tr>
                          <th>Lot Name</th>
                          <th>Bookings</th>
                          <th>Revenue</th>
                        </tr>
                      </thead>
                      <tbody>
                        {analytics.top_parking_lots.map((lot, idx) => (
                          <tr key={idx}>
                            <td>{lot.lot_name}</td>
                            <td>{lot.total_bookings}</td>
                            <td className="fw-bold" style={{color: '#10b981', textShadow: '0 0 8px rgba(16, 185, 129, 0.4)'}}>₹{parseFloat(lot.revenue || 0).toFixed(2)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </Table>
                  ) : (
                    <Alert variant="info">No revenue data available</Alert>
                  )}
                </Card.Body>
              </Card>
            </Col>
            <Col md={6} className="mb-4">
              <Card className="shadow-lg">
                <Card.Header>
                  <h5 className="mb-0">📈 Booking Statistics</h5>
                </Card.Header>
                <Card.Body>
                  {analytics.booking_stats && (
                    <div>
                      <p><strong>Total Bookings:</strong> {analytics.booking_stats.total || 0}</p>
                      <p><strong>Active Bookings:</strong> {analytics.booking_stats.active || 0}</p>
                      <p><strong>Completed Bookings:</strong> {analytics.booking_stats.completed || 0}</p>
                    </div>
                  )}
                </Card.Body>
              </Card>
            </Col>
            <Col md={6} className="mb-4">
              <Card className="shadow-lg">
                <Card.Header>
                  <h5 className="mb-0">⭐ Lots with Revenue Above Average (Nested Query)</h5>
                  <small className="text-muted">This uses a nested subquery to find lots performing above average</small>
                </Card.Header>
                <Card.Body>
                  {analytics.above_avg_lots && analytics.above_avg_lots.length > 0 ? (
                    <Table striped hover>
                      <thead>
                        <tr>
                          <th>Lot Name</th>
                          <th>Location</th>
                          <th>Revenue</th>
                        </tr>
                      </thead>
                      <tbody>
                        {analytics.above_avg_lots.map((lot, idx) => (
                          <tr key={idx}>
                            <td>{lot.lot_name}</td>
                            <td>{lot.location}</td>
                            <td className="fw-bold" style={{color: '#10b981', textShadow: '0 0 8px rgba(16, 185, 129, 0.4)'}}>₹{parseFloat(lot.revenue || 0).toFixed(2)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </Table>
                  ) : (
                    <Alert variant="info">No lots found with revenue above average</Alert>
                  )}
                </Card.Body>
              </Card>
            </Col>
            <Col md={12} className="mb-4">
              <Card className="shadow-lg">
                <Card.Header>
                  <h5 className="mb-0">📅 Revenue by Day (Last 7 Days)</h5>
                </Card.Header>
                <Card.Body>
                  {analytics.revenue_by_day && analytics.revenue_by_day.length > 0 ? (
                    <Table striped hover>
                      <thead>
                        <tr>
                          <th>Date</th>
                          <th>Bookings</th>
                          <th>Revenue</th>
                        </tr>
                      </thead>
                      <tbody>
                        {analytics.revenue_by_day.map((day, idx) => (
                          <tr key={idx}>
                            <td>{new Date(day.date).toLocaleDateString()}</td>
                            <td>{day.bookings_count}</td>
                            <td className="fw-bold" style={{color: '#10b981', textShadow: '0 0 8px rgba(16, 185, 129, 0.4)'}}>₹{parseFloat(day.revenue || 0).toFixed(2)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </Table>
                  ) : (
                    <Alert variant="info">No revenue data for the last 7 days</Alert>
                  )}
                </Card.Body>
              </Card>
            </Col>
          </Row>
        )}
      </Container>

      {/* Edit Lot Modal */}
      <Modal show={showEditModal} onHide={() => setShowEditModal(false)}>
        <Modal.Header closeButton>
          <Modal.Title>Edit Parking Lot</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form>
            <Form.Group className="mb-3">
              <Form.Label>Lot Name</Form.Label>
              <Form.Control
                type="text"
                value={editForm.lot_name || ""}
                onChange={(e) =>
                  setEditForm({ ...editForm, lot_name: e.target.value })
                }
              />
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Location</Form.Label>
              <Form.Control
                type="text"
                value={editForm.location || ""}
                onChange={(e) =>
                  setEditForm({ ...editForm, location: e.target.value })
                }
              />
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Total Spots</Form.Label>
              <Form.Control
                type="number"
                value={editForm.total_spots || ""}
                onChange={(e) =>
                  setEditForm({ ...editForm, total_spots: parseInt(e.target.value) })
                }
              />
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Hourly Rate (₹)</Form.Label>
              <Form.Control
                type="number"
                step="0.01"
                value={editForm.hourly_rate || ""}
                onChange={(e) =>
                  setEditForm({ ...editForm, hourly_rate: parseFloat(e.target.value) })
                }
              />
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Status</Form.Label>
              <Form.Select
                value={editForm.status || "open"}
                onChange={(e) =>
                  setEditForm({ ...editForm, status: e.target.value })
                }
              >
                <option value="open">Open</option>
                <option value="closed">Closed</option>
              </Form.Select>
            </Form.Group>
          </Form>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowEditModal(false)}>
            Cancel
          </Button>
          <Button variant="primary" onClick={handleUpdateLot}>
            Save Changes
          </Button>
        </Modal.Footer>
      </Modal>

      {/* Create Lot Modal */}
      <Modal show={showCreateLotModal} onHide={() => setShowCreateLotModal(false)} size="lg">
        <Modal.Header closeButton>
          <Modal.Title>➕ Create New Parking Lot</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form>
            <Form.Group className="mb-3">
              <Form.Label>Lot Name *</Form.Label>
              <Form.Control
                type="text"
                placeholder="e.g., Downtown Plaza Lot"
                value={createLotForm.lot_name}
                onChange={(e) =>
                  setCreateLotForm({ ...createLotForm, lot_name: e.target.value })
                }
              />
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Location *</Form.Label>
              <Form.Control
                type="text"
                placeholder="e.g., Downtown, Main Street"
                value={createLotForm.location}
                onChange={(e) =>
                  setCreateLotForm({ ...createLotForm, location: e.target.value })
                }
              />
            </Form.Group>
            <Row>
              <Col md={6}>
                <Form.Group className="mb-3">
                  <Form.Label>Total Spots *</Form.Label>
                  <Form.Control
                    type="number"
                    min="1"
                    placeholder="e.g., 50"
                    value={createLotForm.total_spots}
                    onChange={(e) =>
                      setCreateLotForm({ ...createLotForm, total_spots: e.target.value })
                    }
                  />
                </Form.Group>
              </Col>
              <Col md={6}>
                <Form.Group className="mb-3">
                  <Form.Label>Hourly Rate (₹) *</Form.Label>
                  <Form.Control
                    type="number"
                    step="0.01"
                    min="0"
                    placeholder="e.g., 30.00"
                    value={createLotForm.hourly_rate}
                    onChange={(e) =>
                      setCreateLotForm({ ...createLotForm, hourly_rate: e.target.value })
                    }
                  />
                </Form.Group>
              </Col>
            </Row>
            <Form.Group className="mb-3">
              <Form.Label>Status</Form.Label>
              <Form.Select
                value={createLotForm.status}
                onChange={(e) =>
                  setCreateLotForm({ ...createLotForm, status: e.target.value })
                }
              >
                <option value="open">Open</option>
                <option value="closed">Closed</option>
              </Form.Select>
            </Form.Group>
          </Form>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowCreateLotModal(false)}>
            Cancel
          </Button>
          <Button variant="success" onClick={handleCreateLot}>
            Create Lot
          </Button>
        </Modal.Footer>
      </Modal>

      {/* Create User Modal */}
      <Modal show={showCreateUserModal} onHide={() => setShowCreateUserModal(false)}>
        <Modal.Header closeButton>
          <Modal.Title>➕ Create New User</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form>
            <Form.Group className="mb-3">
              <Form.Label>Name *</Form.Label>
              <Form.Control
                type="text"
                placeholder="Full Name"
                value={createUserForm.name}
                onChange={(e) =>
                  setCreateUserForm({ ...createUserForm, name: e.target.value })
                }
              />
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Email *</Form.Label>
              <Form.Control
                type="email"
                placeholder="user@example.com"
                value={createUserForm.email}
                onChange={(e) =>
                  setCreateUserForm({ ...createUserForm, email: e.target.value })
                }
              />
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Password *</Form.Label>
              <Form.Control
                type="password"
                placeholder="Enter password"
                value={createUserForm.password}
                onChange={(e) =>
                  setCreateUserForm({ ...createUserForm, password: e.target.value })
                }
              />
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Role</Form.Label>
              <Form.Select
                value={createUserForm.role}
                onChange={(e) =>
                  setCreateUserForm({ ...createUserForm, role: e.target.value })
                }
              >
                <option value="driver">Driver</option>
                <option value="admin">Admin</option>
              </Form.Select>
            </Form.Group>
          </Form>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowCreateUserModal(false)}>
            Cancel
          </Button>
          <Button variant="success" onClick={handleCreateUser}>
            Create User
          </Button>
        </Modal.Footer>
      </Modal>
    </div>
  );
}

export default AdminDashboard;

