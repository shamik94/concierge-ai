import React, { useState, useEffect } from "react";
import axios from "axios";

function App() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const testConnection = async () => {
    try {
      const response = await axios.get("http://localhost:8000/ping");
      console.log("Server connection test:", response.data);
    } catch (err) {
      console.error("Server connection test failed:", err);
    }
  };

  useEffect(() => {
    testConnection();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const response = await axios.post("http://localhost:8000/search", {
        query: query.trim(),
      });
      setResults(response.data.results);
    } catch (err) {
      setError("An error occurred while processing your request. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-extrabold text-gray-900 sm:text-5xl md:text-6xl">
            Location Intelligence
            <span className="text-primary-600"> Assistant</span>
          </h1>
          <p className="mt-3 text-base text-gray-500 sm:mt-5 sm:text-lg">
            Ask questions about locations, restaurants, and other points of interest
          </p>
        </div>

        <form onSubmit={handleSubmit} className="mt-8 space-y-6">
          <div className="rounded-md shadow-sm">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="e.g., Tell me all the vegan restaurants around Berlin Mitte which are open till 11 pm on a tuesday"
              className="appearance-none rounded-lg relative block w-full px-4 py-4 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-primary-500 focus:border-primary-500 focus:z-10 sm:text-sm"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className={`group relative w-full flex justify-center py-3 px-4 border border-transparent text-sm font-medium rounded-md text-white ${
              loading
                ? "bg-primary-400 cursor-not-allowed"
                : "bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
            }`}
          >
            {loading ? (
              <span className="flex items-center">
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  />
                </svg>
                Searching...
              </span>
            ) : (
              "Search"
            )}
          </button>
        </form>

        {error && (
          <div className="mt-8 rounded-md bg-red-50 p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                  />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm text-red-700">{error}</p>
              </div>
            </div>
          </div>
        )}

        {results && (
          <div className="mt-8 bg-white shadow overflow-hidden rounded-lg divide-y divide-gray-200">
            <div className="px-4 py-5 sm:px-6">
              <h2 className="text-lg leading-6 font-medium text-gray-900">Search Results</h2>
            </div>
            {Array.isArray(results) && results.length === 0 ? (
              <div className="px-4 py-5 sm:p-6 text-center text-gray-500">
                No places found matching your criteria.
              </div>
            ) : (
              <div className="divide-y divide-gray-200">
                {results.map((place, index) => (
                  <div key={index} className="px-4 py-5 sm:p-6">
                    <h3 className="text-lg leading-6 font-medium text-gray-900">{place.name}</h3>
                    <div className="mt-4 space-y-3">
                      <p className="text-sm text-gray-500">
                        <span className="font-medium text-gray-700">Address:</span> {place.address}
                      </p>
                      {place.rating && (
                        <p className="text-sm text-gray-500">
                          <span className="font-medium text-gray-700">Rating:</span> {place.rating} ⭐
                          {place.user_ratings_total && ` (${place.user_ratings_total} reviews)`}
                        </p>
                      )}
                      {place.phone && (
                        <p className="text-sm text-gray-500">
                          <span className="font-medium text-gray-700">Phone:</span> {place.phone}
                        </p>
                      )}
                      {place.website && (
                        <p className="text-sm text-gray-500">
                          <span className="font-medium text-gray-700">Website:</span>{" "}
                          <a
                            href={place.website}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-primary-600 hover:text-primary-500"
                          >
                            {place.website}
                          </a>
                        </p>
                      )}
                      {place.opening_hours && place.opening_hours.length > 0 && (
                        <div className="mt-4">
                          <h4 className="text-sm font-medium text-gray-700">Opening Hours:</h4>
                          <ul className="mt-2 space-y-1">
                            {place.opening_hours.map((day, i) => (
                              <li key={i} className="text-sm text-gray-500">
                                {day}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
