import React from 'react';

// This helper returns a formatted date string
function formatDate(date: Date): string {
    return date.toLocaleDateString();
}

/** A class-based React component */
export class Welcome extends React.Component<{ name: string }> {
    /** Render the component */
    render() {
        return <h2>Welcome, {this.props.name}</h2>;
    }
}