import React, { useEffect, useState } from 'react';
import { Canvas, useLoader } from '@react-three/fiber';
import { OrbitControls, Sphere } from '@react-three/drei';
import axios from 'axios';
import * as THREE from 'three';
import { MeshLineGeometry, MeshLineMaterial, raycast } from 'meshline'

function AirportNodes({ airports, onSelect }) {
  return airports.map((airport, idx) => (
    <mesh
      key={idx}
      position={latLonToXYZ(airport.lat, airport.lon, 1.01)}
      onClick={() => onSelect(airport)}
    >
      <sphereGeometry args={[0.005, 16, 16]} />
      <meshStandardMaterial color="orange" />
    </mesh>
  ));
}

/* function Routes({ airports, routes, highlightedRoutes = [] }) {
  const airportMap = Object.fromEntries(airports.map(a => [a.id, a]));

  const highlightedRoutesSet = new Set();
  highlightedRoutes.forEach(route => {
    //const key = `${route.source}-${route.target}`;
    const key = [route.source, route.target].sort().join('-');
    highlightedRoutesSet.add(key);
  });

  return routes.map((route, idx) => {
    const origin = airportMap[route.source];
    const dest = airportMap[route.target];

    if (!origin || !dest) return null;

    const start = latLonToXYZ(origin.lat, origin.lon, 1.01);
    const end = latLonToXYZ(dest.lat, dest.lon, 1.01);

    // Get midpoint for arc
    const midPoint = new THREE.Vector3().addVectors(start, end).multiplyScalar(0.5).normalize();
    const distance = start.distanceTo(end);

    // Choose an arc height factor — tweakable
    const arcHeightFactor = 0.45; // increase for more dramatic arcs
    const arcHeight = 1.01 + arcHeightFactor * distance;

    const arcMid = midPoint.multiplyScalar(arcHeight);
    const curve = new THREE.QuadraticBezierCurve3(start, arcMid, end);
    const points = curve.getPoints(50);
    const geometry = new THREE.BufferGeometry().setFromPoints(points);

    //const routeKey = `${route.source}-${route.target}`;
    const routeKey = [route.source, route.target].sort().join('-');
    const isHighlighted = highlightedRoutesSet.has(routeKey);
    const lineColor = isHighlighted ? "green" : "aqua";
    const lineWidth = isHighlighted ? 5 : 3;

    return (
      <line key={idx} geometry={geometry}>
        <lineBasicMaterial color={lineColor} linewidth={lineWidth}/>
      </line>
    );
  });
} */

  function Routes({ airports, routes, highlightedRoutes = [] }) {
    const airportMap = Object.fromEntries(airports.map(a => [a.id, a]));
  
    const highlightedRoutesSet = new Set();
    highlightedRoutes.forEach(route => {
      const key = [route.source, route.target].sort().join('-');
      highlightedRoutesSet.add(key);
    });
  
    return routes.map((route, idx) => {
      const origin = airportMap[route.source];
      const dest = airportMap[route.target];
  
      if (!origin || !dest) return null;
  
      const start = latLonToXYZ(origin.lat, origin.lon, 1.01);
      const end = latLonToXYZ(dest.lat, dest.lon, 1.01);
  
      const midPoint = new THREE.Vector3().addVectors(start, end).multiplyScalar(0.5).normalize();
      const distance = start.distanceTo(end);
  
      const arcHeightFactor = 0.45;
      const arcHeight = 1.01 + arcHeightFactor * distance;
      const arcMid = midPoint.multiplyScalar(arcHeight);
      const curve = new THREE.QuadraticBezierCurve3(start, arcMid, end);
      const points = curve.getPoints(50);
  
      // Create MeshLineGeometry and set points
      const geometry = new MeshLineGeometry();
      const pointArray = points.map(p => [p.x, p.y, p.z]);
      geometry.setPoints(pointArray, (p) => 0.0005);
  
      // Define whether this route is highlighted
      const routeKey = [route.source, route.target].sort().join('-');
      const isHighlighted = highlightedRoutesSet.has(routeKey);
      const lineColor = isHighlighted ? "green" : "aqua";
      const lineWidth = isHighlighted ? 13 : 3;
  
      // Create MeshLineMaterial
      const material = new MeshLineMaterial({
        color: new THREE.Color(lineColor),
        lineWidth: lineWidth,
        sizeAttenuation: 1, // constant line width
        transparent: true,
        opacity: 1, // set as needed
      });
  
      // Create MeshLine Mesh
      const mesh = new THREE.Mesh(geometry, material);
      mesh.raycast = raycast;
  
      return <primitive key={idx} object={mesh} />;
    });
  }

function GlobeComponent({ schedulingExternal, setSchedulingExternal }) {
  const [airports, setAirports] = useState([]);
  const [routes, setRoutes] = useState([]);
  const [selectedAirport, setSelectedAirport] = useState(null);

  const [scheduling, setScheduling] = useState(false); 
  const [step, setStep] = useState(null);
  const [origin, setOrigin] = useState(null);
  const [destination, setDestination] = useState(null);
  const [departureTime, setDepartureTime] = useState('');

  const [trips, setTrips] = useState([]);
  const [selectedTrip, setSelectedTrip] = useState(null);
  const [highlightedRoutes, setHighlightedRoutes] = useState([]);
  const [showTrips, setShowTrips] = useState(false);

  const earthTexture = useLoader(THREE.TextureLoader, 'earth_texture.png');

  useEffect(() => {
    axios.get('/api/globe-data/').then(res => {
      setAirports(res.data.nodes);
      setRoutes(res.data.links);
    });

    fetchTrips();
  }, []);

  const fetchTrips = () => {
    axios.get('/api/trips/')
      .then(res => {
        console.log(res)
        setTrips(res.data.trips);
      })
      .catch(err => console.error("Failed to fetch trips", err));
  };

  useEffect(() => {
    if (schedulingExternal) {
      startSchedulingFlow();
      setSchedulingExternal(false); // reset the external trigger
    }
  }, [schedulingExternal, setSchedulingExternal]);

  const startSchedulingFlow = () => {
    setScheduling(true);
    setStep('selectOrigin');
    setSelectedAirport(null);
    setOrigin(null);
    setDestination(null);
    setDepartureTime('');
    setSelectedTrip(null);
    setHighlightedRoutes([]);
  };

  const resetSchedulingFlow = () => {
    setScheduling(false);
    setStep(null);
    setOrigin(null);
    setDestination(null);
    setDepartureTime('');
    setSelectedAirport(null);
  };

  const handleAirportClick = (airport) => {
    if (scheduling) {
      if (step === 'selectOrigin') {
        setOrigin(airport);
        setStep('setTime');
      } else if (step === 'selectDestination') {
        setDestination(airport);
      }
    } else {
      axios.get(`/api/airport/${airport.id}/`)
        .then(res => {
          setSelectedAirport(res.data)
          setSelectedTrip(null);
          setHighlightedRoutes([]);
        })
        .catch(err => console.error("Failed to fetch airport details", err));
    }
  };

  const confirmOriginAndTime = () => {
    if (departureTime && origin) {
      setStep('selectDestination');
    }
  };

  const confirmDestination = () => {
    if (origin && destination && departureTime) {
      axios.post('/api/compute_trip/', {
        origin_id: origin.id,
        destination_id: destination.id,
        departure_time: departureTime,
      })
        .then(res => {
          console.log("Response from server:", res);
          alert("Flight scheduled successfully!");
          resetSchedulingFlow();

          fetchTrips();
        })
        .catch(err => {
          console.error("Failed to schedule flight", err);
          alert("Error scheduling flight.");
        });
    }
  };

  const handleTripSelect = (tripId) => {
    setSelectedAirport(null);
    
    if (selectedTrip && selectedTrip.id === tripId) {
      setSelectedTrip(null);
      setHighlightedRoutes([]);
    } else {
      axios.get(`/api/trips/${tripId}/`)
        .then(res => {
          setSelectedTrip(res.data);
          setHighlightedRoutes(res.data.route_segments);
        })
        .catch(err => console.error("Failed to fetch trip details", err));
    }
  };

  const toggleTripsPanel = () => {
    setShowTrips(!showTrips);
    if (!showTrips) {
      fetchTrips(); 
    }
  };

  return (
    <>
      <Canvas 
        camera={{ position: [0, 0, 2.5] }}
        style={{ background: 'black' }}
      >
        <ambientLight />
        <directionalLight position={[0, 0, 400]} />
        <OrbitControls />
        <Sphere args={[1, 64, 64]}>
          <meshStandardMaterial map={earthTexture} />
        </Sphere>
        <AirportNodes airports={airports} onSelect={handleAirportClick} />
        <Routes airports={airports} routes={routes} highlightedRoutes={highlightedRoutes}/>
      </Canvas>

      <div className="control-buttons">
        <button 
          onClick={startSchedulingFlow} 
          className="action-button schedule-button"
        >
          Schedule Flight
        </button>
        <button 
          onClick={toggleTripsPanel} 
          className="action-button view-trips-button"
        >
          {showTrips ? 'Hide Trips' : 'View Trips'}
        </button>
      </div>

      { scheduling && (
        <div className="scheduler-panel">
          <h3>Flight Scheduler</h3>
          {step === 'selectOrigin' && (
            <p>Select a <strong>departure airport</strong> by clicking on the globe.</p>
          )}
          {step === 'setTime' && origin && (
            <>
              <p><b>Departure Airport:</b> {origin.name}</p>
              <label>
                Departure Time:
                <input 
                  type="datetime-local" 
                  value={departureTime} 
                  onChange={e => setDepartureTime(e.target.value)} 
                  className="full-width-input"
                />
              </label>
              <button onClick={confirmOriginAndTime} className="confirm-button">
                Confirm Departure Time
              </button>
            </>
          )}
          {step === 'selectDestination' && (
            <>
              <p><b>Departure Airport:</b> {origin?.name}</p>
              <p><b>Departure Time:</b> {new Date(departureTime).toLocaleString()}</p>
              {destination ? (
                <>
                  <p><b>Destination Airport:</b> {destination.name}</p>
                  <button onClick={confirmDestination}>Confirm & Schedule Flight</button>
                </>
              ) : (
                <p>Select a <strong>destination airport</strong> by clicking on the globe.</p>
              )}
            </>
          )}
          <button onClick={resetSchedulingFlow} className="cancel-button">
            Cancel
          </button>
        </div>
      )}

      { selectedAirport && !scheduling && (
        <div className="selected-airport-panel">
          <h3>{selectedAirport.name || 'Unknown Airport'}</h3>
          <p><b>Code:</b> {selectedAirport.code || selectedAirport.id}</p>
          <p><b>Latitude:</b> {selectedAirport.latitude ?? selectedAirport.lat}</p>
          <p><b>Longitude:</b> {selectedAirport.longitude ?? selectedAirport.lon}</p>

          <div style={{ marginTop: '1em' }}>
            <h4>Departures</h4>
            {selectedAirport.departures?.length > 0 ? (
              <ul>
                {selectedAirport.departures.map((flight, idx) => (
                  <li key={idx}>
                    <b>{flight.flight_number}</b> to {flight.destination_name || flight.destination} at {new Date(flight.departure_time).toLocaleTimeString()}
                  </li>
                ))}
              </ul>
            ) : (
              <p>No scheduled departures.</p>
            )}

            <h4>Arrivals</h4>
            {selectedAirport.arrivals?.length > 0 ? (
              <ul>
                {selectedAirport.arrivals.map((flight, idx) => (
                  <li key={idx}>
                    <b>{flight.flight_number}</b> from {flight.origin_name || flight.origin} at {new Date(flight.arrival_time).toLocaleTimeString()}
                  </li>
                ))}
              </ul>
            ) : (
              <p>No scheduled arrivals.</p>
            )}
          </div>
        </div>
      )}

      { showTrips && (
        <div className="trips-panel">
          <h3>Scheduled Trips</h3>
          <div className="trips-list">
            {trips.length > 0 ? (
              trips.map(trip => (
                <div 
                  key={trip.id} 
                  className={`trip-card ${selectedTrip && selectedTrip.id === trip.id ? 'selected' : ''}`}
                  onClick={() => handleTripSelect(trip.id)}
                >
                  <div className="trip-header">
                    <div className="trip-airports">
                      <span className="trip-origin">{trip.origin_code}</span>
                      <span className="trip-arrow">→</span>
                      <span className="trip-destination">{trip.destination_code}</span>
                    </div>
                    <div className="trip-flight-count">{trip.num_flights} flight{trip.num_flights !== 1 ? 's' : ''}</div>
                  </div>
                  <div className="trip-details">
                    <div>
                      <div className="detail-label">Departure:</div>
                      <div className="detail-value">{new Date(trip.departure_time).toLocaleString()}</div>
                    </div>
                    <div>
                      <div className="detail-label">Arrival:</div>
                      <div className="detail-value">{new Date(trip.arrival_time).toLocaleString()}</div>
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <p>No trips scheduled yet.</p>
            )}
          </div>
        </div>
      )}

      { selectedTrip && (
        <div className="selected-trip-panel">
          <h3>Trip Details</h3>
          <div className="trip-overview">
            <h4>{selectedTrip.origin_name} ({selectedTrip.origin_code}) → {selectedTrip.destination_name} ({selectedTrip.destination_code})</h4>
            <p><b>Departure:</b> {new Date(selectedTrip.flights[0].departure_time).toLocaleString()}</p>
            <p><b>Arrival:</b> {new Date(selectedTrip.flights[selectedTrip.flights.length - 1].arrival_time).toLocaleString()}</p>
          </div>
          
          <div className="trip-flights">
            <h4>Flight Segments</h4>
            <div className="flight-segments">
              {selectedTrip.flights.map((flight, idx) => (
                <div key={idx} className="flight-segment">
                  <div className="flight-number">{flight.flight_number}</div>
                  <div className="segment-details">
                    <div className="segment-airports">
                      <span>{flight.origin_code}</span>
                      <span className="segment-arrow">→</span>
                      <span>{flight.destination_code}</span>
                    </div>
                    <div className="segment-times">
                      <div>{new Date(flight.departure_time).toLocaleTimeString()} - {new Date(flight.arrival_time).toLocaleTimeString()}</div>
                      <div className="segment-date">{new Date(flight.departure_time).toLocaleDateString()}</div>
                    </div>
                  </div>
                  <div className="flight-status">{flight.status}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </>
  );
}

// Converts latitude/longitude to Cartesian coords on a sphere
function latLonToXYZ(lat, lon, radius) {
  const phi = (90 - lat) * (Math.PI / 180);
  const theta = (lon + 180) * (Math.PI / 180);

  const x = -radius * Math.sin(phi) * Math.cos(theta);
  const y = radius * Math.cos(phi);
  const z = radius * Math.sin(phi) * Math.sin(theta);

  return new THREE.Vector3(x, y, z);
}

export default GlobeComponent;