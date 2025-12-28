import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import (
    InputLayer, Dense, Conv1D, Conv2D, MaxPooling1D, MaxPooling2D,
    AveragePooling1D, AveragePooling2D, Dropout, BatchNormalization,
    LSTM, Bidirectional, Flatten
)
from tensorflow.keras.optimizers import Adam, Nadam, SGD
from tensorflow.keras.regularizers import l1, l2, l1_l2
from tensorflow.keras.utils import plot_model
from pathlib import Path
import os
import sys
from PIL import Image, ImageTk


BASE_DIR = Path(__file__).parent



class ModelConfigurator:
    """
    A GUI-based model configuration tool for building and compiling deep learning models using Keras.

    This class provides a step-by-step wizard that allows users to define the input shape, add various types of layers
    (e.g., Dense, Conv1D, Conv2D, MaxPooling, etc.), configure optimizers, loss functions, and evaluation metrics,
    and optionally save the configured model along with its architecture diagram and summary. The user interface is built
    with Tkinter, while the model construction leverages Keras' Sequential API.

    **Recommended Environment Setup**:
    Due to compatibility requirements, it is strongly recommended to use a virtual environment with the following setup:
    
    - Python version: **≤ 3.10**
    - TensorFlow version: **2.10**
    - NumPy version: **< 2.0**
    
    Example of creating and activating a virtual environment:
    
    ```bash
    python -m venv myenv
    # On Windows:
    myenv\Scripts\activate
    # On Unix or macOS:
    source myenv/bin/activate
    ```

    After activating the environment, install the necessary dependencies:
    
    ```bash
    pip install tensorflow==2.10 numpy<2.0
    ```

    **Example Usage**:
    
    ```python
    from synapse_ai.DNN import ModelConfigurator
    
    # Launch the GUI-based model configurator
    ModelConfigurator()
    ```
    """

    def __init__(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        src_dir = os.path.join(base_dir, 'src')
        self.root = tk.Tk()
        self.root.title('Synapse.AI - Model Configuration')
        self.root.iconbitmap(os.path.join(BASE_DIR, 'src/Logo.ico'))
        self.root.geometry('1300x700')
        self.root.minsize(900, 600)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)
        self.root.rowconfigure(0, weight=0)

        self.layers_config = []
        self.input_shape = None
        self.save_directory = tk.StringVar(value='')
        self.problem_type = tk.StringVar(value='classification')
        self.loss_function = tk.StringVar(value='')
        self.metrics_vars = []
        self.current_step = 0
        self.status_var = tk.StringVar(value='')
        self.optimizer_var = tk.StringVar(value='Select optimizer')
        self.learning_rate_var = tk.DoubleVar(value=0.001)
        self.save_var = tk.BooleanVar(value=False)

        self.font_config = ('Helvetica', 13)
        self.pad_config = 8

        self.style = ttk.Style()
        self.style.configure('Orange.TButton', foreground='orange')

        self.header_frame = ttk.Frame(self.root, name='header_frame')
        self.header_frame.grid(row=0, column=0, sticky='ew', padx=10, pady=5)
        self.header_frame.columnconfigure(0, weight=1)
        self.header_frame.columnconfigure(1, weight=0)
        self.header_frame.columnconfigure(2, weight=1)

        self.logo_empresa = self.load_image(os.path.join(BASE_DIR, 'src/Logo.png'), 250, 250)
        self.logo_tensorflow = self.load_image(os.path.join(BASE_DIR, 'src/tf.png'), 140, 100)
        self.root.logo_empresa = self.logo_empresa
        self.root.logo_tensorflow = self.logo_tensorflow

        self.logo_label_empresa = tk.Label(self.header_frame, image=self.logo_empresa)
        self.logo_label_empresa.grid(row=0, column=0, padx=(0, 15), sticky='e')

        tk.Label(
            self.header_frame,
            text='Powered by',
            font=('Helvetica', 11, 'italic'),
            fg='#666666'
        ).grid(row=0, column=1, padx=10, pady=10)

        self.logo_label_tensorflow = tk.Label(self.header_frame, image=self.logo_tensorflow)
        self.logo_label_tensorflow.grid(row=0, column=2, padx=(15, 0), sticky='w')

        self.steps = [self.step_0, self.step_1, self.step_2, self.step_3, self.step_4]
        self.show_step(0)
        self.root.mainloop()


    def load_image(self, path, width, height):
        img = Image.open(path)
        img = img.resize((width, height), Image.LANCZOS)
        return ImageTk.PhotoImage(img)

    def show_info(self, message):
        messagebox.showinfo('Parameter Info', message)

    def clear_window(self):
        for widget in self.root.winfo_children():
            if widget not in [self.header_frame, self.root]:
                if isinstance(widget, ttk.Frame) and widget.winfo_name() not in ['header_frame']:
                    widget.destroy()
        self.root.update()

    def show_step(self, step):
        self.current_step = step
        self.clear_window()
        self.steps[step]()

    def step_0(self):
        content_frame = ttk.Frame(self.root, name='step0_frame')
        content_frame.grid(row=1, column=0, sticky='nsew', padx=50, pady=50)
        tk.Label(content_frame, text='Select Problem Type', font=self.font_config).pack(pady=self.pad_config * 2)
        tk.Radiobutton(content_frame, text='Classification', variable=self.problem_type,
                       value='classification', font=self.font_config).pack(pady=self.pad_config)
        tk.Radiobutton(content_frame, text='Regression', variable=self.problem_type,
                       value='regression', font=self.font_config).pack(pady=self.pad_config)
        ttk.Button(
            content_frame,
            name='step0_next_btn',
            text='Next',
            command=lambda: self.show_step(1)
        ).pack(pady=20)

    def step_1(self):
        main_frame = ttk.Frame(self.root, name='step1_main_frame')
        main_frame.grid(row=1, column=0, sticky='nsew', padx=20, pady=20)

        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient='vertical', command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), 'units')

        def _bind_mousewheel(event):
            canvas.bind_all('<MouseWheel>', _on_mousewheel)

        def _unbind_mousewheel(event):
            canvas.unbind_all('<MouseWheel>')

        scrollable_frame.bind('<Enter>', _bind_mousewheel)
        scrollable_frame.bind('<Leave>', _unbind_mousewheel)

        canvas.bind_all('<Button-4>', lambda e: canvas.yview_scroll(-1, 'units'))
        canvas.bind_all('<Button-5>', lambda e: canvas.yview_scroll(1, 'units'))

        scrollable_frame.bind(
            '<Configure>',
            lambda e: canvas.configure(
                scrollregion=canvas.bbox('all'),
                width=e.width
            )
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.grid(row=0, column=0, sticky='nsew')
        scrollbar.grid(row=0, column=1, sticky='ns')

        container = ttk.Frame(scrollable_frame)
        container.pack(expand=False, fill='x', padx=220)
        main_frame.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)

        tk.Label(container, text='Define Input Shape and Add Layers',
                 font=self.font_config).pack(pady=self.pad_config * 2)

        input_frame = ttk.Frame(container)
        input_frame.pack(pady=self.pad_config, anchor='center')

        tk.Label(input_frame, text='Input Shape:', font=self.font_config).grid(row=0, column=0, padx=self.pad_config)
        input_shape_entry = ttk.Entry(input_frame, font=self.font_config, width=20)
        input_shape_entry.grid(row=0, column=1, padx=130)

        def show_input_shape_examples():
            examples = (
                'Examples:\n'
                '- Tabular data: Number of features (e.g., 10).\n'
                '- Grayscale images: Height x Width (e.g., 28,28,1).\n'
                '- Color images: Height x Width x Channels (e.g., 28,28,3).\n'
                '- Time series: Number of time steps (e.g., 50).'
            )
            messagebox.showinfo('Input Shape Examples', examples)

        ttk.Button(input_frame, text='ℹ️', command=show_input_shape_examples).grid(row=0, column=2, padx=self.pad_config)

        layers_frame = ttk.Frame(container)
        layers_frame.pack(pady=self.pad_config * 2, fill='x', expand=True, anchor='center')

        def add_layer():
            layer_frame = ttk.Frame(layers_frame, name=f'layer_frame_{len(self.layers_config)}')
            layer_frame.pack(pady=self.pad_config, fill='x')
            layer_type_var = tk.StringVar(value='Dense')
            layer_type_menu = ttk.Combobox(
                layer_frame,
                textvariable=layer_type_var,
                values=[
                    'Dense', 'Conv1D', 'Conv2D', 'MaxPooling1D',
                    'MaxPooling2D', 'AveragePooling1D', 'AveragePooling2D',
                    'Dropout', 'BatchNormalization', 'LSTM',
                    'Bidirectional(LSTM)', 'Flatten'
                ],
                state='readonly',
                width=20,
                font=self.font_config
            )
            layer_type_menu.grid(row=0, column=0, padx=self.pad_config)

            params_frame = ttk.Frame(layer_frame)
            params_frame.grid(row=0, column=1, padx=self.pad_config, sticky='ew')

            saved = False
            layer_index = None

            def clear_params():
                for widget in params_frame.winfo_children():
                    if getattr(widget, 'ignore_clear', False):
                        continue
                    widget.destroy()

            def show_params(event=None):
                clear_params()
                lt = layer_type_var.get()

                if lt == 'Dense':
                    ttk.Label(params_frame, text='Neurons:', font=self.font_config).grid(row=0, column=0)
                    neurons_entry = ttk.Entry(params_frame, width=8, font=self.font_config)
                    neurons_entry.insert(0, '32')
                    neurons_entry.grid(row=0, column=1)
                    tk.Button(params_frame, text='i', fg='orange',
                              command=lambda: self.show_info('Number of Neurons (Positive Integer): Sets how many neurons are in the layer. More neurons increase model complexity.')
                              ).grid(row=0, column=2, padx=2)

                    ttk.Label(params_frame, text='Activation:', font=self.font_config).grid(row=0, column=3)
                    activation_var = tk.StringVar(value='relu')
                    activation_menu = ttk.Combobox(params_frame, textvariable=activation_var,
                                                   values=['relu', 'sigmoid', 'tanh', 'softmax', 'linear', 'swish', 'elu'],
                                                   state='readonly', width=8, font=self.font_config)
                    activation_menu.grid(row=0, column=4)
                    tk.Button(params_frame, text='i', fg='orange',
                              command=lambda: self.show_info('Activation Function: Defines how neurons activate. Common choices: relu (default), sigmoid, tanh, softmax. For output layers, use linear for regression, sigmoid for binary classification, and softmax for multiclass classification.')
                              ).grid(row=0, column=5, padx=2)

                    ttk.Label(params_frame, text='Regularization:', font=self.font_config).grid(row=1, column=0)
                    reg_type_var = tk.StringVar(value='l2')
                    reg_type_menu = ttk.Combobox(params_frame, textvariable=reg_type_var,
                                                 values=['l1', 'l2', 'l1_l2'], state='readonly', width=5, font=self.font_config)
                    reg_type_menu.grid(row=1, column=1)
                    tk.Button(params_frame, text='i', fg='orange',
                              command=lambda: self.show_info('Regularization Type: Controls weight penalties to reduce overfitting.')
                              ).grid(row=1, column=2, padx=2)

                    ttk.Label(params_frame, text='Reg Value:', font=self.font_config).grid(row=1, column=3)
                    reg_value_entry = ttk.Entry(params_frame, width=5, font=self.font_config)
                    reg_value_entry.insert(0, '0.0')
                    reg_value_entry.grid(row=1, column=4)
                    tk.Button(params_frame, text='i', fg='orange',
                              command=lambda: self.show_info('Regularization Value (Positive Float): Determines the strength of the penalty. Higher values increase regularization. If set to 0, it has no effect.')
                              ).grid(row=1, column=5, padx=2)

                elif lt == 'Conv1D':
                    ttk.Label(params_frame, text='Filters:', font=self.font_config).grid(row=0, column=0)
                    filters_entry = ttk.Entry(params_frame, width=8, font=self.font_config)
                    filters_entry.insert(0, '32')
                    filters_entry.grid(row=0, column=1)
                    tk.Button(params_frame, text='i', fg='orange',
                              command=lambda: self.show_info('Number of Filters (Positive Integer): Sets the number of filters. More filters capture more features.')
                              ).grid(row=0, column=2, padx=2)

                    ttk.Label(params_frame, text='Kernel Size:', font=self.font_config).grid(row=0, column=3)
                    kernel_size_entry = ttk.Entry(params_frame, width=8, font=self.font_config)
                    kernel_size_entry.insert(0, '3')
                    kernel_size_entry.grid(row=0, column=4)
                    tk.Button(params_frame, text='i', fg='orange',
                              command=lambda: self.show_info('Kernel Size (Positive Integer): Sets the size of the convolution window. Common choices: 3, 5, 7.')
                              ).grid(row=0, column=5, padx=2)

                    ttk.Label(params_frame, text='Strides:', font=self.font_config).grid(row=0, column=6)
                    strides_entry = ttk.Entry(params_frame, width=8, font=self.font_config)
                    strides_entry.insert(0, '1')
                    strides_entry.grid(row=0, column=7)
                    tk.Button(params_frame, text='i', fg='orange',
                              command=lambda: self.show_info('Stride Length (Positive Integer): Defines the step size for moving the filter across the input. Common values: 1, 2. Larger strides reduce the output size.')
                              ).grid(row=0, column=8, padx=2)

                    ttk.Label(params_frame, text='Padding:', font=self.font_config).grid(row=0, column=9)
                    padding_var = tk.StringVar(value='valid')
                    padding_menu = ttk.Combobox(params_frame, textvariable=padding_var,
                                                values=['valid', 'same'], state='readonly', width=8, font=self.font_config)
                    padding_menu.grid(row=0, column=10)
                    tk.Button(params_frame, text='i', fg='orange',
                              command=lambda: self.show_info('Padding Type: Defines how the input is padded before applying the filter. valid: No padding, output size is reduced. same: Padding added to keep the output size the same as the input.')
                              ).grid(row=0, column=11, padx=2)

                    ttk.Label(params_frame, text='Regularization:', font=self.font_config).grid(row=1, column=0)
                    reg_type_var = tk.StringVar(value='l2')
                    reg_type_menu = ttk.Combobox(params_frame, textvariable=reg_type_var,
                                                 values=['l1', 'l2', 'l1_l2'], state='readonly', width=5, font=self.font_config)
                    reg_type_menu.grid(row=1, column=1)
                    tk.Button(params_frame, text='i', fg='orange',
                              command=lambda: self.show_info('Regularization Type: Controls weight penalties to reduce overfitting.')
                              ).grid(row=1, column=2, padx=2)

                    ttk.Label(params_frame, text='Reg Value:', font=self.font_config).grid(row=1, column=3)
                    reg_value_entry = ttk.Entry(params_frame, width=5, font=self.font_config)
                    reg_value_entry.insert(0, '0.0')
                    reg_value_entry.grid(row=1, column=4)
                    tk.Button(params_frame, text='i', fg='orange',
                              command=lambda: self.show_info('Regularization Value (Positive Float): Determines the strength of the penalty. Higher values increase regularization. If set to 0, it has no effect.')
                              ).grid(row=1, column=5, padx=2)

                elif lt == 'Conv2D':
                    ttk.Label(params_frame, text='Filters:', font=self.font_config).grid(row=0, column=0)
                    filters_entry = ttk.Entry(params_frame, width=8, font=self.font_config)
                    filters_entry.insert(0, '32')
                    filters_entry.grid(row=0, column=1)
                    tk.Button(params_frame, text='i', fg='orange',
                              command=lambda: self.show_info('Number of Filters (Positive Integer): Sets the number of filters. More filters capture more features.')
                              ).grid(row=0, column=2, padx=2)

                    ttk.Label(params_frame, text='Kernel Size:', font=self.font_config).grid(row=0, column=3)
                    kernel_size_entry = ttk.Entry(params_frame, width=8, font=self.font_config)
                    kernel_size_entry.insert(0, '3,3')
                    kernel_size_entry.grid(row=0, column=4)
                    tk.Button(params_frame, text='i', fg='orange',
                              command=lambda: self.show_info('Kernel Size: Defines the dimensions of the convolutional filter. Common choices: 3, 3; 5, 5; 7, 7. You pass the values as a tuple, e.g., 3, 3. Larger sizes capture broader features.')
                              ).grid(row=0, column=5, padx=2)

                    ttk.Label(params_frame, text='Strides:', font=self.font_config).grid(row=0, column=6)
                    strides_entry = ttk.Entry(params_frame, width=8, font=self.font_config)
                    strides_entry.insert(0, '1,1')
                    strides_entry.grid(row=0, column=7)
                    tk.Button(params_frame, text='i', fg='orange',
                              command=lambda: self.show_info('Stride Length: Defines the step size for moving the filter across the input. Common choices: 1, 1; 2, 2. You pass the values as a tuple, e.g., 1, 1. Larger strides reduce the output size.')
                              ).grid(row=0, column=8, padx=2)

                    ttk.Label(params_frame, text='Padding:', font=self.font_config).grid(row=0, column=9)
                    padding_var = tk.StringVar(value='valid')
                    padding_menu = ttk.Combobox(params_frame, textvariable=padding_var,
                                                values=['valid', 'same'], state='readonly', width=8, font=self.font_config)
                    padding_menu.grid(row=0, column=10)
                    tk.Button(params_frame, text='i', fg='orange',
                              command=lambda: self.show_info('Padding Type: Defines how the input is padded before applying the filter. valid: No padding, output size is reduced. same: Padding added to keep the output size the same as the input.')
                              ).grid(row=0, column=11, padx=2)

                    ttk.Label(params_frame, text='Regularization:', font=self.font_config).grid(row=1, column=0)
                    reg_type_var = tk.StringVar(value='l2')
                    reg_type_menu = ttk.Combobox(params_frame, textvariable=reg_type_var,
                                                 values=['l1', 'l2', 'l1_l2'], state='readonly', width=5, font=self.font_config)
                    reg_type_menu.grid(row=1, column=1)
                    tk.Button(params_frame, text='i', fg='orange',
                              command=lambda: self.show_info('Regularization Type: Controls weight penalties to reduce overfitting.')
                              ).grid(row=1, column=2, padx=2)

                    ttk.Label(params_frame, text='Reg Value:', font=self.font_config).grid(row=1, column=3)
                    reg_value_entry = ttk.Entry(params_frame, width=5, font=self.font_config)
                    reg_value_entry.insert(0, '0.0')
                    reg_value_entry.grid(row=1, column=4)
                    tk.Button(params_frame, text='i', fg='orange',
                              command=lambda: self.show_info('Regularization Value (Positive Float): Determines the strength of the penalty. Higher values increase regularization. If set to 0, it has no effect.')
                              ).grid(row=1, column=5, padx=2)

                elif lt in ['MaxPooling1D', 'AveragePooling1D']:
                    ttk.Label(params_frame, text='Pool Size:', font=self.font_config).grid(row=0, column=0)
                    pool_size_entry = ttk.Entry(params_frame, width=8, font=self.font_config)
                    pool_size_entry.insert(0, '2')
                    pool_size_entry.grid(row=0, column=1)
                    tk.Button(params_frame, text='i', fg='orange',
                              command=lambda: self.show_info('Pooling Window Size (Positive Integer): Defines the size of the window for pooling. Common choices: 2, 3, 5. You pass the value as an integer, e.g., 2. Larger sizes reduce the output size more.')
                              ).grid(row=0, column=2, padx=2)

                    ttk.Label(params_frame, text='Strides:', font=self.font_config).grid(row=0, column=3)
                    strides_entry = ttk.Entry(params_frame, width=8, font=self.font_config)
                    strides_entry.insert(0, '2')
                    strides_entry.grid(row=0, column=4)
                    tk.Button(params_frame, text='i', fg='orange',
                              command=lambda: self.show_info('Stride Length (Positive Integer): Defines the step size for moving the filter across the input. Common values: 1, 2. Larger strides reduce the output size.')
                              ).grid(row=0, column=5, padx=2)

                    ttk.Label(params_frame, text='Padding:', font=self.font_config).grid(row=0, column=6)
                    padding_var = tk.StringVar(value='valid')
                    padding_menu = ttk.Combobox(params_frame, textvariable=padding_var,
                                                values=['valid', 'same'], state='readonly', width=8, font=self.font_config)
                    padding_menu.grid(row=0, column=7)
                    tk.Button(params_frame, text='i', fg='orange',
                              command=lambda: self.show_info('Padding Type: Defines how the input is padded before applying the filter. valid: No padding, output size is reduced. same: Padding added to keep the output size the same as the input.')
                              ).grid(row=0, column=8, padx=2)

                elif lt in ['MaxPooling2D', 'AveragePooling2D']:
                    ttk.Label(params_frame, text='Pool Size:', font=self.font_config).grid(row=0, column=0)
                    pool_size_entry = ttk.Entry(params_frame, width=8, font=self.font_config)
                    pool_size_entry.insert(0, '2,2')
                    pool_size_entry.grid(row=0, column=1)
                    tk.Button(params_frame, text='i', fg='orange',
                              command=lambda: self.show_info('Pooling Window Size (e.g., 2, 2): Defines the size of the pooling window. Common choices: 2, 2; 3, 3. You pass the values as a tuple, e.g., 2, 2. Larger sizes reduce the output size more.')
                              ).grid(row=0, column=2, padx=2)

                    ttk.Label(params_frame, text='Strides:', font=self.font_config).grid(row=0, column=3)
                    strides_entry = ttk.Entry(params_frame, width=8, font=self.font_config)
                    strides_entry.insert(0, '2,2')
                    strides_entry.grid(row=0, column=4)
                    tk.Button(params_frame, text='i', fg='orange',
                              command=lambda: self.show_info('Stride Length: Defines the step size for moving the pooling window across the input. Common choices: 1, 1; 2, 2. You pass the values as a tuple, e.g., 2, 2. Larger strides reduce the output size more.')
                              ).grid(row=0, column=5, padx=2)

                    ttk.Label(params_frame, text='Padding:', font=self.font_config).grid(row=0, column=6)
                    padding_var = tk.StringVar(value='valid')
                    padding_menu = ttk.Combobox(params_frame, textvariable=padding_var,
                                                values=['valid', 'same'], state='readonly', width=8, font=self.font_config)
                    padding_menu.grid(row=0, column=7)
                    tk.Button(params_frame, text='i', fg='orange',
                              command=lambda: self.show_info('Padding Type: Defines how the input is padded before applying the filter. valid: No padding, output size is reduced. same: Padding added to keep the output size the same as the input.')
                              ).grid(row=0, column=8, padx=2)

                elif lt == 'Dropout':
                    ttk.Label(params_frame, text='Dropout Rate:', font=self.font_config).grid(row=0, column=0)
                    dropout_rate_entry = ttk.Entry(params_frame, width=8, font=self.font_config)
                    dropout_rate_entry.insert(0, '0.5')
                    dropout_rate_entry.grid(row=0, column=1)
                    tk.Button(params_frame, text='i', fg='orange',
                              command=lambda: self.show_info('Dropout Rate (float between 0 and 1): Defines the fraction of neurons to drop during training to prevent overfitting. Common values: 0.2, 0.5. Higher values lead to more regularization.')
                              ).grid(row=0, column=2, padx=2)

                elif lt == 'BatchNormalization':
                    tk.Label(params_frame, text='No configurable parameters.', font=self.font_config).grid(row=0, column=0)

                elif lt == 'LSTM':
                    ttk.Label(params_frame, text='Units:', font=self.font_config).grid(row=0, column=0)
                    units_entry = ttk.Entry(params_frame, width=8, font=self.font_config)
                    units_entry.insert(0, '64')
                    units_entry.grid(row=0, column=1)
                    tk.Button(params_frame, text='i', fg='orange',
                              command=lambda: self.show_info('Number of LSTM Units (Positive Integer): Defines the number of units in the LSTM layer. More units allow the model to capture more complex patterns.')
                              ).grid(row=0, column=2, padx=2)
                    ttk.Label(params_frame, text='Return Sequences:', font=self.font_config).grid(row=0, column=3)
                    return_sequences_var = tk.BooleanVar(value=False)
                    return_sequences_check = ttk.Checkbutton(params_frame, variable=return_sequences_var)
                    return_sequences_check.grid(row=0, column=4)
                    tk.Button(params_frame, text='i', fg='orange',
                              command=lambda: self.show_info('Return Sequences: If activated, the layer returns the full sequence of outputs for each time step. If deactivated, only the output from the last time step is returned.')
                              ).grid(row=0, column=5, padx=2)

                elif lt == 'Bidirectional(LSTM)':
                    ttk.Label(params_frame, text='Units:', font=self.font_config).grid(row=0, column=0)
                    units_entry = ttk.Entry(params_frame, width=8, font=self.font_config)
                    units_entry.insert(0, '64')
                    units_entry.grid(row=0, column=1)
                    tk.Button(params_frame, text='i', fg='orange',
                              command=lambda: self.show_info('Number of LSTM Units (Positive Integer): Defines the number of units in the LSTM layer. More units allow the model to capture more complex patterns.')
                              ).grid(row=0, column=2, padx=2)
                    ttk.Label(params_frame, text='Return Sequences:', font=self.font_config).grid(row=0, column=3)
                    return_sequences_var = tk.BooleanVar(value=False)
                    return_sequences_check = ttk.Checkbutton(params_frame, variable=return_sequences_var)
                    return_sequences_check.grid(row=0, column=4)
                    tk.Button(params_frame, text='i', fg='orange',
                              command=lambda: self.show_info('Return Sequences: If activated, the layer returns the full sequence of outputs for each time step. If deactivated, only the output from the last time step is returned.')
                              ).grid(row=0, column=5, padx=2)

                elif lt == 'Flatten':
                    tk.Label(params_frame, text='No configurable parameters.', font=self.font_config).grid(row=0, column=0)

                def guardar_capa():
                    nonlocal saved, layer_index
                    config = {}
                    if lt == 'Dense':
                        try:
                            config['neurons'] = int(neurons_entry.get())
                        except Exception:
                            messagebox.showerror('Error. Invalid value in Neurons')
                            return
                        config['activation'] = activation_var.get()
                        config['reg_type'] = reg_type_var.get()
                        try:
                            config['reg_value'] = float(reg_value_entry.get())
                        except Exception:
                            messagebox.showerror('Error. Invalid value in Reg Value')
                            return
                    elif lt == 'Conv1D':
                        try:
                            config['filters'] = int(filters_entry.get())
                        except Exception:
                            messagebox.showerror('Error. Invalid value in Filters')
                            return
                        try:
                            config['kernel_size'] = int(kernel_size_entry.get())
                        except Exception:
                            messagebox.showerror('Error. Invalid value in Kernel Size')
                            return
                        try:
                            config['strides'] = int(strides_entry.get())
                        except Exception:
                            messagebox.showerror('Error. Invalid value in Strides')
                            return
                        config['padding'] = padding_var.get()
                        config['reg_type'] = reg_type_var.get()
                        try:
                            config['reg_value'] = float(reg_value_entry.get())
                        except Exception:
                            messagebox.showerror('Error. Invalid value in Reg Value')
                            return
                    elif lt == 'Conv2D':
                        try:
                            config['filters'] = int(filters_entry.get())
                        except Exception:
                            messagebox.showerror('Error. Invalid value in Filters')
                            return
                        try:
                            config['kernel_size'] = tuple(map(int, kernel_size_entry.get().split(',')))
                        except Exception:
                            messagebox.showerror('Error. Invalid value in Kernel Size')
                            return
                        try:
                            config['strides'] = tuple(map(int, strides_entry.get().split(',')))
                        except Exception:
                            messagebox.showerror('Error. Invalid value in Strides')
                            return
                        config['padding'] = padding_var.get()
                        config['reg_type'] = reg_type_var.get()
                        try:
                            config['reg_value'] = float(reg_value_entry.get())
                        except Exception:
                            messagebox.showerror('Error. Invalid value in Reg Value')
                            return
                    elif lt in ['MaxPooling1D', 'AveragePooling1D']:
                        try:
                            config['pool_size'] = int(pool_size_entry.get())
                        except Exception:
                            messagebox.showerror('Error. Invalid value in Pool Size')
                            return
                        try:
                            config['strides'] = int(strides_entry.get())
                        except Exception:
                            messagebox.showerror('Error. Invalid value in Strides')
                            return
                        config['padding'] = padding_var.get()
                    elif lt in ['MaxPooling2D', 'AveragePooling2D']:
                        try:
                            config['pool_size'] = tuple(map(int, pool_size_entry.get().split(',')))
                        except Exception:
                            messagebox.showerror('Error. Invalid value in Pool Size')
                            return
                        try:
                            config['strides'] = tuple(map(int, strides_entry.get().split(',')))
                        except Exception:
                            messagebox.showerror('Error. Invalid value in Strides')
                            return
                        config['padding'] = padding_var.get()
                    elif lt == 'Dropout':
                        try:
                            config['dropout_rate'] = float(dropout_rate_entry.get())
                        except Exception:
                            messagebox.showerror('Error. Invalid value in Dropout Rate')
                            return
                    elif lt == 'LSTM':
                        try:
                            config['units'] = int(units_entry.get())
                        except Exception:
                            messagebox.showerror('Error. Invalid value in Units')
                            return
                        config['return_sequences'] = return_sequences_var.get()
                    elif lt == 'Bidirectional(LSTM)':
                        try:
                            config['units'] = int(units_entry.get())
                        except Exception:
                            messagebox.showerror('Error. Invalid value in Units')
                            return
                        config['return_sequences'] = return_sequences_var.get()

                    if not saved:
                        self.layers_config.append({
                            'layer_type': lt,
                            'params': config
                        })
                        layer_index = len(self.layers_config) - 1
                        saved = True
                        messagebox.showinfo('Layer saved', f'Layer {lt} saved successfully.')
                        guardar_button.config(text='Update layer')
                    else:
                        self.layers_config[layer_index]['layer_type'] = lt
                        self.layers_config[layer_index]['params'] = config
                        messagebox.showinfo('Layer updated', f'Layer {lt} updated successfully.')

                def eliminar_capa():
                    nonlocal saved, layer_index
                    if saved and layer_index is not None:
                        try:
                            del self.layers_config[layer_index]
                        except Exception:
                            pass
                    layer_frame.destroy()

                guardar_button = ttk.Button(params_frame, text='💾', command=guardar_capa)
                guardar_button.ignore_clear = True
                guardar_button.grid(row=101, column=0, pady=self.pad_config)
                eliminar_button = ttk.Button(params_frame, text='🗑️', command=eliminar_capa)
                eliminar_button.ignore_clear = True
                eliminar_button.grid(row=101, column=1, pady=self.pad_config)

            layer_type_menu.bind('<<ComboboxSelected>>', show_params)
            show_params()

        ttk.Button(container, text='Add Layer', command=add_layer, style='Large.TButton').pack(pady=self.pad_config * 2)

        def process_and_next():
            try:
                input_shape_str = input_shape_entry.get().strip()
                if not input_shape_str:
                    raise ValueError('Input shape is required!')
                if ',' in input_shape_str:
                    parts = [p.strip() for p in input_shape_str.split(',')]
                    if not all(p.strip().isdigit() for p in parts):
                        raise ValueError('Invalid format. Use only integers separated by commas.')
                    self.input_shape = tuple(map(int, parts))
                else:
                    if not input_shape_str.isdigit():
                        raise ValueError('Must be a positive integer.')
                    self.input_shape = (int(input_shape_str),)
                self.show_step(2)
            except ValueError as ve:
                messagebox.showerror(f'Validation Error: Invalid data:\n{ve}')
            except Exception as e:
                messagebox.showerror(f'Critical Error: Unexpected error:\n{str(e)}')

        nav_frame = ttk.Frame(main_frame)
        nav_frame.grid(row=1, column=0, sticky='se', pady=10)
        ttk.Button(
            nav_frame,
            name='step1_back_btn',
            text='Back',
            command=lambda: self.show_step(0)
        ).pack(side='left', padx=10)
        ttk.Button(
            nav_frame,
            name='step1_next_btn',
            text='Next',
            command=process_and_next
        ).pack(side='right', padx=10)

    def step_2(self):
        content_frame = ttk.Frame(self.root, name='step2_frame')
        content_frame.grid(row=1, column=0, sticky='nsew', padx=50, pady=50)
        tk.Label(content_frame, text='Configure Optimizer', font=self.font_config).pack(pady=self.pad_config * 2)

        self.optimizer_var.set('Select optimizer')
        self.learning_rate_var.set(0.001)

        tk.Label(content_frame, text='Optimizer:', font=self.font_config).pack(pady=self.pad_config)
        ttk.Combobox(content_frame, textvariable=self.optimizer_var,
                     values=['Adam', 'Nadam', 'SGD'], state='readonly', font=self.font_config).pack(pady=self.pad_config)

        tk.Label(content_frame, text='Learning Rate:', font=self.font_config).pack(pady=self.pad_config)
        tk.Scale(content_frame, from_=0.0001, to=1, resolution=0.0001,
                 orient='horizontal', variable=self.learning_rate_var,
                 length=500, font=self.font_config).pack(pady=self.pad_config)

        nav_frame = ttk.Frame(content_frame)
        nav_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=20)

        btn_container = ttk.Frame(nav_frame)
        btn_container.pack(side=tk.RIGHT)

        ttk.Button(btn_container, text='Back',
                   command=lambda: self.show_step(1)).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_container, text='Next',
                   command=lambda: self.show_step(3)).pack(side=tk.LEFT, padx=5)

    def step_3(self):
        content_frame = ttk.Frame(self.root, name='step3_frame')
        content_frame.grid(row=1, column=0, sticky='nsew', padx=50, pady=50)
        tk.Label(content_frame, text='Loss Function and Metrics', font=self.font_config).pack(pady=self.pad_config * 2)

        if self.problem_type.get() == 'classification':
            loss_options = ['binary_crossentropy', 'categorical_crossentropy']
            metrics_options = ['accuracy', 'precision']
        else:
            loss_options = ['mse', 'mae']
            metrics_options = ['mse', 'mae']

        if self.loss_function.get() not in loss_options:
            self.loss_function.set(loss_options[0])

        ttk.Label(content_frame, text='Loss Function:', font=self.font_config).pack(pady=self.pad_config)
        loss_combobox = ttk.Combobox(content_frame, textvariable=self.loss_function,
                                     values=loss_options, state='readonly', font=self.font_config)
        loss_combobox.pack(pady=self.pad_config)

        self.metrics_vars.clear()
        if self.problem_type.get() == 'classification':
            metrics_options = ['accuracy', 'precision']
        else:
            metrics_options = ['mse', 'mae']

        ttk.Label(content_frame, text='Metrics:', font=self.font_config).pack(pady=self.pad_config)

        metrics_frame = ttk.Frame(content_frame, name='step3_metrics_frame')
        metrics_frame.pack(pady=self.pad_config, anchor='center')
        for metric in metrics_options:
            var = tk.BooleanVar()
            check_frame = ttk.Frame(metrics_frame)
            check_frame.pack(pady=2, anchor='center')
            checkbutton = ttk.Checkbutton(check_frame, text=metric, variable=var)
            checkbutton.pack(side='left')
            self.metrics_vars.append((metric, var))

        nav_frame = ttk.Frame(content_frame)
        nav_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=20)

        btn_container = ttk.Frame(nav_frame)
        btn_container.pack(side=tk.RIGHT)

        ttk.Button(btn_container, text='Back',
                   command=lambda: self.show_step(2)).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_container, text='Next',
                   command=lambda: self.show_step(4)).pack(side=tk.LEFT, padx=5)

    def step_4(self):
        content_frame = ttk.Frame(self.root, name='step4_frame')
        content_frame.grid(row=1, column=0, sticky='nsew', padx=50, pady=50)

        tk.Label(content_frame, text='Save Model', font=self.font_config).pack(pady=self.pad_config * 2)
        ttk.Checkbutton(content_frame, text='Save Model', variable=self.save_var).pack(pady=self.pad_config)
        ttk.Button(content_frame, text='Select Directory',
                   command=lambda: self.save_directory.set(filedialog.askdirectory())).pack(pady=self.pad_config)
        ttk.Label(content_frame, textvariable=self.save_directory, font=self.font_config).pack()

        status_label = ttk.Label(content_frame, textvariable=self.status_var,
                                 font=self.font_config, foreground='red')
        status_label.pack(pady=self.pad_config)

        nav_frame = ttk.Frame(content_frame)
        nav_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=20)

        btn_container = ttk.Frame(nav_frame)
        btn_container.pack(side=tk.RIGHT)

        ttk.Button(btn_container, text='Back',
                   command=lambda: self.show_step(3)).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_container, text='Create',
                   command=self.create_model).pack(side=tk.LEFT, padx=5)

    def create_model(self):
        try:
            if not self.layers_config:
                raise ValueError('No layers defined in the model!')
            if self.input_shape is None:
                raise ValueError('Input shape not defined')

            model = Sequential()
            for i, layer_config in enumerate(self.layers_config):
                layer_type = layer_config['layer_type']
                params = layer_config['params']
                kwargs = {}
                if i == 0:
                    kwargs['input_shape'] = self.input_shape

                if layer_type == 'Dense':
                    reg = None
                    if params['reg_value'] > 0:
                        reg = globals()[params['reg_type']](params['reg_value'])
                    model.add(Dense(
                        units=params['neurons'],
                        activation=params['activation'],
                        kernel_regularizer=reg,
                        **kwargs
                    ))
                elif layer_type == 'Conv1D':
                    reg = None
                    if params['reg_value'] > 0:
                        reg = globals()[params['reg_type']](params['reg_value'])
                    model.add(Conv1D(
                        filters=params['filters'],
                        kernel_size=params['kernel_size'],
                        strides=params['strides'],
                        padding=params['padding'],
                        kernel_regularizer=reg,
                        **kwargs
                    ))
                elif layer_type == 'Conv2D':
                    reg = None
                    if params['reg_value'] > 0:
                        reg = globals()[params['reg_type']](params['reg_value'])
                    model.add(Conv2D(
                        filters=params['filters'],
                        kernel_size=params['kernel_size'],
                        strides=params['strides'],
                        padding=params['padding'],
                        kernel_regularizer=reg,
                        **kwargs
                    ))
                elif layer_type == 'MaxPooling1D':
                    model.add(MaxPooling1D(
                        pool_size=params['pool_size'],
                        strides=params['strides'],
                        padding=params['padding']
                    ))
                elif layer_type == 'MaxPooling2D':
                    model.add(MaxPooling2D(
                        pool_size=params['pool_size'],
                        strides=params['strides'],
                        padding=params['padding']
                    ))
                elif layer_type == 'AveragePooling1D':
                    model.add(AveragePooling1D(
                        pool_size=params['pool_size'],
                        strides=params['strides'],
                        padding=params['padding']
                    ))
                elif layer_type == 'AveragePooling2D':
                    model.add(AveragePooling2D(
                        pool_size=params['pool_size'],
                        strides=params['strides'],
                        padding=params['padding']
                    ))
                elif layer_type == 'Dropout':
                    model.add(Dropout(
                        rate=params['dropout_rate']
                    ))
                elif layer_type == 'LSTM':
                    model.add(LSTM(
                        units=params['units'],
                        return_sequences=params['return_sequences'],
                        **kwargs
                    ))
                elif layer_type == 'Bidirectional(LSTM)':
                    lstm_layer = LSTM(
                        units=params['units'],
                        return_sequences=params['return_sequences']
                    )
                    model.add(Bidirectional(
                        lstm_layer,
                        **kwargs
                    ))
                elif layer_type == 'Flatten':
                    model.add(Flatten())
                elif layer_type == 'BatchNormalization':
                    model.add(BatchNormalization())
                else:
                    raise ValueError(f'Unsupported layer type: {layer_type}')

            optimizer_type = self.optimizer_var.get()
            if optimizer_type == 'Adam':
                optimizer = Adam(learning_rate=self.learning_rate_var.get())
            elif optimizer_type == 'Nadam':
                optimizer = Nadam(learning_rate=self.learning_rate_var.get())
            elif optimizer_type == 'SGD':
                optimizer = SGD(learning_rate=self.learning_rate_var.get())
            else:
                raise ValueError('Select a valid optimizer')

            model.compile(optimizer=optimizer,
                          loss=self.loss_function.get(),
                          metrics=[metric for metric, var in self.metrics_vars if var.get()])

            if self.save_var.get():
                directory = self.save_directory.get()
                if not directory:
                    raise ValueError('Select a directory to save')
                os.makedirs(directory, exist_ok=True)
                model.save(os.path.join(directory, 'model.h5'))
                plot_model(model, to_file=os.path.join(directory, 'model.png'), show_shapes=True)
                with open(os.path.join(directory, 'summary.txt'), 'w') as f:
                    model.summary(print_fn=lambda x: f.write(x + '\n'))
                messagebox.showinfo('Success', 'Model saved successfully!')
            else:
                messagebox.showinfo('Success', 'Model created successfully!')

        except Exception as e:
            messagebox.showerror('Error', str(e))


if __name__ == '__main__':
    ModelConfigurator()









    


