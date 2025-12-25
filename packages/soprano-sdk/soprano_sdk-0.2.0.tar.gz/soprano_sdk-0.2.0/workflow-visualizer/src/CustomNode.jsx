import React, { memo } from 'react';
import { Handle, Position } from 'reactflow';

const CustomNode = memo(({ data }) => {
    let borderColor = '#333';
    let backgroundColor = '#1e1e1e';
    let headerColor = '#2d2d2d';
    let textColor = '#e0e0e0';
    let labelColor = '#fff';

    if (data.isOutcome) {
        if (data.type === 'success') {
            borderColor = '#2e7d32'; // Dark Green
            backgroundColor = '#1b3320';
            headerColor = '#2e7d32';
        } else if (data.type === 'failure') {
            borderColor = '#c62828'; // Dark Red
            backgroundColor = '#3e1b1b';
            headerColor = '#c62828';
        } else {
            borderColor = '#ef6c00'; // Dark Orange
            backgroundColor = '#332010';
            headerColor = '#ef6c00';
        }
    } else {
        // Steps - different colors based on action type
        if (data.action === 'call_function') {
            borderColor = '#7b1fa2'; // Purple for function calls
            backgroundColor = '#1e1e1e';
            headerColor = '#7b1fa2';
        } else {
            borderColor = '#1565c0'; // Blue for other actions
            backgroundColor = '#1e1e1e';
            headerColor = '#1565c0';
        }
    }

    return (
        <div style={{
            padding: '0',
            borderRadius: '8px',
            background: backgroundColor,
            border: `1px solid ${borderColor}`,
            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.5), 0 2px 4px -1px rgba(0, 0, 0, 0.3)',
            minWidth: '220px',
            maxWidth: '280px',
            fontFamily: '"Inter", sans-serif',
            overflow: 'hidden',
            color: textColor
        }}>
            <Handle type="target" position={Position.Top} style={{ background: '#888' }} />

            <div style={{
                padding: '8px 12px',
                background: headerColor,
                fontWeight: '600',
                fontSize: '14px',
                color: '#fff',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between'
            }}>
                <span>{data.label}</span>
            </div>

            <div style={{ padding: '12px', fontSize: '11px', color: '#b0bec5', lineHeight: '1.5' }}>
                {data.action && (
                    <div style={{ marginBottom: '4px' }}>
                        <span style={{ fontWeight: 600, color: '#90caf9' }}>Action:</span> {data.action}
                    </div>
                )}
                {data.field && (
                    <div style={{ marginBottom: '4px' }}>
                        <span style={{ fontWeight: 600, color: '#90caf9' }}>Field:</span> {data.field}
                    </div>
                )}
                {data.function && (
                    <div style={{ marginBottom: '4px' }}>
                        <span style={{ fontWeight: 600, color: '#90caf9' }}>Function:</span> {data.function}
                    </div>
                )}
                {data.output && (
                    <div style={{ marginBottom: '4px' }}>
                        <span style={{ fontWeight: 600, color: '#90caf9' }}>Output:</span> {data.output}
                    </div>
                )}
                {data.agent && (
                    <div style={{ marginBottom: '4px' }}>
                        <span style={{ fontWeight: 600, color: '#90caf9' }}>Agent:</span> {data.agent.name}
                    </div>
                )}
                {(data.max_attempts || data.retry_limit) && (
                    <div style={{ marginBottom: '4px' }}>
                        <span style={{ fontWeight: 600, color: '#90caf9' }}>Max Attempts:</span> {data.max_attempts || data.retry_limit}
                    </div>
                )}
                {data.validator && (
                    <div style={{ marginBottom: '4px' }}>
                        <span style={{ fontWeight: 600, color: '#90caf9' }}>Validator:</span> {data.validator}
                    </div>
                )}
                {data.depends_on && (
                    <div style={{ marginBottom: '4px' }}>
                        <span style={{ fontWeight: 600, color: '#90caf9' }}>Depends On:</span> {data.depends_on}
                    </div>
                )}
                {data.type && (
                    <div style={{ marginBottom: '4px' }}>
                        <span style={{ fontWeight: 600, color: '#90caf9' }}>Type:</span> {data.type}
                    </div>
                )}
                {data.message && (
                    <div style={{ marginTop: '8px', padding: '6px', background: '#2d2d2d', borderRadius: '4px', fontStyle: 'italic', color: '#cfd8dc', fontSize: '10px' }}>
                        {data.message.length > 60 ? data.message.substring(0, 60) + '...' : data.message}
                    </div>
                )}
            </div>

            <Handle type="source" position={Position.Bottom} style={{ background: '#888' }} />
        </div>
    );
});

export default CustomNode;
