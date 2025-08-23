# Setup

```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

# Run Data App

To run the Dash application, run the following command:

```bash
cd ../../
python examples/data_app/app.py
```

This will start a Dash server on port 8050.

## View the Dashboard

Open your browser and navigate to:
```
http://localhost:8050
```

## Features

The AI Agent Performance Dashboard includes:

- **Model Response Times**: Box plot showing response time distributions across different LLM models
- **Model Accuracy Trends**: Time series showing accuracy performance over time
- **Token Usage by Task Type**: Stacked bar chart showing input/output token consumption
- **Agent Conversation Analysis**: Scatter plot correlating conversation turns with success rates
- **Performance Heatmap**: Multi-dimensional view of model performance metrics
- **Real-time Metrics**: Live updating cards showing key performance indicators

The dashboard uses synthetic data simulating:
- 5 different LLM models (GPT-4, Claude-3, Gemini-Pro, LLaMA-2, GPT-3.5)
- 5 task types (Code Generation, Text Analysis, Translation, Summarization, Q&A)
- 30 days of historical performance data
- 100 conversation interactions with varying complexity

All visualizations update every 5 seconds to simulate real-time monitoring capabilities.