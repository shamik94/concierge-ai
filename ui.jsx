import React, { useState } from "react";
import axios from "axios";
import "./App.css";

function App() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!query.trim()) return;

    setLoading(true);
    setError(null);

    try {
      // Call your backend API that integrates Google Maps with LLM
      const response = await axios.post("/api/search", { query });
      setResults(response.data.results);
    } catch (err) {
      setError(
        "An error occurred while processing your request. Please try again."
      );
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container">
      <header>
        <h1>Location Intelligence Assistant</h1>
        <p>
          Ask questions about locations, restaurants, and other points of
          interest
        </p>
      </header>

      <main>
        <form onSubmit={handleSubmit} className="search-form">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="e.g., Tell me all the vegan restaurants around Berlin Mitte which are open till 11 pm on a tuesday"
            className="search-input"
          />
          <button type="submit" className="search-button" disabled={loading}>
            {loading ? "Searching..." : "Search"}
          </button>
        </form>

        {loading && (
          <div className="loading">
            Searching for places that match your criteria...
          </div>
        )}

        {error && <div className="error">{error}</div>}

        {results && (
          <div className="results-container">
            <h2>Search Results</h2>
            {results.length === 0 ? (
              <p>No places found matching your criteria.</p>
            ) : (
              <ul className="results-list">
                {results.map((place, index) => (
                  <li key={place.place_id} className="result-item">
                    <h3>{place.name}</h3>
                    <div className="place-details">
                      <p>
                        <strong>Address:</strong> {place.formatted_address}
                      </p>
                      {place.rating && (
                        <p>
                          <strong>Rating:</strong> {place.rating} ⭐ (
                          {place.user_ratings_total} reviews)
                        </p>
                      )}
                      {place.formatted_phone_number && (
                        <p>
                          <strong>Phone:</strong> {place.formatted_phone_number}
                        </p>
                      )}
                      {place.website && (
                        <p>
                          <strong>Website:</strong>{" "}
                          <a
                            href={place.website}
                            target="_blank"
                            rel="noopener noreferrer"
                          >
                            {place.website}
                          </a>
                        </p>
                      )}
                      {place.opening_hours && (
                        <div className="opening-hours">
                          <p>
                            <strong>Opening Hours:</strong>
                          </p>
                          <ul>
                            {place.opening_hours.weekday_text.map((day, i) => (
                              <li key={i}>{day}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
