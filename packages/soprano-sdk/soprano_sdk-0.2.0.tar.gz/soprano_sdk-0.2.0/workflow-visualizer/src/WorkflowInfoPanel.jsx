import React from 'react';
import {
    Drawer,
    Box,
    Typography,
    IconButton,
    Divider,
    Table,
    TableBody,
    TableRow,
    TableCell,
    Chip,
    Paper
} from '@mui/material';
import { X, Info } from 'lucide-react';

const WorkflowInfoPanel = ({ open, onClose, workflowData }) => {
    if (!workflowData) return null;

    return (
        <Drawer
            anchor="right"
            open={open}
            onClose={onClose}
            PaperProps={{
                sx: {
                    width: { xs: '100%', sm: 400 },
                    backgroundColor: '#1e1e1e',
                    color: '#fff',
                    backgroundImage: 'none'
                }
            }}
        >
            <Box sx={{ p: 2, borderBottom: '1px solid #333', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Box display="flex" alignItems="center" gap={1}>
                    <Info size={20} color="#90caf9" />
                    <Typography variant="h6">Workflow Info</Typography>
                </Box>
                <IconButton onClick={onClose} size="small" sx={{ color: '#fff' }}>
                    <X size={20} />
                </IconButton>
            </Box>

            <Box sx={{ p: 2, overflowY: 'auto', height: '100%' }}>
                {/* Workflow Metadata */}
                <Paper variant="outlined" sx={{ p: 2, mb: 2, backgroundColor: '#2d2d2d', borderColor: '#444' }}>
                    <Typography variant="h6" gutterBottom color="primary.light">Metadata</Typography>

                    <Table size="small">
                        <TableBody>
                            {workflowData.name && (
                                <TableRow>
                                    <TableCell sx={{ color: '#90caf9', fontWeight: 600, borderColor: '#444', width: '40%' }}>Name</TableCell>
                                    <TableCell sx={{ color: '#e0e0e0', borderColor: '#444' }}>{workflowData.name}</TableCell>
                                </TableRow>
                            )}
                            {workflowData.version && (
                                <TableRow>
                                    <TableCell sx={{ color: '#90caf9', fontWeight: 600, borderColor: '#444' }}>Version</TableCell>
                                    <TableCell sx={{ color: '#e0e0e0', borderColor: '#444' }}>{workflowData.version}</TableCell>
                                </TableRow>
                            )}
                            {workflowData.description && (
                                <TableRow>
                                    <TableCell sx={{ color: '#90caf9', fontWeight: 600, borderColor: '#444' }}>Description</TableCell>
                                    <TableCell sx={{ color: '#e0e0e0', borderColor: '#444' }}>{workflowData.description}</TableCell>
                                </TableRow>
                            )}
                        </TableBody>
                    </Table>
                </Paper>

                {/* Data Schema */}
                {workflowData.data && workflowData.data.length > 0 && (
                    <Paper variant="outlined" sx={{ p: 2, mb: 2, backgroundColor: '#2d2d2d', borderColor: '#444' }}>
                        <Typography variant="h6" gutterBottom color="primary.light">Data Schema</Typography>

                        <Box display="flex" flexDirection="column" gap={1.5}>
                            {workflowData.data.map((field, idx) => (
                                <Box key={idx} sx={{ p: 1.5, borderRadius: 1, bgcolor: '#1e1e1e', border: '1px solid #444' }}>
                                    <Box display="flex" justifyContent="space-between" alignItems="center" mb={0.5}>
                                        <Typography variant="body2" fontWeight={600} color="#90caf9">
                                            {field.name}
                                        </Typography>
                                        <Chip
                                            label={field.type}
                                            size="small"
                                            sx={{
                                                height: 20,
                                                fontSize: '0.7rem',
                                                backgroundColor: '#424242',
                                                color: '#fff'
                                            }}
                                        />
                                    </Box>
                                    {field.description && (
                                        <Typography variant="caption" color="#b0bec5">
                                            {field.description}
                                        </Typography>
                                    )}
                                </Box>
                            ))}
                        </Box>
                    </Paper>
                )}

                {/* Tool Configuration */}
                {workflowData.tool_config && workflowData.tool_config.tools && (
                    <Paper variant="outlined" sx={{ p: 2, mb: 2, backgroundColor: '#2d2d2d', borderColor: '#444' }}>
                        <Typography variant="h6" gutterBottom color="primary.light">Tools</Typography>

                        <Box display="flex" flexDirection="column" gap={1.5}>
                            {workflowData.tool_config.tools.map((tool, idx) => (
                                <Box key={idx} sx={{ p: 1.5, borderRadius: 1, bgcolor: '#1e1e1e', border: '1px solid #444' }}>
                                    <Typography variant="body2" fontWeight={600} color="#90caf9" mb={0.5}>
                                        {tool.name}
                                    </Typography>
                                    {tool.description && (
                                        <Typography variant="caption" color="#b0bec5" display="block" mb={0.5}>
                                            {tool.description}
                                        </Typography>
                                    )}
                                    {tool.callable && (
                                        <Typography variant="caption" color="#888" fontFamily="monospace">
                                            {tool.callable}
                                        </Typography>
                                    )}
                                </Box>
                            ))}
                        </Box>
                    </Paper>
                )}

                {/* Statistics */}
                <Paper variant="outlined" sx={{ p: 2, backgroundColor: '#2d2d2d', borderColor: '#444' }}>
                    <Typography variant="h6" gutterBottom color="primary.light">Statistics</Typography>

                    <Box display="grid" gridTemplateColumns="1fr 1fr" gap={2}>
                        <Box>
                            <Typography variant="caption" color="gray">Steps</Typography>
                            <Typography variant="h6" color="#90caf9">
                                {workflowData.steps ? workflowData.steps.length : 0}
                            </Typography>
                        </Box>
                        <Box>
                            <Typography variant="caption" color="gray">Outcomes</Typography>
                            <Typography variant="h6" color="#90caf9">
                                {workflowData.outcomes ? workflowData.outcomes.length : 0}
                            </Typography>
                        </Box>
                        <Box>
                            <Typography variant="caption" color="gray">Data Fields</Typography>
                            <Typography variant="h6" color="#90caf9">
                                {workflowData.data ? workflowData.data.length : 0}
                            </Typography>
                        </Box>
                        <Box>
                            <Typography variant="caption" color="gray">Tools</Typography>
                            <Typography variant="h6" color="#90caf9">
                                {workflowData.tool_config?.tools ? workflowData.tool_config.tools.length : 0}
                            </Typography>
                        </Box>
                    </Box>
                </Paper>
            </Box>
        </Drawer>
    );
};

export default WorkflowInfoPanel;
