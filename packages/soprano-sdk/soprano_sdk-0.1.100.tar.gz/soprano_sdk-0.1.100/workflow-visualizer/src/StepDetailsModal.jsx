import React from 'react';
import {
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    Button,
    Typography,
    Box,
    Chip,
    Divider,
    Paper,
    useTheme,
    useMediaQuery,
    Table,
    TableBody,
    TableRow,
    TableCell
} from '@mui/material';

const StepDetailsModal = ({ open, onClose, onNavigate, node }) => {
    const theme = useTheme();
    const fullScreen = useMediaQuery(theme.breakpoints.down('md'));

    if (!node) return null;
    const { data } = node;

    return (
        <Dialog
            open={open}
            onClose={() => onClose()}
            maxWidth="md"
            fullWidth
            fullScreen={fullScreen}
            PaperProps={{
                style: {
                    backgroundColor: '#1e1e1e',
                    color: '#fff',
                    backgroundImage: 'none'
                }
            }}
        >
            <DialogTitle sx={{ borderBottom: '1px solid #333' }}>
                <Box display="flex" justifyContent="space-between" alignItems="center" flexWrap="wrap" gap={1}>
                    <Typography variant="h6" component="div">
                        {data.label}
                    </Typography>
                    <Chip
                        label={data.action || data.type || 'Step'}
                        size="small"
                        color="primary"
                        variant="outlined"
                    />
                </Box>
            </DialogTitle>

            <DialogContent sx={{ mt: 2 }}>
                {/* Step Configuration */}
                <Paper variant="outlined" sx={{ p: 2, mb: 3, backgroundColor: '#2d2d2d', borderColor: '#444' }}>
                    <Typography variant="h6" gutterBottom color="primary.light">Step Configuration</Typography>

                    <Table size="small">
                        <TableBody>
                            {data.action && (
                                <TableRow>
                                    <TableCell sx={{ color: '#90caf9', fontWeight: 600, borderColor: '#444', width: '35%' }}>Action</TableCell>
                                    <TableCell sx={{ color: '#e0e0e0', borderColor: '#444' }}>{data.action}</TableCell>
                                </TableRow>
                            )}
                            {data.field && (
                                <TableRow>
                                    <TableCell sx={{ color: '#90caf9', fontWeight: 600, borderColor: '#444' }}>Field</TableCell>
                                    <TableCell sx={{ color: '#e0e0e0', borderColor: '#444' }}>{data.field}</TableCell>
                                </TableRow>
                            )}
                            {data.function && (
                                <TableRow>
                                    <TableCell sx={{ color: '#90caf9', fontWeight: 600, borderColor: '#444' }}>Function</TableCell>
                                    <TableCell sx={{ color: '#e0e0e0', borderColor: '#444' }}>{data.function}</TableCell>
                                </TableRow>
                            )}
                            {data.output && (
                                <TableRow>
                                    <TableCell sx={{ color: '#90caf9', fontWeight: 600, borderColor: '#444' }}>Output</TableCell>
                                    <TableCell sx={{ color: '#e0e0e0', borderColor: '#444' }}>{data.output}</TableCell>
                                </TableRow>
                            )}
                            {(data.max_attempts || data.retry_limit) && (
                                <TableRow>
                                    <TableCell sx={{ color: '#90caf9', fontWeight: 600, borderColor: '#444' }}>Max Attempts</TableCell>
                                    <TableCell sx={{ color: '#e0e0e0', borderColor: '#444' }}>{data.max_attempts || data.retry_limit}</TableCell>
                                </TableRow>
                            )}
                            {data.validator && (
                                <TableRow>
                                    <TableCell sx={{ color: '#90caf9', fontWeight: 600, borderColor: '#444' }}>Validator</TableCell>
                                    <TableCell sx={{ color: '#e0e0e0', borderColor: '#444' }}>{data.validator}</TableCell>
                                </TableRow>
                            )}
                            {data.depends_on && (
                                <TableRow>
                                    <TableCell sx={{ color: '#90caf9', fontWeight: 600, borderColor: '#444' }}>Depends On</TableCell>
                                    <TableCell sx={{ color: '#e0e0e0', borderColor: '#444' }}>
                                        <Chip
                                            label={data.depends_on}
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                if (onNavigate) {
                                                    onNavigate(data.depends_on);
                                                }
                                            }}
                                            size="small"
                                            sx={{
                                                cursor: 'pointer',
                                                backgroundColor: '#1565c0',
                                                color: '#fff',
                                                '&:hover': {
                                                    backgroundColor: '#1976d2'
                                                }
                                            }}
                                        />
                                    </TableCell>
                                </TableRow>
                            )}
                        </TableBody>
                    </Table>
                </Paper>

                {data.description && (
                    <Box mb={3}>
                        <Typography variant="subtitle2" color="gray" gutterBottom>Description</Typography>
                        <Typography variant="body1">{data.description}</Typography>
                    </Box>
                )}

                {data.agent && (
                    <Paper variant="outlined" sx={{ p: 2, mb: 3, backgroundColor: '#2d2d2d', borderColor: '#444' }}>
                        <Typography variant="h6" gutterBottom color="primary.light">Agent Configuration</Typography>

                        <Box display="grid" gridTemplateColumns={fullScreen ? "1fr" : "1fr 1fr"} gap={2} mb={2}>
                            <Box>
                                <Typography variant="caption" color="gray">Name</Typography>
                                <Typography variant="body2">{data.agent.name}</Typography>
                            </Box>
                            <Box>
                                <Typography variant="caption" color="gray">Model</Typography>
                                <Typography variant="body2">{data.agent.model}</Typography>
                            </Box>
                        </Box>

                        {data.agent.description && (
                            <Box mb={2}>
                                <Typography variant="caption" color="gray">Description</Typography>
                                <Typography variant="body2">{data.agent.description}</Typography>
                            </Box>
                        )}

                        {data.agent.initial_message && (
                            <Box mb={2}>
                                <Typography variant="caption" color="gray">Initial Message</Typography>
                                <Typography variant="body2" sx={{ fontStyle: 'italic' }}>"{data.agent.initial_message}"</Typography>
                            </Box>
                        )}

                        {data.agent.instructions && (
                            <Box>
                                <Typography variant="caption" color="gray">Instructions</Typography>
                                <Box
                                    component="pre"
                                    sx={{
                                        p: 1.5,
                                        borderRadius: 1,
                                        bgcolor: '#111',
                                        overflowX: 'auto',
                                        fontSize: '0.85rem',
                                        fontFamily: 'monospace',
                                        color: '#d4d4d4',
                                        border: '1px solid #333',
                                        whiteSpace: 'pre-wrap',
                                        wordBreak: 'break-word'
                                    }}
                                >
                                    {data.agent.instructions}
                                </Box>
                            </Box>
                        )}

                        {data.agent.tools && (
                            <Box mt={2}>
                                <Typography variant="caption" color="gray" gutterBottom>Tools</Typography>
                                <Box display="flex" flexWrap="wrap" gap={1} mt={1}>
                                    {data.agent.tools.map((tool, idx) => (
                                        <Chip
                                            key={idx}
                                            label={tool}
                                            size="small"
                                            variant="outlined"
                                            sx={{ borderColor: '#555', color: '#ccc' }}
                                        />
                                    ))}
                                </Box>
                            </Box>
                        )}
                    </Paper>
                )}

                {data.transitions && (
                    <Box mb={3}>
                        <Typography variant="subtitle2" color="gray" gutterBottom>Transitions</Typography>
                        <Box display="flex" flexDirection="column" gap={1}>
                            {data.transitions.map((t, idx) => {
                                let label = '';
                                if (t.pattern) {
                                    label = `${t.pattern} → ${t.next}`;
                                } else if (t.condition !== undefined) {
                                    label = `condition: ${t.condition} → ${t.next}`;
                                }
                                return (
                                    <Chip
                                        key={idx}
                                        label={label}
                                        variant="outlined"
                                        sx={{ borderColor: '#555', color: '#ccc', justifyContent: 'flex-start' }}
                                    />
                                );
                            })}
                        </Box>
                    </Box>
                )}

                {data.next && !data.transitions && (
                    <Box mb={3}>
                        <Typography variant="subtitle2" color="gray" gutterBottom>Next Step</Typography>
                        <Chip
                            label={data.next}
                            variant="outlined"
                            sx={{ borderColor: '#555', color: '#ccc' }}
                        />
                    </Box>
                )}

                <Box mt={4}>
                    <Typography variant="caption" color="gray" sx={{ display: 'block', mb: 1 }}>Raw Data</Typography>
                    <Box
                        component="pre"
                        sx={{
                            p: 1,
                            bgcolor: '#111',
                            borderRadius: 1,
                            fontSize: '0.75rem',
                            overflowX: 'auto',
                            color: '#888'
                        }}
                    >
                        {JSON.stringify(data, null, 2)}
                    </Box>
                </Box>
            </DialogContent>

            <DialogActions sx={{ borderTop: '1px solid #333', p: 2 }}>
                <Button onClick={onClose} color="inherit">Close</Button>
            </DialogActions>
        </Dialog>
    );
};

export default StepDetailsModal;
