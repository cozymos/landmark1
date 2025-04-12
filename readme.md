### Step-by-Step for Running the Streamlit App

1. **Setup Virtual Environment**
2. **Install Dependencies**
3. **Configure Environment Variables**
4. **Run the App**

### 1. Create and Activate Virtual Environment

```bash
python -m venv venv
.\venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install streamlit folium streamlit-folium
```

### 3. Create Environment Variables

```bash
export GOOGLE_MAPS_API_KEY=your_api_key_here
```

### 4. Run the Streamlit App

```bash
streamlit run main.py
```

### 5. Project Structure
```
LandmarkLocator/
├── pyproject.toml      # Project metadata and dependencies
├── uv.lock            # Locked dependencies with exact versions
├── main.py           # Main application file
└── .venv/            # Virtual environment
```

### Expected Result:
- App will launch in default browser
- Default URL: http://localhost:8501
- Streamlit interface will show:
  - Map interface
  - Sidebar controls
  - Landmark recommendations

### Debugging Steps if Needed:
1. Check console for errors
2. Verify API key is loaded
3. Confirm all dependencies installed
4. Check network connectivity
