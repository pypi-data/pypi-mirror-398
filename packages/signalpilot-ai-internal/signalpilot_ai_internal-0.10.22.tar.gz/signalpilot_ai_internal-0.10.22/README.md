# **SignalPilot Agent — The AI-Powered Assistant for Jupyter Notebooks**

![Logo](https://i.imgur.com/JdA8ilQ.png)

---

## **What is SignalPilot Agent?**

**SignalPilot is an AI-native notebook assistant that supercharges your existing Jupyter workflows.**

Built by leading AI and quant researchers from YC, Harvard, MIT, and Goldman Sachs, SignalPilot brings real-time, context-aware assistance directly into JupyterLab.

Use natural language to clean data, write analysis code, debug errors, explore dataframes, and build models—faster and with fewer mistakes.

**No hallucinated code. No context switching. Just faster insights.**

---

## **Why Use SignalPilot Agent in Jupyter?**

Whether you’re a quant, data scientist, or analyst living in notebooks, SignalPilot helps you:

✅ Clean and transform messy data in seconds

✅ Visualize trends, rollups, and anomalies from a prompt

✅ Connect your custom databases in one click and easily explore from notebooks 

✅ Generate *runnable* Python or SQL that fits your current cell + variable context

✅ Auto-detect schema changes and debug downstream errors

✅ Stay private: run entirely *local-first* or in your own secure VPC

✅ Extend JupyterLab without changing how you work

---

## **Perfect For:**

- Data scientists cleaning huge CSVs
- Quant researchers testing ML pipelines
- Product and analytics teams tired of building dashboards and flaky notebooks
- Anyone tired of LLM tools that break their code

---

## **Installation**

### **📦 Requirements**

- JupyterLab >= 4.0.0
- NodeJS (for development)

### **🧠 Install SignalPilot Agent:**

```
pip install jupyterlab signalpilot_ai_internal
```

### **❌ Uninstall:**

```
pip uninstall signalpilot_ai_internal
```

---

## **How to Get Started**

To unlock full functionality, you’ll need SignalPilot API credentials.

👉 [**Request your API key**](https://signalpilot.ai/#contact) or email us at [fahim@signalpilot.ai](mailto:fahim@signalpilot.ai)

---

## **Why SignalPilot**

- ✅ Context-aware code gen: understands variables, dataframes, imports, and prior cells
- ✅ AI that *fixes* schema issues and silent join bugs
- ✅ Inline review + diffs before you run any code
- ✅ Visualizations via natural language (matplotlib, plotly, seaborn supported)
- ✅ BYO LLM: Anthropic, OpenAI, vLLM, Ollama, or HF endpoints
- ✅ Built to run in air-gapped / enterprise environments

---

## **Local Development Instructions**

To contribute or develop locally:

```
# Clone the repo and enter the directory
git clone https://github.com/sagebook/signalpilot_ai_internal.git
cd signalpilot_ai_internal

# Install in editable mode
pip install -e "."

# Link extension to JupyterLab
jupyter labextension develop . --overwrite

# Rebuild on changes
jlpm build
```

For auto-rebuild while editing:

```
# Watch source
jlpm watch

# Run JupyterLab in parallel
jupyter lab
```

---

## **Uninstall in Dev Mode**

```
pip uninstall signalpilot_ai_internal
# Then manually remove labextension symlink from JupyterLab extensions dir.
```

---

## **Want to See SignalPilot in Action?**

🎥 Try the demo notebook or explore at [https://signalpilot.ai](https://signalpilot.ai/)

---

**Built for teams working with sensitive data:**

- Zero data retention by default
- Optional BYO keys for Claude, OpenAI, or local models
- Notebook-specific controls for what the model can “see”
- Fine-grained telemetry settings

---

## **Contact**

Questions? Ideas?

Email: [fahim@signalpilot.ai](mailto:fahim@signalpilot.ai)

Website: [https://signalpilot.ai](https://signalpilot.ai/)

---

AI Jupyter Notebook, JupyterLab Extension, Jupyter Assistant, Data Science Assistant, Jupyter LLM, AI code generation, dataframe cleaning, Jupyter AI, SignalPilot, SignalPilot Agent, AI for dataframes, Jupyter SQL assistant, notebook extension
