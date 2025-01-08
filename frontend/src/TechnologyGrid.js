import React from "react";
import "./TechnologyGrid.css"; // Create a CSS file for specific styles
import categories from "./categories";

const TechnologyGrid = ({ selectedIcons, onToggle }) => {
  return (
    <div className="category-container">
      {categories.map((category) => (
        <div key={category.name} className="category-card">
          <h3 className="category-title">{category.name}</h3>
          <div className="technology-grid">
            {category.technologies.map((tech) => (
              <div
                key={tech.id}
                className={`technology-square ${
                  selectedIcons.includes(tech.name) ? "selected" : ""
                }`}
                onClick={() => onToggle(tech.name)} // Toggle the technology
              >
                <p className="technology-name">{tech.name}</p>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
};

export default TechnologyGrid;
