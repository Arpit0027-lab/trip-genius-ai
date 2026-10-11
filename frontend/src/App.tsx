import { useState } from "react";
import "./App.css";

interface Activity {
  time: string;
  activity: string;
  estimated_cost: number;
}

interface DayPlan {
  day: number;
  title: string;
  activities: Activity[];
}

interface Itinerary {
  destination: string;
  summary: string;
  days: DayPlan[];
  estimated_total_cost: number;
  travel_tips: string[];
}

interface SavedTrip {
  id: string;
  starting_city: string;
  destination: string;
  start_date: string;
  end_date: string;
  budget: number;
  travelers: number;
  interests: string[];
  travel_style: string;
  created_at: string;
  itineraries: {
    id: string;
    summary: string;
    itinerary_data: Itinerary;
    estimated_total_cost: number;
  }[];
}

function App() {
  const [form, setForm] = useState({
    starting_city: "Bhopal",
    destination: "",
    start_date: "",
    end_date: "",
    budget: "8000",
    travelers: "2",
    interests: "Nature, Sightseeing, Food",
    travel_style: "Adventure",
  });

  const [itinerary, setItinerary] = useState<Itinerary | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [savedTrips, setSavedTrips] = useState<SavedTrip[]>([]);
  const [tripsLoading, setTripsLoading] = useState(false);
  const [tripsError, setTripsError] = useState("");
  const [selectedTrip, setSelectedTrip] = useState<Itinerary | null>(null);

  const handleChange = (
    event: React.ChangeEvent<
      HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement
    >
  ) => {
    setForm({ ...form, [event.target.name]: event.target.value });
  };

  const loadSavedTrips = async () => {
    setTripsLoading(true);
    setTripsError("");

    try {
      const response = await fetch("http://127.0.0.1:8000/api/trips");

      if (!response.ok) {
        throw new Error("Could not load saved trips.");
      }

      const data = await response.json();
      setSavedTrips(data.trips ?? []);
    } catch (err) {
      setTripsError(
        err instanceof Error ? err.message : "Something went wrong."
      );
    } finally {
      setTripsLoading(false);
    }
  };

  const openSavedTrip = async (tripId: string) => {
    setTripsError("");

    try {
      const response = await fetch(
        `http://127.0.0.1:8000/api/trips/${tripId}`
      );

      if (!response.ok) {
        throw new Error("Could not open this trip.");
      }

      const trip: SavedTrip = await response.json();

      if (!trip.itineraries?.length) {
        throw new Error("No itinerary was found for this trip.");
      }

      setSelectedTrip(trip.itineraries[0].itinerary_data);

      setTimeout(() => {
        document.getElementById("saved-itinerary")?.scrollIntoView({
          behavior: "smooth",
          block: "start",
        });
      }, 100);
    } catch (err) {
      setTripsError(
        err instanceof Error ? err.message : "Could not open this trip."
      );
    }
  };

  const generateItinerary = async (
    event: React.FormEvent<HTMLFormElement>
  ) => {
    event.preventDefault();
    setLoading(true);
    setError("");
    setItinerary(null);
    setSelectedTrip(null);

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/api/itinerary",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            ...form,
            budget: Number(form.budget),
            travelers: Number(form.travelers),
            interests: form.interests
              .split(",")
              .map((interest) => interest.trim())
              .filter(Boolean),
          }),
        }
      );

      if (!response.ok) {
        const details = await response.text();
        throw new Error(details || "Failed to generate itinerary.");
      }

      const data: Itinerary = await response.json();
      setItinerary(data);

      // Refresh the saved trips after successfully generating a trip.
      try {
        const tripsResponse = await fetch(
          "http://127.0.0.1:8000/api/trips"
        );

        if (tripsResponse.ok) {
          const tripsData = await tripsResponse.json();
          setSavedTrips(tripsData.trips ?? []);
        }
      } catch {
        // The generated itinerary can still be displayed if refreshing fails.
      }
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Something went wrong. Please try again."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="app">
      <header className="hero">
        <div className="brand">✈ Trip Genius AI</div>

        <p className="eyebrow">YOUR NEXT ADVENTURE STARTS HERE</p>

        <h1>
          Travel smarter.
          <br />
          Explore further.
        </h1>

        <p className="hero-text">
          Your personal AI travel planner creates itineraries around your
          interests, budget, and travel style.
        </p>
      </header>

      <section className="planner">
        <div className="section-heading">
          <span className="step-label">PERSONALIZED TRAVEL PLANNER</span>
          <h2>Plan your perfect trip</h2>
          <p>Tell us what you love. Let AI plan the rest.</p>
        </div>

        <form onSubmit={generateItinerary}>
          <div className="form-grid">
            <label>
              Starting city
              <input
                name="starting_city"
                value={form.starting_city}
                onChange={handleChange}
                required
              />
            </label>

            <label>
              Destination
              <input
                name="destination"
                placeholder="e.g. Pachmarhi"
                value={form.destination}
                onChange={handleChange}
                required
              />
            </label>

            <label>
              Start date
              <input
                type="date"
                name="start_date"
                value={form.start_date}
                onChange={handleChange}
                required
              />
            </label>

            <label>
              End date
              <input
                type="date"
                name="end_date"
                value={form.end_date}
                min={form.start_date || undefined}
                onChange={handleChange}
                required
              />
            </label>

            <label>
              Total budget (₹)
              <input
                type="number"
                name="budget"
                min="1"
                value={form.budget}
                onChange={handleChange}
                required
              />
            </label>

            <label>
              Number of travelers
              <input
                type="number"
                name="travelers"
                min="1"
                max="50"
                value={form.travelers}
                onChange={handleChange}
                required
              />
            </label>

            <label className="full-width">
              Your interests
              <input
                name="interests"
                value={form.interests}
                onChange={handleChange}
                placeholder="Nature, Food, Adventure"
                required
              />
              <small>Separate interests with commas.</small>
            </label>

            <label className="full-width">
              Travel style
              <select
                name="travel_style"
                value={form.travel_style}
                onChange={handleChange}
              >
                <option>Adventure</option>
                <option>Relaxation</option>
                <option>Luxury</option>
                <option>Budget</option>
                <option>Family</option>
                <option>Romantic</option>
                <option>Cultural</option>
              </select>
            </label>
          </div>

          <button className="generate-button" disabled={loading}>
            {loading
              ? "✨ Creating your itinerary..."
              : "✨ Generate My Itinerary"}
          </button>
        </form>

        {error && <div className="error-box">{error}</div>}
      </section>

      {/* Saved Trips Section */}
      <section className="saved-trips">
        <div className="saved-trips-heading">
          <div>
            <span className="step-label">YOUR TRAVEL COLLECTION</span>
            <h2>Saved Trips</h2>
            <p>Revisit your previously generated adventures.</p>
          </div>

          <button
            type="button"
            className="refresh-button"
            onClick={loadSavedTrips}
            disabled={tripsLoading}
          >
            {tripsLoading ? "Loading..." : "↻ Load Trips"}
          </button>
        </div>

        {tripsError && <div className="error-box">{tripsError}</div>}

        {!tripsLoading && savedTrips.length === 0 && (
          <p className="empty-trips">
            Click "Load Trips" to see your saved journeys.
          </p>
        )}

        <div className="saved-trips-grid">
          {savedTrips.map((trip) => (
            <article className="saved-trip-card" key={trip.id}>
              <span className="day-number">{trip.travel_style}</span>

              <h3>📍 {trip.destination}</h3>

              <p>
                {trip.start_date} → {trip.end_date}
              </p>

              <p>
                {trip.travelers} traveler(s) · Budget ₹
                {Number(trip.budget).toLocaleString("en-IN")}
              </p>

              <button
                type="button"
                className="view-trip-button"
                onClick={() => openSavedTrip(trip.id)}
              >
                View Itinerary →
              </button>
            </article>
          ))}
        </div>
      </section>

      {/* Newly Generated Itinerary */}
      {itinerary && (
        <section className="results">
          <div className="results-header">
            <span className="step-label">YOUR PERSONALIZED JOURNEY</span>

            <h2>{itinerary.destination} ✨</h2>

            <p>{itinerary.summary}</p>

            <div className="budget-card">
              <span>Estimated total budget</span>
              <strong>
                ₹{itinerary.estimated_total_cost.toLocaleString("en-IN")}
              </strong>
            </div>
          </div>

          <h3 className="subheading">Your day-by-day itinerary</h3>

          {itinerary.days.map((day) => (
            <article className="day-card" key={day.day}>
              <div className="day-heading">
                <span className="day-number">DAY {day.day}</span>
                <h3>{day.title}</h3>
              </div>

              {day.activities.map((activity, index) => (
                <div
                  className="activity"
                  key={`${day.day}-${index}`}
                >
                  <div className="activity-dot" />

                  <div className="activity-content">
                    <span className="activity-time">
                      {activity.time}
                    </span>
                    <p>{activity.activity}</p>
                  </div>

                  <strong>
                    ₹{activity.estimated_cost.toLocaleString("en-IN")}
                  </strong>
                </div>
              ))}
            </article>
          ))}

          <div className="tips-card">
            <h3>💡 Travel tips</h3>
            <ul>
              {itinerary.travel_tips.map((tip, index) => (
                <li key={index}>{tip}</li>
              ))}
            </ul>
          </div>

          <button
            type="button"
            className="print-button"
            onClick={() => window.print()}
          >
            Print / Save as PDF
          </button>

          <p className="disclaimer">
            AI-generated estimates are indicative, not verified live prices.
            Confirm transport, entry fees, and opening hours before traveling.
          </p>
        </section>
      )}

      {/* Previously Saved Itinerary */}
      {selectedTrip && (
        <section className="results" id="saved-itinerary">
          <div className="results-header">
            <span className="step-label">YOUR SAVED JOURNEY</span>

            <h2>{selectedTrip.destination} ✨</h2>

            <p>{selectedTrip.summary}</p>

            <div className="budget-card">
              <span>Estimated total budget</span>
              <strong>
                ₹
                {selectedTrip.estimated_total_cost.toLocaleString("en-IN")}
              </strong>
            </div>
          </div>

          <h3 className="subheading">Your day-by-day itinerary</h3>

          {selectedTrip.days.map((day) => (
            <article className="day-card" key={day.day}>
              <div className="day-heading">
                <span className="day-number">DAY {day.day}</span>
                <h3>{day.title}</h3>
              </div>

              {day.activities.map((activity, index) => (
                <div
                  className="activity"
                  key={`${day.day}-${index}`}
                >
                  <div className="activity-dot" />

                  <div className="activity-content">
                    <span className="activity-time">
                      {activity.time}
                    </span>
                    <p>{activity.activity}</p>
                  </div>

                  <strong>
                    ₹{activity.estimated_cost.toLocaleString("en-IN")}
                  </strong>
                </div>
              ))}
            </article>
          ))}

          <div className="tips-card">
            <h3>💡 Travel tips</h3>
            <ul>
              {selectedTrip.travel_tips.map((tip, index) => (
                <li key={index}>{tip}</li>
              ))}
            </ul>
          </div>

          <button
            type="button"
            className="print-button"
            onClick={() => window.print()}
          >
            Print / Save as PDF
          </button>

          <button
            type="button"
            className="refresh-button"
            onClick={() => setSelectedTrip(null)}
          >
            Close Saved Itinerary
          </button>

          <p className="disclaimer">
            AI-generated estimates are indicative, not verified live prices.
            Confirm transport, entry fees, and opening hours before traveling.
          </p>
        </section>
      )}

      <footer>
        <p>Trip Genius AI · Your journey, personalized.</p>
      </footer>
    </main>
  );
}

export default App;