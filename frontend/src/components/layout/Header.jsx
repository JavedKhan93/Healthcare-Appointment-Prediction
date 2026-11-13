import React from 'react';

export default function Header({ category, title, description, rightContent, badge }) {
  return (
    <header className="page-header">
      <div>
        {category && (
          <div className="page-header-meta">
            <span>{category}</span>
          </div>
        )}
        <h1>
          {title}
          {badge && <span className="synthetic-pill">{badge}</span>}
        </h1>
        {description && <p className="page-header-desc">{description}</p>}
      </div>
      {rightContent && <div>{rightContent}</div>}
    </header>
  );
}

