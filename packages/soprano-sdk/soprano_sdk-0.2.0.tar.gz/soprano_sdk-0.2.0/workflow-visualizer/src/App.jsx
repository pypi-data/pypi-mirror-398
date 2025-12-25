import React, { useState, useEffect } from 'react';
import yaml from 'js-yaml';
import WorkflowGraph from './WorkflowGraph';
import StepDetailsModal from './StepDetailsModal';
import WorkflowInfoPanel from './WorkflowInfoPanel';
import { Upload } from 'lucide-react';
import { ThemeProvider, createTheme, CssBaseline, Box, AppBar, Toolbar, Typography, Button } from '@mui/material';

const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#90caf9',
    },
    background: {
      default: '#121212',
      paper: '#1e1e1e',
    },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
  },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          scrollbarColor: "#6b6b6b #2b2b2b",
          "&::-webkit-scrollbar, & *::-webkit-scrollbar": {
            backgroundColor: "#2b2b2b",
          },
          "&::-webkit-scrollbar-thumb, & *::-webkit-scrollbar-thumb": {
            borderRadius: 8,
            backgroundColor: "#6b6b6b",
            minHeight: 24,
            border: "3px solid #2b2b2b",
          },
          "&::-webkit-scrollbar-thumb:focus, & *::-webkit-scrollbar-thumb:focus": {
            backgroundColor: "#959595",
          },
          "&::-webkit-scrollbar-thumb:active, & *::-webkit-scrollbar-thumb:active": {
            backgroundColor: "#959595",
          },
          "&::-webkit-scrollbar-thumb:hover, & *::-webkit-scrollbar-thumb:hover": {
            backgroundColor: "#959595",
          },
          "&::-webkit-scrollbar-corner, & *::-webkit-scrollbar-corner": {
            backgroundColor: "#2b2b2b",
          },
        },
      },
    },
  },
});

function App() {
  const [workflowData, setWorkflowData] = useState(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [error, setError] = useState(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [infoPanelOpen, setInfoPanelOpen] = useState(false);
  const [isDragging, setIsDragging] = useState(false);

  const loadWorkflowFile = (file) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const data = yaml.load(e.target.result);
        setWorkflowData(data);
        setError(null);
      } catch (err) {
        setError("Invalid YAML file");
        console.error(err);
      }
    };
    reader.readAsText(file);
  };

  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
      loadWorkflowFile(file);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file && (file.name.endsWith('.yaml') || file.name.endsWith('.yml'))) {
      loadWorkflowFile(file);
    } else {
      setError('Please drop a valid YAML file (.yaml or .yml)');
    }
  };

  const onNodeClick = (event, node) => {
    // Only open modal for steps (not outcomes), or if user wants to see outcomes too?
    // User request: "like when I click on a step node(not the outcome node) a pop up appears"
    if (!node.data.isOutcome) {
      setSelectedNode(node);
      setModalOpen(true);
    }
  };

  const handleCloseModal = () => {
    setModalOpen(false);
    setSelectedNode(null);
  };

  const handleNavigate = (stepId) => {
    if (stepId && workflowData?.steps) {
      const dependentStep = workflowData.steps.find(step => step.id === stepId);
      if (dependentStep) {
        const dependentNode = {
          id: dependentStep.id,
          data: { label: dependentStep.id, ...dependentStep, isOutcome: false }
        };
        setSelectedNode(dependentNode);
      }
    }
  };

  return (
    <ThemeProvider theme={darkTheme}>
      <CssBaseline />
      <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh', width: '100vw', overflow: 'hidden' }}>
        <AppBar position="static" color="default" elevation={1} sx={{ bgcolor: '#1e1e1e', borderBottom: '1px solid #333' }}>
          <Toolbar variant="dense" sx={{ flexWrap: 'wrap', py: 1 }}>
            <Typography variant="h6" component="div" sx={{ flexGrow: 1, fontWeight: 600, fontSize: { xs: '1rem', sm: '1.25rem' } }}>
              Workflow Visualizer
            </Typography>

            {error && <Typography color="error" sx={{ mr: 2, fontSize: '0.875rem' }}>{error}</Typography>}
          </Toolbar>
        </AppBar>

        <Box sx={{ flex: 1, position: 'relative', bgcolor: '#121212', overflow: 'hidden', display: 'flex', minHeight: 0 }}>
          {workflowData ? (
            <WorkflowGraph workflowData={workflowData} onNodeClick={onNodeClick} onInfoClick={() => setInfoPanelOpen(true)} />
          ) : (
            <Box
              display="flex"
              justifyContent="center"
              alignItems="center"
              height="100%"
              width="100%"
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              sx={{
                border: isDragging ? '3px dashed #90caf9' : '3px dashed #444',
                borderRadius: 2,
                m: 4,
                maxWidth: '40%',
                maxHeight: '30%',
                mx: 'auto',
                my: 'auto',
                transition: 'all 0.3s ease',
                backgroundColor: isDragging ? 'rgba(144, 202, 249, 0.1)' : 'transparent'
              }}
            >
              <Box textAlign="center" p={4}>
                <Upload size={64} color="#90caf9" style={{ marginBottom: 16 }} />
                <Typography variant="h5" gutterBottom color="#fff">
                  Drop your workflow YAML file here
                </Typography>
                <Typography variant="body2" color="text.secondary" mb={3}>
                  or click the button below to browse
                </Typography>
                <Button
                  component="label"
                  variant="contained"
                  size="large"
                  startIcon={<Upload size={20} />}
                  sx={{ textTransform: 'none' }}
                >
                  Choose Workflow File
                  <input type="file" accept=".yaml,.yml" hidden onChange={handleFileUpload} />
                </Button>
                {error && (
                  <Typography color="error" mt={2}>
                    {error}
                  </Typography>
                )}
              </Box>
            </Box>
          )}
        </Box>

        <StepDetailsModal
          open={modalOpen}
          onClose={handleCloseModal}
          onNavigate={handleNavigate}
          node={selectedNode}
        />

        <WorkflowInfoPanel
          open={infoPanelOpen}
          onClose={() => setInfoPanelOpen(false)}
          workflowData={workflowData}
        />
      </Box>
    </ThemeProvider>
  );
}

export default App;
