import React from 'react';

const ResultDisplay = ({ queryType, results }) => {
  const renderResults = () => {
    switch (queryType) {
      case 'place_search_temporal':
        return <TemporalSearchResults results={results} />;
      case 'place_attribute_check':
        return <AttributeCheckResults results={results} />;
      case 'nearby_search':
        return <NearbySearchResults results={results} />;
      case 'unclassified':
        return <GenericResults results={results} />;
      default:
        return <p>Unknown result type</p>;
    }
  };

  return (
    <div className="mt-8 bg-white shadow rounded-lg">
      <div className="px-4 py-5 border-b border-gray-200">
        <h3 className="text-lg leading-6 font-medium text-gray-900">
          {CONFIG.query_types[queryType].name}
        </h3>
      </div>
      <div className="px-4 py-5">
        {renderResults()}
      </div>
    </div>
  );
};

// Individual result type components
const TemporalSearchResults = ({ results }) => {
  // Render temporal search results
};

const AttributeCheckResults = ({ results }) => {
  // Render attribute check results
};

const NearbySearchResults = ({ results }) => {
  // Render nearby search results
};

const GenericResults = ({ results }) => {
  // Render generic results
};

export default ResultDisplay; 