import React, { useEffect, useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import axios from "axios";
import { Card, Spinner, Alert, Container, Row, Col, Button, Badge, Table } from "react-bootstrap";
import { useAuth } from "../context/AuthContext1";
import "../styles/Dashboard.css";

function Dashboard() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [lots, setLots] = useState([]);
  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [activeTab, setActiveTab] = useState("lots");

  const fetchLots = async () => {
    try {
      const res = await axios.get("http://127.0.0.1:8000/parking/lots");
      setLots(res.data.parking_lots);
    } catch (err) {
      setError("Failed to load parking lots");
    }
  };

  const fetchBookings = async () => {
    if (!user?.user_id) return;
    try {
      const res = await axios.get(`http://127.0.0.1:8000/parking/bookings/${user.user_id}`);
      setBookings(res.data.bookings || []);
    } catch (err) {
      setBookings([]);
    }
  };

  const handleCancelBooking = async (reservationId) => {
    if (!window.confirm("Are you sure you want to cancel this booking? The parking spot will be freed up and made available for others.")) {
      return;
    }

    try {
      await axios.put(`http://127.0.0.1:8000/parking/bookings/${reservationId}/cancel`);
      await Promise.all([fetchBookings(), fetchLots()]);
      alert("Booking cancelled successfully!");
    } catch (err) {
      const errorMsg = err.response?.data?.detail || "Failed to cancel booking";
      alert(errorMsg);
    }
  };

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await Promise.all([fetchLots(), fetchBookings()]);
      setLoading(false);
    };
    loadData();
    
    const params = new URLSearchParams(location.search);
    const tabParam = params.get("tab");
    if (tabParam) {
      setActiveTab(tabParam);
    }
  }, [user, location.search]);

  useEffect(() => {
    const handleFocus = () => {
      fetchLots();
      fetchBookings();
    };
    window.addEventListener('focus', handleFocus);
    
    const handleVisibilityChange = () => {
      if (!document.hidden) {
        fetchLots();
        fetchBookings();
      }
    };
    document.addEventListener('visibilitychange', handleVisibilityChange);
    
    return () => {
      window.removeEventListener('focus', handleFocus);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [user]);

  if (loading)
    return (
      <div className="dashboard-loading">
        <Spinner animation="border" variant="primary" />
        <p>Loading parking lots...</p>
      </div>
    );

  if (error)
    return (
      <Alert variant="danger" className="mt-4 text-center">
        {error}
      </Alert>
    );

  return (
    <div className="dashboard-wrapper">
      <div className="dashboard-header">
        <Container fluid>
          <Row className="align-items-center">
            <Col>
              <h2 className="mb-0">
                <span className="dashboard-icon">P</span> Smart Parking System
              </h2>
              <p className="text-muted mb-0">Welcome, {user?.name || "User"}</p>
            </Col>
            <Col xs="auto" className="d-flex gap-2">
              {user?.role === "admin" && (
                <Button
                  variant="outline-primary"
                  onClick={() => navigate("/admin")}
                >
                  Admin Dashboard
                </Button>
              )}
              <Button variant="outline-danger" onClick={logout}>
                Logout
              </Button>
            </Col>
          </Row>
        </Container>
      </div>

      <Container className="mt-4">
        <div className="mb-4 text-center">
          <Button
            variant={activeTab === "lots" ? "primary" : "outline-primary"}
            onClick={() => setActiveTab("lots")}
            className="me-2"
          >
            Parking Lots
          </Button>
          <Button
            variant={activeTab === "bookings" ? "primary" : "outline-primary"}
            onClick={() => setActiveTab("bookings")}
          >
            My Bookings
          </Button>
        </div>

        {activeTab === "lots" && (
          <>
            <Row className="mb-4">
              <Col>
                <h3 className="text-center">Available Parking Lots</h3>
                <p className="text-center text-muted">
                  Select a parking lot to book your spot
                </p>
              </Col>
            </Row>
            <Row>
          {lots.map((lot) => (
            <Col md={4} lg={3} key={lot.lot_id} className="mb-4">
              <Card className="lot-card shadow-lg">
                <Card.Body className="p-4 position-relative">
                  <div className="lot-status-badge">
                    <Badge
                      bg={
                        lot.available_spots > 10
                          ? "success"
                          : lot.available_spots > 0
                          ? "warning"
                          : "danger"
                      }
                      className="status-badge"
                    >
                      {lot.status === "open" ? "Open" : "Closed"}
                    </Badge>
                  </div>
                  <Card.Title className="fw-bold mt-2 mb-3">
                    {lot.lot_name}
                  </Card.Title>
                  <Card.Text className="text-muted mb-3">
                    <span>{lot.location}</span>
                  </Card.Text>
                  <div className="lot-info mb-3">
                    <div className="info-item">
                      <span className="info-label">Available:</span>
                      <span className="info-value">
                        {lot.available_spots} / {lot.total_spots}
                      </span>
                    </div>
                    <div className="info-item">
                      <span className="info-label">Rate:</span>
                      <span className="info-value">₹{lot.hourly_rate}/hr</span>
                    </div>
                  </div>
                  <Button
                    variant={lot.available_spots > 0 && lot.status === "open" ? "success" : "secondary"}
                    className="w-100"
                    onClick={() => navigate(`/book/${lot.lot_id}`)}
                    disabled={lot.available_spots === 0 || lot.status !== "open"}
                  >
                    {lot.available_spots > 0 && lot.status === "open"
                      ? "Book Now"
                      : "Not Available"}
                  </Button>
                </Card.Body>
              </Card>
            </Col>
          ))}
        </Row>
        </>
        )}

        {activeTab === "bookings" && (
          <Row>
            <Col>
              <Card className="shadow-lg">
                <Card.Header>
                  <h4 className="mb-0">My Bookings</h4>
                </Card.Header>
                <Card.Body>
                  {bookings.length === 0 ? (
                    <Alert variant="info" className="text-center">
                      <p className="mb-0">No bookings yet. Book a parking spot to see your bookings here!</p>
                    </Alert>
                  ) : (
                    <div className="table-responsive">
                      <table className="table table-hover">
                        <thead>
                          <tr>
                            <th>Booking ID</th>
                            <th>Parking Lot</th>
                            <th>Location</th>
                            <th>Start Time</th>
                            <th>End Time</th>
                            <th>Duration</th>
                            <th>Total Cost</th>
                            <th>Status</th>
                            <th>Actions</th>
                          </tr>
                        </thead>
                        <tbody>
                          {bookings.map((booking) => {
                            const start = new Date(booking.start_time);
                            const end = new Date(booking.end_time);
                            const hours = Math.ceil((end - start) / (1000 * 60 * 60));
                            const isActive = booking.status === "active";
                            const canCancel = isActive;
                            return (
                              <tr key={booking.reservation_id}>
                                <td>#{booking.reservation_id}</td>
                                <td>{booking.lot_name}</td>
                                <td>{booking.location}</td>
                                <td>{start.toLocaleString()}</td>
                                <td>{end.toLocaleString()}</td>
                                <td>{hours} hour{hours !== 1 ? 's' : ''}</td>
                                <td className="fw-bold" style={{color: '#10b981', textShadow: '0 0 8px rgba(16, 185, 129, 0.4)'}}>₹{parseFloat(booking.total_cost).toFixed(2)}</td>
                                <td>
                                  <Badge
                                    bg={
                                      booking.status === "active"
                                        ? "success"
                                        : booking.status === "completed"
                                        ? "primary"
                                        : booking.status === "cancelled"
                                        ? "danger"
                                        : "secondary"
                                    }
                                  >
                                    {booking.status}
                                  </Badge>
                                </td>
                                <td>
                                  {canCancel && (
                                    <Button
                                      variant="outline-danger"
                                      size="sm"
                                      onClick={() => handleCancelBooking(booking.reservation_id)}
                                      className="cancel-btn"
                                    >
                                      Cancel
                                    </Button>
                                  )}
                                  {!canCancel && <span className="text-muted" style={{color: '#888888'}}>-</span>}
                                </td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                      <div className="mt-3 p-3 bg-light rounded" style={{background: 'rgba(18, 18, 32, 0.6)', border: '1px solid rgba(255, 255, 255, 0.1)'}}>
                        <strong style={{color: '#ffffff'}}>Total Spent: </strong>
                        <span className="text-success fw-bold fs-5" style={{color: '#10b981', textShadow: '0 0 10px rgba(16, 185, 129, 0.5)'}}>
                          ₹{bookings
                            .filter(b => b.status !== 'cancelled')
                            .reduce((sum, b) => sum + parseFloat(b.total_cost || 0), 0).toFixed(2)}
                        </span>
                        <p className="text-muted mb-0 mt-2 small" style={{color: '#888888'}}>
                          Active Bookings: {bookings.filter(b => b.status === 'active').length} | 
                          Completed: {bookings.filter(b => b.status === 'completed').length} | 
                          Cancelled: {bookings.filter(b => b.status === 'cancelled').length}
                        </p>
                      </div>
                    </div>
                  )}
                </Card.Body>
              </Card>
            </Col>
          </Row>
        )}
      </Container>
    </div>
  );
}

export default Dashboard;
