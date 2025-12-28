# synapse\_ai\_tools

`synapse_ai_tools` is a Python package developed by **SYNAPSE AI SAS**. It provides utilities for phonetic processing, Mel spectrogram generation, exploratory data analysis (EDA), and interactive deep learning model configuration — especially useful in voice-related AI applications like TTS and voice cloning.

## Installation

```bash
pip install synapse_ai_tools
```

**Requires:** Python > 3.6 and < 3.11

**Important:** To avoid conflicts with other packages, it is strongly recommended to use a virtual environment:

```bash
python -m venv myenv
# On Windows:
myenv\Scripts\activate
# On Unix or macOS:
source myenv/bin/activate
pip install synapse_ai_tools
```

---

## Modules Overview

### `phonemes`

Rule-based transformations optimized for Rioplatense Spanish:

* `phoneme(text, punctuation=False)`: Converts Spanish text into a simplified phoneme sequence using context-sensitive linguistic rules.
* `accent(text, punctuation=False)`: Applies accentuation to each word based on syllabic stress rules.
* `dictionaries(text, order_by_frequency=True, pad=True)`: Returns a phoneme-to-index dictionary and a phoneme frequency dictionary.
* `phoneme_graphs(text, sort=True)`: Displays a bar chart of phoneme frequency distribution.
* `embeddings(input_dim, output_dim, std, pad=True, seed=23)`: Returns an embedding matrix with variance scaled by token index. Useful for models where lower indices represent more frequent tokens.

### `mel_spectrograms`

* `load_audio_to_mel(file_path, sr=22050, ...)`: Converts an audio file into a Mel spectrogram (in dB scale) using Librosa, with customizable STFT and Mel filter parameters.
* `graph_mel_spectrogram(spectrogram, output_dir='', name='Spectrogram', ...)`: Visualizes and optionally saves the spectrogram image with customizable size, colormap, and layout.

### `eda`

Utilities for inspecting structured data and feature distributions:

* `nulls(df, column)`: Prints count and percentage of null values in a given column.
* `outliers(df, column, ...)`: Analyzes and visualizes outliers via histograms, boxplots, and summary statistics.
* `heatmap_correlation(df, columns, correlation_type='spearman', ...)`: Displays a correlation heatmap for selected columns.
* `pca_view(df, dimensions=2 or 3, target=None, ...)`: Performs PCA and optionally visualizes it in 2D or 3D, with or without a target variable.

### `ModelConfigurator`

An interactive Tkinter-based GUI to build deep learning models with the Keras Sequential API:

* Choose problem type: classification or regression
* Define input shape
* Add layers: Dense, Conv1D/2D, Pooling, Dropout, BatchNormalization, LSTM, Bidirectional, Flatten
* Select optimizers, loss functions, metrics
* Export trained model and architecture diagram

**Usage:**

```python
from synapse_ai.DNN.model_configurator import ModelConfigurator
ModelConfigurator()
```

Note: This tool uses tkinter for GUI rendering and requires a graphical environment.
If you're working on a headless system (e.g., some cloud servers or Docker containers), the GUI won't launch unless properly configured (e.g., using X11 forwarding or a virtual display).

---

## Use Cases

* Prepare phonetic inputs for voice synthesis or TTS training
* Visualize and debug Mel spectrograms
* Perform quick EDA and dimensionality reduction
* Build deep learning architectures without writing code

---

## Developed by

**SYNAPSE AI SAS**
Advanced solutions in artificial intelligence, speech processing, and applied data science.
